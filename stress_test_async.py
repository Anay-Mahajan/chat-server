"""
Async stress test for the TCP chat server.

Fixes over the previous version:
  1. Latency is tracked per-receiver (not popped on first arrival)
  2. Drain phase waits dynamically until message flow stops (not hardcoded 3s)
  3. Delivery completeness is verified (expected vs actual received)
  4. Throughput is measured only during the messaging phase (excludes connect/drain)
  5. All clients finish @advertize before any messages are sent (warmup phase)
  6. Timeouts prevent the test from hanging forever
  7. Better statistics: min, median, p50, p95, p99, max
"""

import asyncio
import time
import argparse
import random
import statistics

DEFAULT_IP="127.0.0.1"
DEFAULT_PORT = 9090
DEFAULT_CLIENTS = 1000
DEFAULT_MSGS = 10
DRAIN_IDLE_TIMEOUT = 5       # stop draining if no messages received for this many seconds
DRAIN_MAX_TIMEOUT = 60       # absolute max drain time
CONNECT_TIMEOUT = 10         # per-client connection timeout


# ── Global latency tracker ──────────────────────────────────────────────────
# Key: message content string ("msg_5_3")
# Value: send timestamp (float)
# We do NOT pop entries — every receiver reads it.
sent_timestamps: dict[str, float] = {}


class ChatClient:
    def __init__(self, client_id: int, host: str, port: int, total_clients: int):
        self.client_id = client_id
        self.username = f"user{client_id}"
        self.host = host
        self.port = port
        self.total_clients = total_clients

        self.reader: asyncio.StreamReader | None = None
        self.writer: asyncio.StreamWriter | None = None

        self.connected = False
        self.latencies: list[float] = []
        self.send_errors = 0
        self.recv_errors = 0
        self.received_count = 0
        self.sent_count = 0

    # ── Phase 1: Connect & register ────────────────────────────────────
    async def connect_and_register(self) -> bool:
        try:
            self.reader, self.writer = await asyncio.wait_for(
                asyncio.open_connection(self.host, self.port),
                timeout=CONNECT_TIMEOUT,
            )
            msg = f"@advertize {self.username}\n"
            self.writer.write(msg.encode())
            await self.writer.drain()
            self.connected = True
            return True
        except Exception as e:
            self.send_errors += 1
            print(f"  [!] Client {self.client_id} connect failed: {e}")
            return False

    # ── Phase 2: Send messages ─────────────────────────────────────────
    async def send_messages(self, num_messages: int):
        if not self.writer or not self.connected:
            return

        for i in range(num_messages):
            content = f"msg_{self.client_id}_{i}"
            msg = f"@all {content}\n"

            sent_timestamps[content] = time.monotonic()

            try:
                self.writer.write(msg.encode())
                await self.writer.drain()
                self.sent_count += 1
            except Exception as e:
                self.send_errors += 1
                print(f"  [!] Client {self.client_id} send error: {e}")
                break

            # Small random delay to avoid perfect synchronization
            await asyncio.sleep(random.uniform(0.005, 0.02))

    # ── Receiver (runs continuously in background) ─────────────────────
    async def receive_loop(self):
        """Read messages until cancelled. Tracks latency and counts."""
        if not self.reader:
            return

        try:
            while True:
                data = await self.reader.readline()
                if not data:
                    break

                line = data.decode().strip()
                if "->" not in line:
                    continue

                parts = line.split("->", 1)
                if len(parts) != 2:
                    continue

                content = parts[1]
                self.received_count += 1

                # Look up (don't pop) the send timestamp
                send_time = sent_timestamps.get(content)
                if send_time is not None:
                    latency_ms = (time.monotonic() - send_time) * 1000
                    self.latencies.append(latency_ms)

        except asyncio.CancelledError:
            pass
        except Exception as e:
            self.recv_errors += 1

    # ── Cleanup ────────────────────────────────────────────────────────
    async def close(self):
        if self.writer:
            try:
                self.writer.close()
                await self.writer.wait_closed()
            except Exception:
                pass


