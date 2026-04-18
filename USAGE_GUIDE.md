# Dynamic Resource Allocator - Usage Guide

## Quick Start

### 1. Installation
```bash
pip install psutil
```

### 2. Basic Usage
```bash
# Start monitoring system resources
python main.py

# With 60-second duration
python main.py --duration 60

# Interactive mode
python main.py --interactive
```

### 3. With Simulation
```bash
# Start with workload simulator
python main.py --simulate --cpu-processes 3 --memory-processes 2 --sim-duration 120
```

## Command-Line Options

### Core Options
| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--monitor-only` | flag | - | Run in monitoring-only mode |
| `--interactive` | flag | - | Run interactive CLI |
| `--duration` | int | 0 | Runtime in seconds (0=infinite) |

### Configuration
| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--config` | str | config.json | Configuration file path |
| `--save-config` | str | - | Save config to file |
| `--strategy` | str | performance | Allocation strategy |
| `--cpu-threshold` | float | 80.0 | CPU warning threshold (%) |
| `--mem-threshold` | float | 85.0 | Memory warning threshold (%) |

### Simulation
| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--simulate` | flag | - | Start workload simulator |
| `--cpu-processes` | int | 2 | CPU-bound processes |
| `--memory-processes` | int | 2 | Memory-bound processes |
| `--sim-duration` | int | 60 | Simulation duration (seconds) |

### Reporting
| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--export-report` | str | - | Export report to JSON file |
| `--report-interval` | int | 0 | Report interval (seconds) |

### Monitoring
| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--monitor-interval` | float | 1.0 | Monitoring interval (seconds) |
| `--optimize-interval` | float | 5.0 | Optimization interval (seconds) |

## Usage Examples

### Example 1: Monitor System for 2 Minutes
```bash
python main.py --duration 120
```

### Example 2: Simulate High Load with Resource Management
```bash
python main.py --simulate --cpu-processes 5 --memory-processes 3 --sim-duration 300
```

### Example 3: Use PRIORITY Allocation Strategy
```bash
python main.py --strategy priority --interactive
```

### Example 4: Monitor with Custom Configuration
```bash
python main.py --config custom_config.json --duration 60 --export-report report.json
```

### Example 5: Aggressive Threshold Monitoring
```bash
python main.py --cpu-threshold 70 --mem-threshold 80 --report-interval 5
```

### Example 6: Performance Report Export
```bash
python main.py --simulate --duration 120 --export-report final_report.json
```

## Interactive Commands

When running with `--interactive` flag:

```
start              - Start resource allocation
stop               - Stop resource allocation  
status             - Show current system status
top                - Show top processes by CPU
report             - Show detailed performance report
register PID       - Register program for management
strategy STR       - Change allocation strategy
export FILE        - Export report to JSON
help               - Show help
exit               - Exit program
```

### Interactive Example Session
```
>> status
{
  "running": true,
  "uptime_seconds": 125.4,
  "system_metrics": {
    "cpu_percent": 45.2,
    "memory_percent": 62.8,
    ...
  }
}
>> top
Top Processes by CPU:
  1234   chrome                   CPU: 15.32%
  5678   python                   CPU: 12.15%
  ...
>> register 5678
Registered program PID: 5678
>> strategy priority
Changed allocation strategy to: priority
```

## Configuration File

Edit `config.json` to customize system behavior:

```json
{
  "monitoring_interval": 1.0,
  "optimization_interval": 5.0,
  "cpu_threshold_high": 80,
  "cpu_threshold_critical": 95,
  "memory_threshold_high": 85,
  "memory_threshold_critical": 95,
  "allocation_strategy": "performance",
  "enable_logging": true,
  "max_history_entries": 300,
  "reserved_memory_percent": 10
}
```

Key settings:
- `monitoring_interval`: How often to collect metrics (lower = more data, higher CPU)
- `optimization_interval`: How often to rebalance resources
- `allocation_strategy`: Default resource allocation method
- `reserved_memory_percent`: Always keep this much memory free

## Programmatic Usage

```python
from dynamic_allocator import DynamicResourceAllocator
from resource_manager import ProcessPriority, ResourceAllocationStrategy

# Create allocator
allocator = DynamicResourceAllocator()

# Start system
allocator.start()

# Register a program
allocator.register_program(
    pid=1234,
    program_name="MyApp",
    priority=ProcessPriority.HIGH
)

# Change strategy
allocator.set_allocation_strategy(ResourceAllocationStrategy.PRIORITY)

# Get status
status = allocator.get_system_status()
print(f"CPU: {status['system_metrics']['cpu_percent']}%")

# Export report
allocator.export_report("report.json")

