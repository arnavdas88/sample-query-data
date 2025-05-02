import argparse
import subprocess
import multiprocessing
import signal
import sys
import time

stop_event = None  # Will be initialized later

def run_command(index, command, kill_flag):
    while not stop_event.is_set():
        try:
            proc = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            print(f"[{index}] Started PID {proc.pid}")

            start_time = time.time()

            while True:
                if stop_event.is_set():
                    proc.terminate()
                    break

                if kill_flag and time.time() - start_time >= 2:
                    print(f"[{index}] Killing PID {proc.pid} after 2s")
                    proc.terminate()
                    break

                time.sleep(0.1)

        except Exception as e:
            print(f"[{index}] ERROR: {e}")
            break

def signal_handler(sig, frame):
    print("\n[!] Caught interrupt. Terminating all processes...")
    stop_event.set()

def main():
    global stop_event
    parser = argparse.ArgumentParser(description="Run a command N times in parallel.")
    parser.add_argument('-N', type=int, required=True, help='Number of parallel processes')
    parser.add_argument('-k', action='store_true', help='Kill each process every 2 seconds and restart')
    parser.add_argument('command', nargs=argparse.REMAINDER, help='Command to run')

    args = parser.parse_args()

    if not args.command:
        print("No command provided to run.")
        sys.exit(1)

    stop_event = multiprocessing.Event()
    signal.signal(signal.SIGINT, signal_handler)

    processes = []

    while not stop_event.is_set():
        processes = [p for p in processes if p.is_alive()]

        while len(processes) < args.N:
            idx = len(processes)
            p = multiprocessing.Process(target=run_command, args=(idx, args.command, args.k))
            p.start()
            processes.append(p)

        time.sleep(0.5)

    for p in processes:
        if p.is_alive():
            p.terminate()
    for p in processes:
        p.join()

if __name__ == "__main__":
    try:
        multiprocessing.set_start_method('fork')
    except RuntimeError:
        pass  # Already set - safe to continue

    main()
