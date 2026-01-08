import asyncio
import time
import argparse
import random
import statistics

# --- Configuration defaults ---
DEFAULT_IP = "127.0.0.1"
DEFAULT_PORT = 8080
DEFAULT_CLIENTS = 1000
DEFAULT_MSGS = 10

# --- GLOBAL SHARED TRACKER ---
# Format: { "msg_content": timestamp }
# This allows Client B to measure latency for a message sent by Client A.
global_sent_times = {}

class ChatClient:
    def __init__(self, client_id, host, port, total_clients):
        self.client_id = client_id
        self.username = f"user{client_id}"
        self.host = host
        self.port = port
        self.reader = None
        self.writer = None
        # self.sent_times is removed; we use global_sent_times now
        self.latencies = []
        self.errors = 0
        self.received_count = 0
        self.total_clients = total_clients

    async def connect(self):
        try:
            self.reader, self.writer = await asyncio.open_connection(self.host, self.port)
            # Send advertize command (Protocol: @advertize <username>)
            msg = f"@advertize {self.username}\n"
            self.writer.write(msg.encode())
            await self.writer.drain()
            return True
        except Exception as e:
            self.errors += 1
            return False

    async def send_messages(self, num_messages):
        if not self.writer:
            return

        for i in range(num_messages):
            # Unique message content
            content = f"msg_{self.client_id}_{i}"
            msg = f"@all {content}\n"
            
            # TRACK TIME GLOBALLY BEFORE SENDING
            global_sent_times[content] = time.time()
            
            try:
                self.writer.write(msg.encode())
                await self.writer.drain()
            except Exception:
                self.errors += 1
                break
            
            # Random jitter to prevent unrealistic synchronized bursts
            await asyncio.sleep(random.uniform(0.01, 0.05))

    async def receive_messages(self):
        if not self.reader:
            return

        while True:
            try:
                # Read line-by-line
                data = await self.reader.readline()
                if not data:
                    break
                
                line = data.decode().strip()
                # Expected format: "username->message_content"
                if "->" in line:
                    parts = line.split("->", 1)
                    if len(parts) == 2:
                        content = parts[1]
                        
                        # CHECK GLOBAL REGISTRY
                        # If this message is in the tracker, we calculate latency.
                        # We use .pop() so only the FIRST client to receive it records the latency
                        # (This measures the "fastest path" latency).
                        if content in global_sent_times:
                            start_time = global_sent_times.pop(content)
                            latency = (time.time() - start_time) * 1000 # Convert to ms
                            self.latencies.append(latency)
                        
                self.received_count += 1
            except Exception:
                break

    async def run(self, num_messages, start_event):
        if not await self.connect():
            return

        # Start receiver task
        recv_task = asyncio.create_task(self.receive_messages())

        # Wait for global start signal
        await start_event.wait()

        # Send messages
        await self.send_messages(num_messages)

        # Allow time for trailing messages to arrive
        await asyncio.sleep(3)
        
        # Cleanup
        recv_task.cancel()
        try:
            self.writer.close()
            await self.writer.wait_closed()
        except:
            pass

async def main():
    parser = argparse.ArgumentParser(description="Async Chat Server Stress Test")
    parser.add_argument("--ip", default=DEFAULT_IP, help="Server IP")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Server Port")
    parser.add_argument("--clients", type=int, default=DEFAULT_CLIENTS, help="Number of clients")
    parser.add_argument("--msgs", type=int, default=DEFAULT_MSGS, help="Messages per client")
    args = parser.parse_args()

    print(f"--- Starting Stress Test ---")
    print(f"Target: {args.ip}:{args.port}")
    print(f"Clients: {args.clients}")
    print(f"Messages per Client: {args.msgs}")

    clients = []
    start_event = asyncio.Event()

    # 1. Ramp-up Connections
    print("Connecting clients...", end="", flush=True)
    tasks = []
    for i in range(args.clients):
        client = ChatClient(i, args.ip, args.port, args.clients)
        clients.append(client)
        tasks.append(asyncio.create_task(client.run(args.msgs, start_event)))
        
        # Small delay to mimic real users joining
        if i % 50 == 0:
            print(".", end="", flush=True)
            await asyncio.sleep(0.05) 
    print(" Done.")

    # 2. Start Test
    print("Starting message flood...")
    start_time = time.time()
    start_event.set()

    # 3. Wait for completion
    await asyncio.gather(*tasks)
    duration = time.time() - start_time

    # 4. Aggregate Results
    total_sent = args.clients * args.msgs
    total_errors = sum(c.errors for c in clients)
    
    # Collect all captured latencies from all clients
    all_latencies = [l for c in clients for l in c.latencies]
    
    # Calculate fan-out throughput (Total messages received by everyone)
    total_received = sum(c.received_count for c in clients)
    
    print("\n\n--- Results ---")
    print(f"Time Taken:       {duration:.2f} seconds")
    print(f"Total Sent:       {total_sent}")
    print(f"Total Received:   {total_received} (Fan-out)")
    print(f"Failed/Errors:    {total_errors}")
    print(f"Throughput:       {total_received / duration:.2f} msgs/sec")
    
    if all_latencies:
        avg_lat = statistics.mean(all_latencies)
        try:
            # Python 3.8+
            p99_lat = statistics.quantiles(all_latencies, n=100)[98]
        except AttributeError:
            # Fallback for older Python versions
            all_latencies.sort()
            p99_lat = all_latencies[int(len(all_latencies) * 0.99)]

        print(f"Avg Latency:      {avg_lat:.2f} ms")
        print(f"P99 Latency:      {p99_lat:.2f} ms")
    else:
        print("Latency:          N/A (Could not track any messages)")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nTest cancelled.")