# Stop system
allocator.stop()
```

## Resource Allocation Strategies

### EQUAL Strategy
- Resources split equally among all processes
- Fair distribution
- Best for: Homogeneous workloads

```bash
python main.py --strategy equal
```

### PRIORITY Strategy  
- Resources based on process priority levels
- CRITICAL > HIGH > NORMAL > LOW > BACKGROUND
- Best for: Mixed workloads with clear priorities

```bash
python main.py --strategy priority
```

### PERFORMANCE Strategy (Recommended)
- Uses historical performance data
- Learns optimal allocation patterns
- Adapts to changing conditions
- Best for: Most real-world scenarios

```bash
python main.py --strategy performance
```

### DEMAND Strategy
- Allocates based on immediate demand signals
- Responsive to rapid changes
- Best for: Highly variable workloads

```bash
python main.py --strategy demand
```

## Monitoring Output

### Console Logs
```
2026-04-19 10:30:45,123 [INFO    ] DynamicResourceAllocator: Starting Dynamic Resource Allocator
2026-04-19 10:30:45,234 [INFO    ] ResourceManager: Registered process chrome (PID: 5678) with priority HIGH
2026-04-19 10:30:50,456 [WARNING ] ResourceManager: CPU usage high: 92.5% (threshold: 80%)
```

### JSON Report Sample
```json
{
  "timestamp": "2026-04-19T10:31:00",
  "system_status": {
    "running": true,
    "uptime_seconds": 61.2,
    "system_metrics": {
      "cpu_percent": 45.2,
      "memory_percent": 62.8,
      "process_count": 145
    },
    "optimizer_stats": {
      "total_optimizations": 12,
      "successful_reallocations": 11,
      "success_rate": 0.917
    }
  },
  "performance_report": {
    "top_processes_by_cpu": [
      {
        "pid": 1234,
        "name": "program.exe",
        "cpu_percent": 25.3,
        "memory_mb": 512.4
      }
    ]
  }
}
```

## Performance Tuning

### For Lower CPU Overhead
```bash
# Increase monitoring interval
python main.py --monitor-interval 2.0 --optimize-interval 10.0
```

### For Better Responsiveness  
```bash
# Decrease monitoring interval
python main.py --monitor-interval 0.5 --optimize-interval 2.0
```

### For Memory-Constrained Systems
```bash
# Reduce history entries in config.json
"max_history_entries": 100
```

## Troubleshooting

### Permission Denied Errors
```bash
# Linux/Mac - use sudo
sudo python main.py

# Windows - run as Administrator
python main.py
```

### High CPU Usage
```bash
# Increase monitoring interval
python main.py --monitor-interval 5.0 --optimize-interval 15.0
```

### Memory Issues
Edit `config.json`:
```json
{
  "max_history_entries": 60,
  "reserved_memory_percent": 15
}
```

### Missing psutil
```bash
pip install --upgrade psutil
```

## Log Files

Generated logs:
- `resource_allocator.log` - Main system log
- `resource_manager.log` - Allocation decisions
- `performance_optimizer.log` - Optimization activities
- `dynamic_allocator_main.log` - Entry point logs

View logs:
```bash
# Linux/Mac
tail -f resource_allocator.log

# Windows
type resource_allocator.log
```

## Performance Benchmarks

Typical system overhead:
- Memory: 15-20 MB base + 100-200 bytes per tracked process
- CPU: 0.5-2% depending on configuration
- Disk I/O: Minimal (logging only)

## Best Practices

1. **Start with default configuration** - It's tuned for most scenarios
2. **Use PERFORMANCE strategy** - Adapts to your workload
3. **Monitor logs regularly** - Catch issues early
4. **Test before production** - Verify with your workloads
5. **Adjust thresholds appropriately** - Match your SLAs
6. **Export reports regularly** - Track performance trends

## Advanced Scenarios

### Protect Critical Database
```python
allocator.register_program(2847, "DatabaseServer", ProcessPriority.CRITICAL)
allocator.set_allocation_strategy(ResourceAllocationStrategy.PRIORITY)
```

### Prevent Background Interference
```bash
python main.py --strategy priority  # Give priority processes superior resources
```

### Emergency Resource Reclamation
```python
# Monitor for overload and throttle if needed
status = allocator.get_system_status()
if status['system_metrics']['memory_percent'] > 95:
    allocator.set_program_priority(task_pid, ProcessPriority.LOW)
```

## Support

- Check logs: `resource_allocator.log`
- Export report: `--export-report file.json`
- Run interactively: `--interactive`
- View config: `cat config.json`

---

**Last Updated**: April 19, 2026  
**Version**: 1.0
