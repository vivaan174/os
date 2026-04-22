# Dynamic Resource Allocator (C)

A high-performance system resource allocator written in C. It monitors CPU and memory usage, manages workloads via a REST API, and dynamically adjusts process priorities using direct system calls.

## Build

```bash
gcc -o allocator allocator.c -lpthread
```

## Run

```bash
./allocator
```

The server starts on `http://localhost:8080` by default.

## Features

- Real-time CPU and memory monitoring
- REST API for workload submission and management
- Dynamic process priority adjustment via `fork`/`execvp`
- Thread-safe multi-client HTTP server
- Live performance metrics

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/status` | System status and metrics |
| POST | `/api/workload` | Submit a new workload |
| GET | `/api/workloads` | List all workloads |
| DELETE | `/api/workload/:id` | Stop a workload |

## Notes

- Requires a POSIX-compatible system (Linux/macOS) or WSL on Windows.
- Run with appropriate permissions for process priority changes.
