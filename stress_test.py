import socket
import threading
import time
import random

SERVER_IP = "3.109.206.199"
SERVER_PORT = 8080

NUM_CLIENTS = 1000
MESSAGES_PER_CLIENT = 10

start_event = threading.Event()

successful_sends = 0
failed_sends = 0
lock = threading.Lock()


def client_task(client_id):
    global successful_sends, failed_sends

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((SERVER_IP, SERVER_PORT))
        s.settimeout(5)

        username = f"user{client_id}"
        s.sendall(f"@advertize {username}\n".encode())

        # Start background receiver to avoid send buffer blockage
        def recv_loop():
            try:
                while True:
                    data = s.recv(4096)
                    if not data:
                        break
            except:
                pass

        threading.Thread(target=recv_loop, daemon=True).start()

        # Wait until all clients are ready
        start_event.wait()

        for i in range(MESSAGES_PER_CLIENT):
            msg = f"@all message {i} from {username}\n"
            try:
                s.sendall(msg.encode())
                with lock:
                    successful_sends += NUM_CLIENTS - 1
            except Exception:
                with lock:
                    failed_sends += NUM_CLIENTS - 1
                break

            time.sleep(random.uniform(0.001, 0.005))

        time.sleep(1)
        s.close()

    except Exception:
        with lock:
            failed_sends += NUM_CLIENTS - 1


def main():
    threads = []

    print(f"Starting {NUM_CLIENTS} clients...")

    start_time = time.time()

    for i in range(NUM_CLIENTS):
        t = threading.Thread(target=client_task, args=(i,))
        threads.append(t)
        t.start()

    # Give all clients time to connect
    time.sleep(2)

    print("All clients connected. Starting message send phase.")
    start_event.set()

    for t in threads:
        t.join()

    end_time = time.time()

    total_messages = NUM_CLIENTS * MESSAGES_PER_CLIENT * (NUM_CLIENTS - 1)

    print("\n===== Stress Test Results =====")
    print(f"Total fan-out messages attempted: {total_messages}")
    print(f"Successful sends: {successful_sends}")
    print(f"Failed sends: {failed_sends}")
    print(f"Time taken: {end_time - start_time:.2f} seconds")

    if end_time > start_time:
        print(f"Throughput: {total_messages / (end_time - start_time):,.0f} msgs/sec")


if __name__ == "__main__":
    main()
