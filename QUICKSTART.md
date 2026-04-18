# Dynamic Resource Allocator - Quick Start Guide

## ⚡ 5-Minute Setup

### Step 1: Install Dependencies
```bash
pip install psutil
```

### Step 2: Run the System
```bash
python main.py --duration 60
```

That's it! The system is now monitoring and optimizing resources.

---

## 🚀 Common Use Cases

### 1. Monitor System for 5 Minutes
```bash
python main.py --duration 300
```

### 2. Test with Simulated High Load
```bash
python main.py --simulate --cpu-processes 4 --memory-processes 3 --duration 120
```

### 3. Interactive Mode (Best for Learning)
```bash
python main.py --interactive
```

**Then use commands like:**
```
>> start
>> status
>> top
>> report
>> exit
```

### 4. Export Performance Report
```bash
python main.py --simulate --duration 60 --export-report report.json
```

Then view the JSON file to see detailed metrics.

### 5. Use Priority-Based Allocation
```bash
python main.py --strategy priority --duration 60
```

---

## 📊 What Gets Monitored?

The system tracks:
- **CPU Usage** - Percentage and per-core allocation
- **Memory** - Physical and virtual memory usage
- **Processes** - Individual process metrics
- **Performance Metrics** - Trends, bottlenecks, optimization results

---

## 🎯 How It Works in 30 Seconds

1. **Monitors** (Every 1 second) - Collects CPU/memory metrics
2. **Analyzes** (Every 5 seconds) - Detects bottlenecks and performance issues
3. **Optimizes** (Every 5 seconds) - Adjusts resource allocation
4. **Reports** - Provides detailed performance insights

---

## 📁 Key Files

| File | Purpose |
|------|---------|
| `main.py` | Entry point - run this file |
| `dynamic_allocator.py` | Main system orchestrator |
| `system_monitor.py` | Collects system metrics |
| `resource_manager.py` | Manages resource allocation |
| `performance_optimizer.py` | Analyzes and optimizes |
| `config.json` | Configuration settings |
| `example_usage.py` | Runnable examples |
| `test_allocator.py` | Unit and integration tests |

---

## 🔧 Configuration Quick Tips

Edit `config.json` to adjust:

```json
{
  "monitoring_interval": 1.0,
  "optimization_interval": 5.0,
  "allocation_strategy": "performance",
  "cpu_threshold_high": 80,
  "memory_threshold_high": 85
}
```

Key settings:
- **monitoring_interval**: How often to collect data (lower = more responsive)
- **optimization_interval**: How often to rebalance (lower = more aggressive)
- **allocation_strategy**: "performance" recommended for most cases
- **thresholds**: When to trigger warnings

---

## 📊 Allocation Strategies Explained

### PERFORMANCE (Recommended ⭐)
- Learns from workload history
- Automatically adapts
- Best for mixed workloads
```bash
python main.py --strategy performance
```

### PRIORITY
- Allocates by importance level
- CRITICAL gets more resources than BACKGROUND
- Good when priorities are clear
```bash
python main.py --strategy priority
```

### EQUAL
- Fair distribution
- Simple and predictable
```bash
python main.py --strategy equal
```

### DEMAND
- Responds to immediate needs
- Fast reaction to load changes
```bash
python main.py --strategy demand
```

---

## 🎓 Example Programs

### Run All Demos
```bash
python example_usage.py
```

This runs 5 different demonstration scenarios showing:
1. Basic system usage
2. Program registration
3. Strategy switching
4. Monitoring and export
5. Performance optimization

### Simple Example
```bash
python example_usage.py simple
```

Quick 5-second demo.

---

## 📈 Understanding Output

### Console Output
```
2026-04-19 10:30:45 [INFO    ] Starting Dynamic Resource Allocator
2026-04-19 10:30:45 [INFO    ] Allocation strategy: performance
2026-04-19 10:30:50 [WARNING ] CPU usage high: 92.5% (threshold: 80%)
```

### Interactive Mode Status
```
>> status
{
  "running": true,
  "cpu_percent": 45.2,
  "memory_percent": 62.8,
  "processes": 145
}
```

### Top Processes
```
>> top
Top Processes by CPU:
  1. chrome (PID: 1234)     CPU: 25.3%
  2. python (PID: 5678)     CPU: 15.8%
  3. ...
```

---

## 🧪 Run Tests

Verify everything works:
```bash
python test_allocator.py
```

This runs unit and integration tests to verify all components.

---

## 🐛 Troubleshooting

### "Permission Denied"
Run with elevated privileges:
```bash
# Linux/Mac
sudo python main.py

# Windows
# Run Command Prompt as Administrator, then:
python main.py
```

### High CPU Usage by allocator
```bash
# Reduce monitoring frequency
python main.py --monitor-interval 2.0 --optimize-interval 10.0
```

### "ModuleNotFoundError: No module named 'psutil'"
```bash
pip install psutil --upgrade
```

### Finding Logs
- `resource_allocator.log` - Main system log
- `resource_manager.log` - Allocation decisions
- `performance_optimizer.log` - Optimization details

---

## 🔄 Typical Workflow

1. **Start with defaults**
   ```bash
   python main.py --interactive
   ```

2. **Monitor system**
   ```
   >> status
   >> top
   ```

3. **Register your apps** (if needed)
   ```
   >> register 1234
   ```

4. **Try different strategies**
   ```
   >> strategy priority
   ```

5. **Export report**
   ```
   >> export report.json
   ```

6. **Exit**
   ```
   >> exit
   ```

---

## 📚 Learn More

- **USAGE_GUIDE.md** - Comprehensive usage documentation
- **ARCHITECTURE.md** - System design and internals
- **README.md** - Full technical reference
- **example_usage.py** - Python API examples

---

## ✅ Verification Checklist

- [ ] Dependencies installed (`pip install psutil`)
- [ ] Run basic system: `python main.py --duration 30`
- [ ] Check logs: View any `.log` files generated
- [ ] Try interactive: `python main.py --interactive`
- [ ] Run tests: `python test_allocator.py`
- [ ] Try simulation: `python main.py --simulate --duration 60`
- [ ] Export report: `python main.py --export-report test.json`

---

## 🎉 You're Ready!

The Dynamic Resource Allocator is now set up and ready to optimize your system resources. Start with:

```bash
python main.py --interactive
```

Type `help` for commands, or refer to this guide for quick reference.

---

**Questions?** Check the logs, read the documentation, or examine `example_usage.py` for code patterns.

**Happy optimizing! 🚀**
