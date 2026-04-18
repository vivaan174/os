# Dynamic Resource Allocation System

This project demonstrates a Python-based resource manager that monitors system processes and dynamically adjusts CPU and memory utilization by changing process priority and suspending low-priority processes.

## Features

- Monitor CPU and memory usage for active processes
- Detect high utilization and prioritize critical workloads
- Lower priority or suspend non-critical processes when thresholds are exceeded
- Simulate multiple workloads for testing

## Installation

```powershell
cd c:\Users\anshika\Downloads\Speckey-main\Speckey-main\os
python -m pip install -r requirements.txt
```

## Usage

Start the resource manager:

```powershell
python main.py --cpu-threshold 70 --mem-threshold 70 --interval 1.0
```

Run the monitor with a simulated workload:

```powershell
python main.py --simulate --duration 60
```

## Notes

- On Windows, process priority changes require administrator permissions for some targets.
- This implementation uses `psutil` and Windows priority classes; it is intended as a demonstration rather than a full production scheduler.