async def main():
    parser = argparse.ArgumentParser(description="Chat Server Stress Test")
    parser.add_argument("--ip", default=DEFAULT_IP, help="Server IP address")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Server port")
    parser.add_argument("--clients", type=int, default=DEFAULT_CLIENTS, help="Number of concurrent clients")
    parser.add_argument("--msgs", type=int, default=DEFAULT_MSGS, help="Messages per client")
    parser.add_argument("--drain-timeout", type=int, default=DRAIN_IDLE_TIMEOUT,
                        help="Seconds of idle before ending drain phase")
    args = parser.parse_args()

    n_clients = args.clients
    n_msgs = args.msgs
    expected_per_client = (n_clients - 1) * n_msgs  # each client gets msgs from all others
    expected_total = n_clients * expected_per_client

    print("=" * 60)
    print("  Chat Server Stress Test")
    print("=" * 60)
    print(f"  Target:             {args.ip}:{args.port}")
    print(f"  Clients:            {n_clients}")
    print(f"  Messages/client:    {n_msgs}")
    print(f"  Expected fan-out:   {expected_total:,} messages")
    print(f"  Drain idle timeout: {args.drain_timeout}s")
    print("=" * 60)

    # ── Phase 1: Connect all clients ────────────────────────────────────
    print("\n[Phase 1] Connecting and registering clients...")
    phase1_start = time.monotonic()

    clients: list[ChatClient] = []
    for i in range(n_clients):
        c = ChatClient(i, args.ip, args.port, n_clients)
        clients.append(c)

    # Connect in batches to avoid overwhelming the server's accept queue
    BATCH_SIZE = 50
    for batch_start in range(0, n_clients, BATCH_SIZE):
        batch = clients[batch_start : batch_start + BATCH_SIZE]
        results = await asyncio.gather(
            *[c.connect_and_register() for c in batch],
            return_exceptions=True,
        )
        connected_in_batch = sum(1 for r in results if r is True)
        print(f"  Connected {batch_start + connected_in_batch}/{n_clients}", end="\r", flush=True)
        await asyncio.sleep(0.05)  # small pause between batches

    connected_clients = [c for c in clients if c.connected]
    n_connected = len(connected_clients)
    phase1_time = time.monotonic() - phase1_start
    print(f"  Connected {n_connected}/{n_clients} clients in {phase1_time:.2f}s")

    if n_connected == 0:
        print("\n[ABORT] No clients connected. Is the server running?")
        return

    # ── Start all receiver loops ────────────────────────────────────────
    recv_tasks = {c.client_id: asyncio.create_task(c.receive_loop()) for c in connected_clients}

    # Brief warmup so all @advertize messages are processed server-side
    print("  Warmup pause (1s)...")
    await asyncio.sleep(1.0)

    # ── Phase 2: Message flood ──────────────────────────────────────────
    print(f"\n[Phase 2] Sending {n_connected * n_msgs:,} messages...")
    phase2_start = time.monotonic()

    send_tasks = [c.send_messages(n_msgs) for c in connected_clients]
    await asyncio.gather(*send_tasks)

    phase2_time = time.monotonic() - phase2_start
    total_sent = sum(c.sent_count for c in connected_clients)
    print(f"  Sent {total_sent:,} messages in {phase2_time:.2f}s")
    print(f"  Send throughput: {total_sent / phase2_time:,.0f} msgs/sec")

    # ── Phase 3: Drain — wait for all fan-out messages to arrive ────────
    print(f"\n[Phase 3] Draining (waiting for fan-out delivery)...")
    drain_start = time.monotonic()
    last_count = 0
    idle_since = time.monotonic()

    while True:
        await asyncio.sleep(0.5)
        current_count = sum(c.received_count for c in connected_clients)
        elapsed = time.monotonic() - drain_start

        if current_count > last_count:
            idle_since = time.monotonic()
            rate = (current_count - last_count) / 0.5
            print(f"  Received: {current_count:>12,} / {expected_total:,}  "
                  f"(+{current_count - last_count:,} @ {rate:,.0f}/s)   ", end="\r", flush=True)
            last_count = current_count
        else:
            idle_time = time.monotonic() - idle_since
            if idle_time >= args.drain_timeout:
                print(f"\n  Drain complete (idle for {args.drain_timeout}s)")
                break

        if elapsed >= DRAIN_MAX_TIMEOUT:
            print(f"\n  Drain timeout ({DRAIN_MAX_TIMEOUT}s max)")
            break

    drain_time = time.monotonic() - drain_start

    # ── Stop receivers and close connections ─────────────────────────────
    print("\n[Cleanup] Closing connections...")
    for task in recv_tasks.values():
        task.cancel()
    await asyncio.gather(*recv_tasks.values(), return_exceptions=True)
    await asyncio.gather(*[c.close() for c in connected_clients])

    # ── Results ─────────────────────────────────────────────────────────
    total_received = sum(c.received_count for c in connected_clients)
    total_send_errors = sum(c.send_errors for c in connected_clients)
    total_recv_errors = sum(c.recv_errors for c in connected_clients)
    all_latencies = sorted(l for c in connected_clients for l in c.latencies)

    # Recalculate expected based on actual connected clients
    actual_expected = n_connected * (n_connected - 1) * n_msgs
    delivery_pct = (total_received / actual_expected * 100) if actual_expected > 0 else 0

    # Total time only for the messaging + drain phase (not connect)
    messaging_duration = phase2_time + drain_time
    recv_throughput = total_received / messaging_duration if messaging_duration > 0 else 0

    print()
    print("=" * 60)
    print("  RESULTS")
    print("=" * 60)

    print(f"\n  ── Connections ──")
    print(f"  Connected:          {n_connected} / {n_clients}")
    print(f"  Connect time:       {phase1_time:.2f}s")

    print(f"\n  ── Messages ──")
    print(f"  Sent (broadcast):   {total_sent:,}")
    print(f"  Expected fan-out:   {actual_expected:,}")
    print(f"  Actually received:  {total_received:,}")
    print(f"  Delivery rate:      {delivery_pct:.1f}%")
    print(f"  Send errors:        {total_send_errors}")
    print(f"  Recv errors:        {total_recv_errors}")

    print(f"\n  ── Timing ──")
    print(f"  Send phase:         {phase2_time:.2f}s")
    print(f"  Drain phase:        {drain_time:.2f}s")
    print(f"  Total (send+drain): {messaging_duration:.2f}s")

    print(f"\n  ── Throughput ──")
    print(f"  Send:               {total_sent / phase2_time:,.0f} msgs/sec")
    print(f"  Receive (fan-out):  {recv_throughput:,.0f} msgs/sec")

    print(f"\n  ── Latency (first-arrival) ──")
    if all_latencies:
        print(f"  Samples:            {len(all_latencies):,}")
        print(f"  Min:                {all_latencies[0]:.1f} ms")
        print(f"  Median (P50):       {statistics.median(all_latencies):.1f} ms")
        p95_idx = int(len(all_latencies) * 0.95)
        p99_idx = int(len(all_latencies) * 0.99)
        print(f"  Avg:                {statistics.mean(all_latencies):.1f} ms")
        print(f"  P95:                {all_latencies[p95_idx]:.1f} ms")
        print(f"  P99:                {all_latencies[p99_idx]:.1f} ms")
        print(f"  Max:                {all_latencies[-1]:.1f} ms")
    else:
        print(f"  No latency samples collected")

    # ── Per-client delivery breakdown (summary) ─────────────────────────
    recv_counts = [c.received_count for c in connected_clients]
    if recv_counts:
        print(f"\n  ── Per-Client Delivery ──")
        print(f"  Expected/client:    {(n_connected - 1) * n_msgs:,}")
        print(f"  Min received:       {min(recv_counts):,}")
        print(f"  Median received:    {statistics.median(recv_counts):,.0f}")
        print(f"  Max received:       {max(recv_counts):,}")
        underfilled = sum(1 for c in recv_counts if c < (n_connected - 1) * n_msgs)
        print(f"  Clients w/ drops:   {underfilled} / {n_connected}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nTest cancelled by user.")
