import argparse
import multiprocessing
import random
import threading
import time


def cpu_worker(duration: int) -> None:
    end = time.time() + duration
    while time.time() < end:
        x = 0
        for i in range(100000):
            x += i * i


def memory_worker(duration: int, size_mb: int) -> None:
    blocks = []
    block = b"0" * 1024 * 1024
    for _ in range(size_mb):
        blocks.append(block)
        time.sleep(0.05)
    time.sleep(duration)
    del blocks


def start_simulator(num_cpu: int, num_mem: int, duration: int) -> None:
    processes = []
    for _ in range(num_cpu):
        proc = multiprocessing.Process(target=cpu_worker, args=(duration,))
        proc.start()
        processes.append(proc)

    for _ in range(num_mem):
        size_mb = random.randint(100, 200)
        proc = multiprocessing.Process(target=memory_worker, args=(duration, size_mb))
        proc.start()
        processes.append(proc)

    for proc in processes:
        proc.join()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a workload simulator for the resource manager.")
    parser.add_argument("--cpu-processes", type=int, default=2, help="Number of CPU-bound worker processes")
    parser.add_argument("--memory-processes", type=int, default=2, help="Number of memory-bound worker processes")
    parser.add_argument("--duration", type=int, default=60, help="Duration in seconds for the workload")
    args = parser.parse_args()
    start_simulator(args.cpu_processes, args.memory_processes, args.duration)


if __name__ == "__main__":
    main()
