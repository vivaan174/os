# 🖥️ Adaptive Resource Allocation in Multiprogramming Systems

> Develop a system that dynamically adjusts resource allocation among multiple programs to optimize CPU and memory utilization. The solution should monitor system performance and reallocate resources in real-time to prevent bottlenecks.

A complete, single-file C implementation of a dynamic system resource manager with a built-in HTTP web server, interactive dashboard, REST API, workload simulator, and adaptive process controller — all in **~1,450 lines of pure C**.

---

## 📋 Table of Contents

1. [Project Overview](#project-overview)
2. [Architecture](#architecture)
3. [Data Structures](#data-structures)
4. [Core Modules](#core-modules)
   - [System Monitor](#1-system-monitor)
   - [Resource Manager](#2-resource-manager)
   - [Performance Optimizer](#3-performance-optimizer)
   - [Workload Simulator](#4-workload-simulator)
   - [HTTP Web Server](#5-http-web-server)
   - [Web UI Dashboard](#6-web-ui-dashboard)
5. [Allocation Strategies](#allocation-strategies)
6. [Priority Levels](#priority-levels)
7. [REST API Reference](#rest-api-reference)
8. [Concurrency Model](#concurrency-model)
9. [Build & Run](#build--run)
10. [How to Use](#how-to-use)
11. [System Requirements](#system-requirements)
12. [Key Constants & Limits](#key-constants--limits)

---

## Project Overview

This project solves the **adaptive resource allocation problem** in multiprogramming operating systems. The system:

- Continuously **monitors** real system CPU and memory usage by reading `/proc/stat`, `/proc/meminfo`, and `/proc/cpuinfo`
- **Tracks** up to 500 individual processes with per-process CPU and memory metrics via `/proc/<pid>/stat` and `/proc/<pid>/status`
- **Adaptively controls** resource usage by sending `SIGSTOP`/`SIGCONT` signals to low-priority processes when thresholds are breached
- **Simulates workloads** (CPU stress, memory allocation, I/O) to demonstrate real-time impact
- **Serves a web dashboard** through an embedded HTTP/1.1 server with a live Chart.js graph, control panels, and a workload event log

The entire system runs as a single binary with no external runtime dependencies.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        allocator (binary)                    │
│                                                             │
│  ┌──────────────┐   ┌──────────────┐   ┌────────────────┐  │
│  │ Monitor      │   │ Optimizer    │   │ HTTP Server    │  │
│  │ Thread       │   │ Thread       │   │ Thread         │  │
│  │ (every 1s)   │   │ (every 5s)   │   │ (always-on)    │  │
│  └──────┬───────┘   └──────┬───────┘   └───────┬────────┘  │
│         │                  │                   │           │
│         ▼                  ▼                   ▼           │
│  ┌──────────────────────────────────────────────────────┐  │
│  │               SystemState (global, mutex-protected)  │  │
│  │  • metrics[300]   — rolling history ring buffer      │  │
│  │  • tracked[500]   — per-process tracking table       │  │
│  │  • strategy       — active allocation strategy       │  │
│  │  • active_workloads                                  │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │        Workload Threads (spawned on demand)          │  │
│  │   cpu_workload_thread  |  memory_workload_thread     │  │
│  │   io_workload_thread                                 │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                    HTTP on port 7860
                              │
              ┌───────────────▼──────────────┐
              │   Browser  /  curl / client  │
              └──────────────────────────────┘
```

---

## Data Structures

### `SystemMetrics`
Captured every 1 second and stored in a 300-slot ring buffer:

| Field | Type | Description |
|---|---|---|
| `cpu_percent` | `double` | System-wide CPU usage % |
| `memory_percent` | `double` | % of total RAM in use |
| `cpu_count` | `int` | Number of logical CPU cores |
| `memory_used_mb` | `double` | RAM used in MB |
| `memory_total_mb` | `double` | Total RAM in MB |
| `memory_available_mb` | `double` | Available RAM in MB |
| `process_count` | `int` | Total processes on system |
| `timestamp` | `time_t` | Unix timestamp of sample |

### `TrackedProcess`
One entry per registered process in the tracking table (up to 500):

| Field | Type | Description |
|---|---|---|
| `pid` | `int` | Process ID |
| `name` | `char[256]` | Human-readable name |
| `priority` | `ProcessPriority` | CRITICAL / HIGH / NORMAL / LOW / BACKGROUND |
| `cpu_percent` | `double` | Per-process CPU usage |
| `memory_percent` | `double` | Per-process RAM usage (VmRSS-based) |
| `active` | `int` | `1` if process is alive, `0` if exited |
| `registered_time` | `time_t` | When the process was registered |

### `SystemState`
The single global struct (mutex-protected) that all threads share:

| Field | Description |
|---|---|
| `metrics[MAX_HISTORY]` | Rolling ring buffer of `SystemMetrics` (300 samples) |
| `history_count` | How many samples are currently stored |
| `running` | Whether monitoring is active (`1`) or paused (`0`) |
| `start_time` | Time of system start (for uptime calculation) |
| `strategy` | Current `AllocationStrategy` |
| `tracked[MAX_PROCESSES]` | Array of 500 `TrackedProcess` entries |
| `tracked_count` | Total entries ever added (including inactive) |
| `active_workloads` | Count of currently running workload threads |
| `lock` | `pthread_mutex_t` protecting all shared state |
| `monitor_thread` | Thread ID for the metrics collection loop |
| `optimizer_thread` | Thread ID for the adaptive control loop |
| `server_thread` | Thread ID for the HTTP server loop |
| `shutdown_flag` | Set to `1` to trigger clean shutdown of all threads |

---

## Core Modules

### 1. System Monitor

**Source:** `get_cpu_usage()`, `get_memory_usage()`, `count_processes()`, `get_cpu_count()`, `get_process_cpu_percent()`, `get_process_memory_percent()`, `collect_metrics()`

Reads directly from the Linux virtual filesystem — **no shell commands, no `popen`, no external tools**:

| Data Source | What It Provides |
|---|---|
| `/proc/stat` | Raw CPU tick counts (user, nice, system, idle, iowait, irq, softirq) → delta-computed CPU% |
| `/proc/meminfo` | `MemTotal`, `MemFree`, `MemAvailable` → memory % and MB figures |
| `/proc/cpuinfo` | Counts `processor:` lines → logical core count |
| `/proc/` directory | Counts numeric entries → total system process count |
| `/proc/<pid>/stat` | Per-process `utime + stime` → per-process CPU% |
| `/proc/<pid>/status` | `VmRSS` field → per-process resident memory % |
| `/proc/<pid>` existence | `access()` check → detects if a tracked process has exited |

The **monitor thread** calls `collect_metrics()` every **1 second**, updates the ring buffer, refreshes all per-process metrics, and removes dead processes automatically.

---

### 2. Resource Manager

**Source:** `register_process()`, `unregister_process()`, `set_priority()`, `get_tracked_count()`

- **`register_process(pid, name, priority)`** — verifies the PID exists in `/proc`, checks for duplicates, then adds it to the tracking table. Rejects if PID doesn't exist.
- **`unregister_process(pid)`** — marks the entry `active = 0` (soft delete; slot remains for history).
- **`set_priority(pid, priority)`** — updates the stored priority level for a tracked process. This affects the optimizer's SIGSTOP/SIGCONT decisions.
- **`get_tracked_count()`** — returns count of processes with `active == 1`.

All operations are mutex-locked to be thread-safe.

---

### 3. Performance Optimizer

**Source:** `apply_adaptive_control()`

Called every **5 seconds** by the optimizer thread. Implements the core resource reallocation logic:

```
IF cpu_percent > 85% OR memory_percent > 90%:
    → Send SIGSTOP to all tracked processes with priority <= LOW
       (suspends them, freeing CPU/memory for higher-priority work)
ELSE:
    → Send SIGCONT to all tracked processes with priority <= LOW
       (resumes them when resources are available again)
```

This directly maps to the OS concept of **preemptive resource allocation** — the system forcibly pauses background/low-priority processes under load and resumes them when headroom is restored.

The `get_report_text()` function also provides **smart recommendations**:
- ⚠️ CPU > 80% → suggests workload reduction
- ⚠️ Memory > 85% → suggests closing applications
- ⚠️ Process count > 400 → warns of system crowding
- ✅ All clear → confirms optimal operation

---

### 4. Workload Simulator

**Source:** `cpu_workload_thread()`, `memory_workload_thread()`, `io_workload_thread()`

Three types of stress tests, each running for **30 seconds** in a detached thread:

#### CPU Stress (`/api/workload-cpu`)
- Runs a tight arithmetic loop: `sum += i * i` repeated `100,000 × intensity / 100` times
- Intensity is 0–100% (controlled via UI slider)
- Directly measurable on the real-time chart

#### Memory Stress (`/api/workload-memory`)
- Allocates a configurable block (1–500 MB) via `malloc()`
- Fills it with `0xAA` using `memset()` to ensure it's resident in RAM (not paged out)
- Holds for 30 seconds then `free()`s it
- Directly visible as a spike on the memory usage graph

#### I/O Stress (`/api/workload-io`)
- Repeatedly creates, writes to, and deletes up to 50 temporary files in `/tmp`
- Each iteration writes 1,000 bytes (`XXXXXXXXXX` × 100) per file
- Tests filesystem throughput and inode pressure

All workload threads decrement `state.active_workloads` when they exit. `Stop All Workloads` sets `shutdown_flag = 1` for 2 seconds, signalling all loops to break.

---

### 5. HTTP Web Server

**Source:** `server_thread_func()`, `parse_http_request()`, `send_http_response()`, `handle_http_request()`

A minimal but complete **HTTP/1.1 server** built from scratch using POSIX sockets:

- Listens on **port 7860** (all interfaces, `INADDR_ANY`)
- `SO_REUSEADDR` enabled to allow fast restarts
- Accept loop: for each connection, reads up to 16 KB, parses the request line and body, dispatches to the correct handler, sends response, closes socket
- **CORS headers** (`Access-Control-Allow-Origin: *`) included on all responses

#### Request Parser
`parse_http_request()` extracts:
- Method (`GET`, `POST`)
- Path (`/api/status`, etc.)
- Body (everything after `\r\n\r\n`)

#### JSON Helpers
Two lightweight parsers (no external library):
- `json_get_int(json, key)` — scans for `"key":` and reads an integer
- `json_get_string(json, key, out, max_len)` — scans for `"key":"value"` and extracts the string

#### Process Spawning via `fork`/`execvp`
The `/api/start-process` endpoint uses **direct system calls** instead of `system()` or `popen()`:
1. Tokenises the command string into `argv[]`
2. `fork()` creates a child
3. Child calls `setsid()` to detach from the parent's session
4. Child calls `execvp(argv[0], argv)` — replaces itself with the target program
5. Parent returns the new PID immediately

---

### 6. Web UI Dashboard

**Source:** `get_html_page()` — a 300-line HTML/CSS/JS string embedded directly in the binary

The web interface is served at `http://localhost:7860/` and auto-refreshes every **2 seconds**. No external framework — just HTML5, vanilla CSS, and vanilla JavaScript with the `fetch()` API.

#### Sections

| Section | Controls | Description |
|---|---|---|
| **System Control** | Start / Stop buttons | Activates/pauses the monitor and optimizer threads |
| **Strategy & Process Runner** | Dropdown + Apply | Switches allocation strategy; text input to launch shell commands |
| **Monitor & Reports** | Refresh, Generate Report | Live status text box; full performance report |
| **Real-time System Impact Graph** | (automatic) | Chart.js line chart — CPU% and Memory% over last 20 samples |
| **Programs – Available PIDs** | Show PIDs button | Lists up to 100 running processes from `/proc` with names |
| **Programs – Register** | PID, Name, Priority | Adds a process to the tracking table |
| **Programs – Management** | PID, Priority, Unregister | Updates priority or removes a process |
| **Programs – Tracked** | Auto-Refresh button | Shows all active tracked processes with live CPU/Mem stats |
| **Workload Testing – CPU** | Intensity slider (0–100%) | Launches a CPU stress thread |
| **Workload Testing – Memory** | Size slider (1–500 MB) | Launches a memory allocation stress thread |
| **Workload Testing – I/O** | File count slider (1–50) | Launches an I/O stress thread |
| **Workload Impact Dashboard** | (automatic) | Live progress bars for CPU/Memory impact + active workload count |
| **Workload Event Log** | (automatic) | Timestamped log of every workload action taken |

---

## Allocation Strategies

Set via `POST /api/set-strategy` or the UI dropdown:

| Value | Name | Behaviour |
|---|---|---|
| `0` | **Equal** | Resources shared evenly across all tracked processes |
| `1` | **Priority** | Higher-priority processes protected; lower-priority suspended first |
| `2` | **Performance** *(default)* | Optimise for overall system throughput |
| `3` | **Demand** | Allocate resources proportional to current demand |

> The strategy value is stored in `state.strategy` and influences optimizer decisions and future allocation logic.

---

## Priority Levels

| Level | Value | Behaviour under load |
|---|---|---|
| `CRITICAL` | 5 | Never suspended |
| `HIGH` | 4 | Never suspended |
| `NORMAL` | 3 | Never suspended |
| `LOW` | 2 | Suspended via `SIGSTOP` when CPU > 85% or Memory > 90% |
| `BACKGROUND` | 1 | Suspended via `SIGSTOP` when CPU > 85% or Memory > 90% |

---

## REST API Reference

Base URL: `http://localhost:7860`

| Method | Endpoint | Body (JSON) | Response |
|---|---|---|---|
| `GET` | `/` | — | HTML dashboard page |
| `GET` | `/api/status` | — | `{running, uptime_seconds, strategy, tracked_programs, cpu_percent, memory_percent, cpu_count, process_count, active_workloads}` |
| `GET` | `/api/tracked` | — | `{tracked: [{pid, name, priority, cpu, memory}, ...]}` |
| `GET` | `/api/report` | — | Plain-text comprehensive performance report |
| `GET` | `/api/available-pids` | — | Plain-text list of up to 100 running PIDs with names |
| `POST` | `/api/start` | — | `{message}` — activates monitoring |
| `POST` | `/api/stop` | — | `{message}` — pauses monitoring |
| `POST` | `/api/set-strategy` | `{strategy: 0-3}` | `{message}` |
| `POST` | `/api/start-process` | `{command: "sleep 60"}` | `{message}` including new PID |
| `POST` | `/api/register-process` | `{pid, name, priority}` | `{message}` |
| `POST` | `/api/unregister-process` | `{pid}` | `{message}` |
| `POST` | `/api/set-priority` | `{pid, priority}` | `{message}` |
| `POST` | `/api/workload-cpu` | `{intensity: 0-100}` | `{message}` |
| `POST` | `/api/workload-memory` | `{size: 1-500}` | `{message}` (size in MB) |
| `POST` | `/api/workload-io` | `{files: 1-50}` | `{message}` |
| `POST` | `/api/workload-stop` | — | `{message}` — signals all workload threads to exit |

---

## Concurrency Model

The system uses **4 concurrent POSIX threads**:

| Thread | Function | Interval | Role |
|---|---|---|---|
| `server_thread` | `server_thread_func()` | Always-on | Accept HTTP connections, dispatch handlers |
| `monitor_thread` | `monitor_thread_func()` | Every 1 second | Collect system + per-process metrics |
| `optimizer_thread` | `optimizer_thread_func()` | Every 5 seconds | Apply adaptive SIGSTOP/SIGCONT control |
| `workload_thread(s)` | `cpu/memory/io_workload_thread()` | On-demand, 30s | Stress test the system |

All shared state is protected by a single `pthread_mutex_t` (`state.lock`).

**Shutdown sequence:**
1. `state.shutdown_flag = 1`
2. Monitor and optimizer loops break on next iteration
3. Server accept loop breaks
4. `sleep(2)` allows in-flight threads to finish
5. `pthread_mutex_destroy()` cleans up
6. Program exits cleanly

---

## Build & Run

### Prerequisites
- GCC or Clang
- Linux (or WSL on Windows) — requires `/proc` filesystem
- `pthreads` library

### Compile

```bash
gcc -o allocator allocator.c -lpthread -lm
```

### Run

```bash
./allocator
```

### Open the Dashboard

```
http://localhost:7860
```

---

## How to Use

1. **Build and run** the binary.
2. **Open** `http://localhost:7860` in a browser.
3. Click **▶️ Start System** to activate monitoring and the optimizer.
4. Use **🔍 Show Available PIDs** to see running processes on your machine.
5. **Register** a process by entering its PID, a label, and a priority level.
6. Watch it appear in the **Tracked Programs** panel with live CPU/Mem stats.
7. Launch a **CPU**, **Memory**, or **I/O** workload — observe the real-time chart spike.
8. Under load, the optimizer will automatically **SIGSTOP** any `LOW`/`BACKGROUND` tracked processes.
9. Use **Generate Full Report** for a diagnostic summary with smart recommendations.
10. Click **⏹️ Stop System** to pause monitoring; the server continues running.

---

## System Requirements

| Requirement | Minimum |
|---|---|
| OS | Linux (kernel 2.6+) or WSL2 |
| Compiler | GCC 4.8+ or Clang 3.5+ |
| Libraries | `libpthread`, `libm` |
| RAM | ~5 MB (binary + state) + workload memory |
| Port | 7860 (must be free) |

> **Windows users:** Run inside WSL2. The `/proc` virtual filesystem is required for all monitoring features.

---

## Key Constants & Limits

| Constant | Value | Purpose |
|---|---|---|
| `MAX_PROCESSES` | 500 | Maximum tracked processes |
| `MAX_HISTORY` | 300 | Rolling metrics ring buffer size (~5 minutes at 1s interval) |
| `BUFFER_SIZE` | 16,384 bytes | HTTP request read buffer |
| `MAX_JSON_SIZE` | 65,536 bytes | Maximum JSON response size |
| `PORT` | 7860 | HTTP server port |
| CPU threshold | 85% | Triggers SIGSTOP for low-priority processes |
| Memory threshold | 90% | Triggers SIGSTOP for low-priority processes |
| Workload duration | 30 seconds | How long each stress thread runs |
| Max workload memory | 500 MB | Upper cap on memory stress test |
| Max I/O files | 50 | Upper cap on I/O stress test file count |
| Chart window | 20 samples | Points shown on the live impact graph |
| PID listing | 100 | Max PIDs shown in the Available PIDs panel |
