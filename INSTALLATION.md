# Installation & Setup Guide

## Prerequisites
- Python 3.8+
- pip (Python package manager)

## Quick Installation

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

Required packages:
- **psutil**: System and process utilities (CPU, memory, process monitoring)
- **gradio**: Web UI framework for the interface

### Step 2: Run the Application
```bash
python app.py
```

### Step 3: Access the Web Interface
Open your browser and navigate to:
```
http://localhost:7860
```

## Features & Tabs

### 🎮 Control Tab
- **Start System**: Initialize resource monitor and optimizer
- **Stop System**: Gracefully shutdown all components
- **Change Strategy**: Select allocation strategy (equal, priority, performance, demand)

### 📊 Monitor Tab
- **Refresh**: Get real-time system metrics
- Shows CPU%, memory%, process count
- Displays system uptime

### 📋 Programs Tab
- **Show Available PIDs**: View all running processes on system
- **Register**: Add a process to management
  - Enter PID (process ID)
  - Set name and priority level
- **Update Priority**: Change priority for tracked processes
  - Supports 5 levels: CRITICAL → BACKGROUND
- **Unregister**: Remove process from tracking

### 🎯 Tracked Tab
- **Refresh**: View all currently managed processes
- Shows PID, name, and assigned priority

### 📈 Reports Tab
- **Generate Report**: Get system performance analysis
- Recommendations for optimization
- Tracked process count

### ⚡ Workload Test Tab (Hard Mode)
- **CPU Stress Test**: 0-100% intensity for 30 seconds
- **Memory Stress Test**: 1-500 MB allocation for 30 seconds
- **I/O Stress Test**: File operations test
- **Status**: Check active workload threads
- **Stop All**: Terminate all running workloads

## Process Priorities

1. **CRITICAL** - Highest priority, never suspended
2. **HIGH** - Important processes, protected from suspension
3. **NORMAL** - Standard priority
4. **LOW** - Can be suspended under high load
5. **BACKGROUND** - Lowest priority, first to suspend

## Resource Management

### Automatic Behavior

When CPU usage exceeds:
- **80%**: Warning logged, elevated alert
- **85%**: Adaptive control engaged
  - LOW and BACKGROUND processes suspended
  - Non-critical processes limited
  
When Memory usage exceeds:
- **85%**: Warning logged
- **90%**: Adaptive control engaged
  - Stricter process suspension

### Manual Control

1. Register high-priority processes as CRITICAL or HIGH
2. Register background tasks as LOW or BACKGROUND
3. Monitor system via Monitor tab
4. Generate reports for analysis

## Testing Hard Mode Features

### Test Scenario 1: Priority-Based Allocation
```
1. Start system (Control tab)
2. View available PIDs (Programs tab)
3. Register explorer.exe as HIGH priority
4. Register a less critical process as LOW priority
5. Monitor allocation (Monitor tab)
```

### Test Scenario 2: High Utilization Response
```
1. Start system
2. Register a process as LOW priority
3. Go to Workload Test tab
4. Start CPU workload at 90% intensity
5. Monitor system response in Monitor tab
6. Watch logs for suspension events
7. Stop workload to see resumption
```

### Test Scenario 3: Combined Stress
```
1. Start system
2. Register multiple processes with different priorities
3. Start CPU workload (80% intensity)
4. Start Memory workload (300 MB)
5. Generate report to see recommendations
6. Stop all workloads
```

### Test Scenario 4: Strategy Switching
```
1. Start system
2. Change strategy to "priority" (Control tab)
3. Register processes with different priorities
4. Start workload
5. Observe how resources are allocated based on priority
```

## Log Files

The application creates several log files for monitoring:

- **system_monitor.log**: System monitoring events
- **resource_manager.log**: Process management operations
- **performance_optimizer.log**: Optimization actions
- **resource_allocator.log**: Overall system events
- **workload_simulator.log**: Workload test events
- **unified_app.log**: Frontend events

## Troubleshooting

### Port 7860 Already in Use
If you get "Cannot find empty port in range: 7860-7860":
1. Kill existing Python processes: `taskkill /F /IM python.exe`
2. Or modify the port in the code (search for `server_port=7860`)

### Permission Denied Errors
Some operations require admin privileges:
- Suspending/resuming processes
- Accessing certain system resources
- Run as Administrator if needed

### Process Not Found
- The PID must be a currently running process
- Check "Show Available PIDs" for valid PIDs
- Avoid PID 0, 1, 2 (system processes)

## Performance Tips

1. **Start with fewer tracked processes** (< 10) for better performance
2. **Use HIGH/CRITICAL priorities** for important processes only
3. **Monitor regularly** via the Monitor tab
4. **Review logs** for optimization recommendations
5. **Test with reasonable workloads** (don't exceed 100% intensity continuously)

## Architecture

- **Backend**: Python with threading
- **Frontend**: Gradio web interface
- **Monitoring**: psutil library (1-second sampling)
- **Optimization**: 5-second cycles
- **Storage**: File-based logging

## System Requirements

- **CPU**: Any processor
- **Memory**: 512 MB minimum
- **Disk**: 100 MB free space
- **Network**: Localhost only (default)

## Advanced Usage

### Custom Port
Edit `app.py`, line ~960:
```python
interface.launch(
    server_name="0.0.0.0",
    server_port=8000,  # Change this
    debug=False
)
```

### Remote Access
Change `server_name` to allow remote connections:
```python
server_name="0.0.0.0"  # Accessible remotely
# or
server_name="192.168.1.100"  # Specific IP
```

### Network Sharing
```python
interface.launch(
    server_name="0.0.0.0",
    server_port=7860,
    share=True  # Creates public link
)
```

## Support & Documentation

- Check log files in the same directory as app.py
- Review HARD_MODE_VERIFICATION.md for detailed features
- Test scenarios are in this guide

---

**Tested on**: Windows 10+, Python 3.10+
**Status**: Production Ready ✅
