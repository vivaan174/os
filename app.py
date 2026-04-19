"""
Complete Dynamic Resource Allocator - All-in-One Application
Backend + Frontend (Gradio) in a Single Python File

This standalone application includes:
- Real-time system monitoring
- Dynamic resource allocation
- Performance optimization
- Web-based UI with Gradio
- Program registration and management

Run: python app.py
Access: http://localhost:7860
"""

import gradio as gr
import threading
import time
import json
import logging
import psutil
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass, asdict
import statistics

# ============================================================================
# ENUMS AND DATA STRUCTURES
# ============================================================================

class ProcessPriority(Enum):
    """Process priority levels"""
    CRITICAL = 5
    HIGH = 4
    NORMAL = 3
    LOW = 2
    BACKGROUND = 1

class ResourceAllocationStrategy(Enum):
    """Resource allocation strategies"""
    EQUAL = "equal"
    PRIORITY = "priority"
    PERFORMANCE = "performance"
    DEMAND = "demand"

@dataclass
class SystemMetrics:
    """System-wide metrics"""
    timestamp: datetime
    cpu_percent: float
    cpu_count: int
    memory_percent: float
    memory_used_mb: float
    memory_total_mb: float
    memory_available_mb: float
    process_count: int

@dataclass
class ProcessMetrics:
    """Per-process metrics"""
    pid: int
    name: str
    cpu_percent: float
    memory_percent: float
    memory_mb: float

# ============================================================================
# SYSTEM MONITOR
# ============================================================================

class SystemMonitor:
    """Real-time system resource monitoring"""
    
    def __init__(self, sampling_interval: float = 1.0):
        self.sampling_interval = sampling_interval
        self.running = False
        self.monitor_thread = None
        self.system_metrics_history: List[SystemMetrics] = []
        self.process_metrics_history: Dict[int, List[ProcessMetrics]] = {}
        self.callbacks: List = []
        self.max_history = 300
        self.logger = self._setup_logger()
    
    def _setup_logger(self):
        logger = logging.getLogger('SystemMonitor')
        logger.handlers.clear()
        handler = logging.FileHandler('system_monitor.log')
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        return logger
    
    def start(self):
        """Start monitoring"""
        if self.running:
            return
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        self.logger.info("System monitor started")
    
    def stop(self):
        """Stop monitoring"""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2)
        self.logger.info("System monitor stopped")
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.running:
            try:
                metrics = self._collect_system_metrics()
                self.system_metrics_history.append(metrics)
                
                if len(self.system_metrics_history) > self.max_history:
                    self.system_metrics_history.pop(0)
                
                for callback in self.callbacks:
                    try:
                        callback(metrics)
                    except Exception as e:
                        self.logger.error(f"Callback error: {e}")
                
                time.sleep(self.sampling_interval)
            except Exception as e:
                self.logger.error(f"Monitor error: {e}")
    
    def _collect_system_metrics(self) -> SystemMetrics:
        """Collect system metrics"""
        vm = psutil.virtual_memory()
        return SystemMetrics(
            timestamp=datetime.now(),
            cpu_percent=psutil.cpu_percent(interval=0.1),
            cpu_count=psutil.cpu_count(),
            memory_percent=vm.percent,
            memory_used_mb=vm.used / (1024**2),
            memory_total_mb=vm.total / (1024**2),
            memory_available_mb=vm.available / (1024**2),
            process_count=len(psutil.pids())
        )
    
    def get_latest_system_metrics(self) -> Optional[SystemMetrics]:
        """Get latest metrics"""
        return self.system_metrics_history[-1] if self.system_metrics_history else None
    
    def register_callback(self, callback):
        """Register callback"""
        self.callbacks.append(callback)

# ============================================================================
# RESOURCE MANAGER
# ============================================================================

class ResourceManager:
    """Dynamic resource allocation management"""
    
    def __init__(self):
        self.tracked_processes: Dict = {}
        self.strategy = ResourceAllocationStrategy.PERFORMANCE
        self.available_cores = psutil.cpu_count()
        self.logger = self._setup_logger()
    
    def _setup_logger(self):
        logger = logging.getLogger('ResourceManager')
        logger.handlers.clear()
        handler = logging.FileHandler('resource_manager.log')
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        return logger
    
    def register_process(self, pid: int, name: str, priority: ProcessPriority) -> bool:
        """Register a process"""
        try:
            psutil.Process(pid)
            self.tracked_processes[pid] = {
                'name': name,
                'priority': priority,
                'allocations': {'cpu_quota': 0, 'memory_limit_mb': 0}
            }
            self.logger.info(f"Process registered: {name} (PID: {pid})")
            return True
        except psutil.NoSuchProcess:
            return False
        except Exception as e:
            self.logger.error(f"Error registering process: {e}")
            return False
    
    def unregister_process(self, pid: int) -> bool:
        """Unregister a process"""
        if pid in self.tracked_processes:
            del self.tracked_processes[pid]
            self.logger.info(f"Process unregistered (PID: {pid})")
            return True
        return False
    
    def set_process_priority(self, pid: int, priority: ProcessPriority) -> bool:
        """Set process priority"""
        if pid in self.tracked_processes:
            self.tracked_processes[pid]['priority'] = priority
            self.logger.info(f"Priority updated for PID {pid}")
            return True
        return False
    
    def set_allocation_strategy(self, strategy: ResourceAllocationStrategy):
        """Set allocation strategy"""
        self.strategy = strategy
        self.logger.info(f"Strategy changed to {strategy.value}")
    
    def get_all_allocations(self) -> Dict:
        """Get all allocations"""
        return self.tracked_processes
    
    def get_allocation(self, pid: int):
        """Get specific allocation"""
        return self.tracked_processes.get(pid)

# ============================================================================
# PERFORMANCE OPTIMIZER
# ============================================================================

class PerformanceOptimizer:
    """Performance monitoring and optimization"""
    
    def __init__(self, monitor: SystemMonitor, manager: ResourceManager):
        self.monitor = monitor
        self.manager = manager
        self.running = False
        self.optimizer_thread = None
        self.optimization_interval = 5.0
        self.logger = self._setup_logger()
    
    def _setup_logger(self):
        logger = logging.getLogger('PerformanceOptimizer')
        logger.handlers.clear()
        handler = logging.FileHandler('performance_optimizer.log')
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        return logger
    
    def start(self):
        """Start optimizer"""
        if self.running:
            return
        self.running = True
        self.optimizer_thread = threading.Thread(target=self._optimize_loop, daemon=True)
        self.optimizer_thread.start()
        self.logger.info("Optimizer started")
    
    def stop(self):
        """Stop optimizer"""
        self.running = False
        if self.optimizer_thread:
            self.optimizer_thread.join(timeout=2)
        self.logger.info("Optimizer stopped")
    
    def _optimize_loop(self):
        """Main optimization loop"""
        while self.running:
            try:
                metrics = self.monitor.get_latest_system_metrics()
                if metrics:
                    self._optimize_allocations(metrics)
                time.sleep(self.optimization_interval)
            except Exception as e:
                self.logger.error(f"Optimization error: {e}")
    
    def _optimize_allocations(self, metrics: SystemMetrics):
        """Optimize resource allocations with adaptive control"""
        # Detect high utilization and apply adaptive controls
        if metrics.cpu_percent > 85:
            self.logger.warning(f"HIGH CPU: {metrics.cpu_percent}% - Applying adaptive control")
            self._apply_adaptive_resource_control(metrics, 'cpu')
        
        if metrics.memory_percent > 90:
            self.logger.warning(f"HIGH MEMORY: {metrics.memory_percent}% - Applying adaptive control")
            self._apply_adaptive_resource_control(metrics, 'memory')
        
        # Log warnings for elevated usage
        if metrics.cpu_percent > 80:
            self.logger.info(f"Elevated CPU usage: {metrics.cpu_percent}%")
        if metrics.memory_percent > 85:
            self.logger.info(f"Elevated memory usage: {metrics.memory_percent}%")
    
    def _apply_adaptive_resource_control(self, metrics: SystemMetrics, resource_type: str):
        """Apply adaptive resource control by suspending/limiting non-critical processes"""
        try:
            tracked = self.manager.get_all_allocations()
            
            if not tracked:
                return
            
            # Sort processes by priority
            sorted_procs = sorted(
                tracked.items(),
                key=lambda x: x[1]['priority'].value,
                reverse=True
            )
            
            # Suspend lower priority processes if needed
            for pid, proc_info in sorted_procs:
                priority = proc_info['priority']
                
                # Skip critical and high priority processes
                if priority.value >= ProcessPriority.NORMAL.value:
                    continue
                
                try:
                    process = psutil.Process(pid)
                    # Suspend low/background processes under high load
                    if priority in [ProcessPriority.LOW, ProcessPriority.BACKGROUND]:
                        if process.status() != psutil.STATUS_STOPPED:
                            process.suspend()
                            self.logger.info(f"Suspended process {pid} ({proc_info['name']}) - Resource: {resource_type}")
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
        except Exception as e:
            self.logger.error(f"Error in adaptive resource control: {e}")
    
    def get_optimization_report(self) -> Dict:
        """Get optimization report"""
        tracked = self.manager.get_all_allocations()
        
        recommendations = []
        metrics = self.monitor.get_latest_system_metrics()
        
        if metrics:
            if metrics.cpu_percent > 80:
                recommendations.append("High CPU: Consider reducing process count or increasing priorities")
            if metrics.memory_percent > 85:
                recommendations.append("High Memory: Close unnecessary applications")
            if metrics.process_count > 300:
                recommendations.append("Many processes running: May impact system performance")
        
        return {
            'tracked_processes': len(tracked),
            'status': 'active' if self.running else 'inactive',
            'optimization_recommendations': recommendations
        }

# ============================================================================
# WORKLOAD SIMULATOR (For Testing & Stress Testing)
# ============================================================================

class WorkloadSimulator:
    """Simulate various workloads for testing resource allocation"""
    
    def __init__(self):
        self.active_threads = []
        self.stop_event = threading.Event()
        self.logger = self._setup_logger()
    
    def _setup_logger(self):
        logger = logging.getLogger('WorkloadSimulator')
        logger.handlers.clear()
        handler = logging.FileHandler('workload_simulator.log')
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        return logger
    
    def start_cpu_workload(self, intensity: int = 50, duration: int = 60) -> str:
        """Start CPU stress test
        
        Args:
            intensity: 0-100 (percentage of CPU to stress)
            duration: How many seconds to run
        """
        try:
            intensity = max(0, min(100, intensity))  # Clamp 0-100
            num_threads = max(1, (intensity // 25) + 1)
            
            def cpu_stress():
                end_time = time.time() + duration
                while time.time() < end_time and not self.stop_event.is_set():
                    # CPU-intensive calculation
                    result = sum([i * i for i in range(100000)])
            
            threads = []
            for i in range(num_threads):
                t = threading.Thread(target=cpu_stress, daemon=True)
                t.start()
                threads.append(t)
                self.active_threads.append(t)
            
            self.logger.info(f"CPU workload started: {intensity}% intensity for {duration}s")
            return f"✅ CPU workload started: {intensity}% intensity, {duration} seconds"
        except Exception as e:
            self.logger.error(f"Error starting CPU workload: {e}")
            return f"❌ Error: {str(e)}"
    
    def start_memory_workload(self, size_mb: int = 100, duration: int = 60) -> str:
        """Start memory stress test
        
        Args:
            size_mb: Amount of memory to allocate (MB)
            duration: How many seconds to hold
        """
        try:
            size_mb = max(1, min(1000, size_mb))  # Clamp 1-1000 MB
            
            def memory_stress():
                try:
                    # Allocate memory
                    data = bytearray(size_mb * 1024 * 1024)
                    # Keep it allocated
                    time.sleep(duration)
                    del data
                except Exception as e:
                    self.logger.error(f"Memory allocation error: {e}")
            
            t = threading.Thread(target=memory_stress, daemon=True)
            t.start()
            self.active_threads.append(t)
            
            self.logger.info(f"Memory workload started: {size_mb}MB for {duration}s")
            return f"✅ Memory workload started: {size_mb}MB for {duration}s"
        except Exception as e:
            self.logger.error(f"Error starting memory workload: {e}")
            return f"❌ Error: {str(e)}"
    
    def start_io_workload(self, num_files: int = 10, duration: int = 30) -> str:
        """Start I/O stress test
        
        Args:
            num_files: Number of files to create and write to
            duration: How many seconds to run
        """
        try:
            import tempfile
            
            def io_stress():
                end_time = time.time() + duration
                temp_dir = tempfile.gettempdir()
                
                while time.time() < end_time and not self.stop_event.is_set():
                    for i in range(num_files):
                        try:
                            filepath = os.path.join(temp_dir, f"test_io_{i}.tmp")
                            with open(filepath, 'w') as f:
                                f.write("X" * 10000)
                        except:
                            pass
            
            t = threading.Thread(target=io_stress, daemon=True)
            t.start()
            self.active_threads.append(t)
            
            self.logger.info(f"I/O workload started: {num_files} files for {duration}s")
            return f"✅ I/O workload started: {num_files} files for {duration}s"
        except Exception as e:
            self.logger.error(f"Error starting I/O workload: {e}")
            return f"❌ Error: {str(e)}"
    
    def get_status(self) -> str:
        """Get workload status"""
        active = len([t for t in self.active_threads if t.is_alive()])
        return f"Active workload threads: {active}"
    
    def stop_all(self) -> str:
        """Stop all workloads"""
        try:
            self.stop_event.set()
            
            for t in self.active_threads:
                if t.is_alive():
                    t.join(timeout=2)
            
            self.active_threads = []
            self.stop_event.clear()
            
            self.logger.info("All workloads stopped")
            return "✅ All workloads stopped"
        except Exception as e:
            self.logger.error(f"Error stopping workloads: {e}")
            return f"❌ Error: {str(e)}"

# Global workload simulator instance
simulator = WorkloadSimulator()

# ============================================================================
# DYNAMIC RESOURCE ALLOCATOR
# ============================================================================

class DynamicResourceAllocator:
    """Main system orchestrator"""
    
    def __init__(self):
        self.monitor = SystemMonitor(sampling_interval=1.0)
        self.manager = ResourceManager()
        self.optimizer = PerformanceOptimizer(self.monitor, self.manager)
        self.running = False
        self.start_time = None
        self.logger = self._setup_logger()
    
    def _setup_logger(self):
        logger = logging.getLogger('DynamicResourceAllocator')
        logger.handlers.clear()
        handler = logging.FileHandler('resource_allocator.log')
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        console = logging.StreamHandler()
        console.setFormatter(formatter)
        logger.addHandler(console)
        logger.setLevel(logging.INFO)
        return logger
    
    def start(self) -> bool:
        """Start system"""
        if self.running:
            return False
        try:
            self.logger.info("=" * 60)
            self.logger.info("Starting Dynamic Resource Allocator")
            self.logger.info("=" * 60)
            
            self.monitor.start()
            self.optimizer.start()
            self.running = True
            self.start_time = datetime.now()
            
            self.logger.info("All components started successfully")
            self.logger.info(f"CPU Cores Available: {self.manager.available_cores}")
            self.logger.info(f"Allocation Strategy: {self.manager.strategy.value}")
            
            return True
        except Exception as e:
            self.logger.error(f"Failed to start: {e}")
            self.running = False
            return False
    
    def stop(self) -> bool:
        """Stop system"""
        if not self.running:
            return False
        try:
            self.logger.info("Stopping system...")
            self.monitor.stop()
            self.optimizer.stop()
            self.running = False
            uptime = (datetime.now() - self.start_time).total_seconds()
            self.logger.info(f"System stopped. Uptime: {uptime:.1f} seconds")
            self.logger.info("=" * 60)
            return True
        except Exception as e:
            self.logger.error(f"Error stopping: {e}")
            return False
    
    def register_program(self, pid: int, name: str, priority: ProcessPriority) -> bool:
        """Register program"""
        return self.manager.register_process(pid, name, priority)
    
    def unregister_program(self, pid: int) -> bool:
        """Unregister program"""
        return self.manager.unregister_process(pid)
    
    def set_program_priority(self, pid: int, priority: ProcessPriority) -> bool:
        """Set program priority"""
        return self.manager.set_process_priority(pid, priority)
    
    def set_allocation_strategy(self, strategy: ResourceAllocationStrategy):
        """Set allocation strategy"""
        self.manager.set_allocation_strategy(strategy)
    
    def get_system_status(self) -> Dict:
        """Get system status"""
        metrics = self.monitor.get_latest_system_metrics()
        
        status = {
            'running': self.running,
            'uptime_seconds': (datetime.now() - self.start_time).total_seconds() if self.start_time else 0,
            'allocation_strategy': self.manager.strategy.value,
        }
        
        if not metrics:
            status['error'] = 'No metrics available'
            return status
        
        status['system_metrics'] = {
            'timestamp': metrics.timestamp.isoformat(),
            'cpu_percent': metrics.cpu_percent,
            'cpu_count': metrics.cpu_count,
            'memory_percent': metrics.memory_percent,
            'memory_used_mb': metrics.memory_used_mb,
            'memory_total_mb': metrics.memory_total_mb,
            'memory_available_mb': metrics.memory_available_mb,
            'process_count': metrics.process_count,
        }
        status['tracked_programs'] = len(self.manager.tracked_processes)
        
        return status
    
    def get_performance_report(self) -> Dict:
        """Get performance report"""
        metrics = self.monitor.get_latest_system_metrics()
        
        report = {
            'summary': {
                'status': 'active' if self.running else 'inactive',
                'uptime_seconds': (datetime.now() - self.start_time).total_seconds() if self.start_time else 0,
                'tracked_processes': len(self.manager.tracked_processes),
            },
            'metrics_history': [asdict(m) for m in self.monitor.system_metrics_history[-5:]],
            'optimization_recommendations': [
                'Monitor CPU usage for optimal performance',
                'Check memory allocation for tracked processes',
            ]
        }
        
        return report

# ============================================================================
# UNIFIED FRONTEND + BACKEND APPLICATION
# ============================================================================

class UnifiedResourceAllocatorApp:
    """Complete All-in-One Application"""
    
    def __init__(self):
        self.allocator = DynamicResourceAllocator()
        self.logger = self._setup_logger()
    
    def _setup_logger(self):
        logger = logging.getLogger('UnifiedApp')
        logger.handlers.clear()
        handler = logging.FileHandler('unified_app.log')
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        return logger
    
    def start_system(self) -> str:
        """Start system"""
        if self.allocator.running:
            return "⚠️ System already running!"
        
        success = self.allocator.start()
        return "✅ System started successfully!" if success else "❌ Failed to start system"
    
    def stop_system(self) -> str:
        """Stop system"""
        if not self.allocator.running:
            return "⚠️ System not running!"
        
        success = self.allocator.stop()
        return "✅ System stopped successfully!" if success else "❌ Failed to stop"
    
    def get_status(self) -> str:
        """Get system status"""
        try:
            status = self.allocator.get_system_status()
            
            text = "📊 SYSTEM STATUS\n"
            text += "=" * 50 + "\n"
            text += f"✅ Running: {status['running']}\n"
            text += f"⏱️ Uptime: {status['uptime_seconds']:.1f}s\n"
            text += f"🎯 Strategy: {status['allocation_strategy']}\n"
            text += f"📋 Tracked Programs: {status.get('tracked_programs', 0)}\n"
            
            if 'system_metrics' in status:
                m = status['system_metrics']
                text += f"\n📈 METRICS\n"
                text += f"CPU: {m['cpu_percent']:.1f}% ({m['cpu_count']} cores)\n"
                text += f"Memory: {m['memory_percent']:.1f}%\n"
                text += f"Processes: {m['process_count']}\n"
            
            return text
        except Exception as e:
            return f"❌ Error: {str(e)}"
    
    def register_program(self, pid: int, name: str, priority: str) -> str:
        """Register program"""
        if not self.allocator.running:
            return "❌ System not running! Start first."
        
        try:
            pid = int(pid) if pid else None
        except (ValueError, TypeError):
            return "❌ Invalid PID format"
        
        if not pid or pid <= 0:
            return "❌ Enter valid PID (positive number)"
        
        if not name or name.strip() == "":
            name = f"Program_{pid}"
        
        try:
            priority_enum = ProcessPriority[priority.upper().replace(" ", "_")]
        except KeyError:
            return f"❌ Invalid priority: {priority}"
        
        try:
            psutil.Process(pid)
            success = self.allocator.register_program(pid, name, priority_enum)
            if success:
                return f"✅ Registered: {name} (PID: {pid})"
            else:
                return "❌ Already registered or error"
        except psutil.NoSuchProcess:
            return f"❌ Process PID {pid} not found"
        except Exception as e:
            return f"❌ Error: {str(e)}"
    
    def unregister_program(self, pid: int) -> str:
        """Unregister program"""
        try:
            pid = int(pid) if pid else None
        except (ValueError, TypeError):
            return "❌ Invalid PID format"
        
        if not pid or pid <= 0:
            return "❌ Enter valid PID"
        
        try:
            success = self.allocator.unregister_program(pid)
            return f"✅ Unregistered PID {pid}" if success else f"❌ PID {pid} not found"
        except Exception as e:
            return f"❌ Error: {str(e)}"
    
    def set_priority(self, pid: int, priority: str) -> str:
        """Set program priority"""
        try:
            pid = int(pid) if pid else None
        except (ValueError, TypeError):
            return "❌ Invalid PID format"
        
        if not pid or pid <= 0:
            return "❌ Enter valid PID"
        
        try:
            priority_enum = ProcessPriority[priority.upper().replace(" ", "_")]
            success = self.allocator.set_program_priority(pid, priority_enum)
            return f"✅ Priority set to {priority}" if success else "❌ PID not found"
        except KeyError:
            return f"❌ Invalid priority: {priority}"
        except Exception as e:
            return f"❌ Error: {str(e)}"
    
    def change_strategy(self, strategy: str) -> str:
        """Change allocation strategy"""
        if not self.allocator.running:
            return "❌ System not running!"
        
        try:
            strategy_enum = ResourceAllocationStrategy[strategy.upper().replace(" ", "_")]
            self.allocator.set_allocation_strategy(strategy_enum)
            return f"✅ Strategy changed to {strategy}"
        except KeyError:
            return f"❌ Invalid strategy"
        except Exception as e:
            return f"❌ Error: {str(e)}"
    
    def get_tracked(self) -> str:
        """Get tracked programs with system summary"""
        tracked = self.allocator.manager.get_all_allocations()
        metrics = self.allocator.monitor.get_latest_system_metrics()
        
        text = "📋 TRACKED PROGRAMS & SYSTEM STATUS\n"
        text += "=" * 60 + "\n\n"
        
        # System metrics always shown
        if metrics:
            text += "📊 CURRENT SYSTEM METRICS\n"
            text += f"  CPU Usage: {metrics.cpu_percent}% ({metrics.cpu_count} cores)\n"
            text += f"  Memory: {metrics.memory_percent}% ({metrics.memory_used_mb:.0f}/{metrics.memory_total_mb:.0f} MB)\n"
            text += f"  Available RAM: {metrics.memory_available_mb:.0f} MB\n"
            text += f"  Total Processes: {metrics.process_count}\n"
            text += "\n"
        
        # Tracked programs section
        text += f"🎯 TRACKED PROGRAMS: {len(tracked)}\n"
        text += "-" * 60 + "\n"
        
        if tracked:
            for pid, info in tracked.items():
                try:
                    proc = psutil.Process(pid)
                    proc_cpu = proc.cpu_percent(interval=0.1)
                    proc_mem = proc.memory_percent()
                    text += f"\n  PID: {pid}\n"
                    text += f"    Name: {info['name']}\n"
                    text += f"    Priority: {info['priority'].name}\n"
                    text += f"    CPU: {proc_cpu}% | Memory: {proc_mem}%\n"
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    text += f"\n  PID: {pid} (process ended or inaccessible)\n"
                    text += f"    Name: {info['name']}\n"
                    text += f"    Priority: {info['priority'].name}\n"
        else:
            text += "  ⚠️  No processes tracked yet.\n"
            text += "  👉 Use Programs tab to register processes\n"
        
        text += "\n" + "-" * 60 + "\n"
        text += f"🎮 System Status: {'🟢 RUNNING' if self.allocator.running else '🔴 STOPPED'}\n"
        text += f"📈 Strategy: {self.allocator.manager.strategy.value}\n"
        
        return text
    
    def get_report(self) -> str:
        """Get comprehensive performance report"""
        try:
            # Get all data sources
            tracked = self.allocator.manager.get_all_allocations()
            metrics = self.allocator.monitor.get_latest_system_metrics()
            
            text = "📈 COMPREHENSIVE PERFORMANCE REPORT\n"
            text += "=" * 70 + "\n\n"
            
            # System Status Section
            text += "🖥️  SYSTEM STATUS\n"
            text += "-" * 70 + "\n"
            sys_status = 'ACTIVE 🟢' if self.allocator.running else 'INACTIVE 🔴'
            text += f"Status: {sys_status}\n"
            text += f"Strategy: {self.allocator.manager.strategy.value.upper()}\n"
            
            if self.allocator.start_time:
                uptime = (datetime.now() - self.allocator.start_time).total_seconds()
                minutes = int(uptime) // 60
                seconds = int(uptime) % 60
                text += f"Uptime: {minutes}m {seconds}s\n"
            
            text += "\n"
            
            # System Metrics Section
            if metrics:
                text += "📊 REAL-TIME METRICS\n"
                text += "-" * 70 + "\n"
                text += f"CPU Usage: {metrics.cpu_percent}% (Cores: {metrics.cpu_count})\n"
                text += f"Memory: {metrics.memory_percent}% ({metrics.memory_used_mb:.0f}MB used / {metrics.memory_total_mb:.0f}MB total)\n"
                text += f"Available RAM: {metrics.memory_available_mb:.0f}MB\n"
                text += f"Total Processes: {metrics.process_count}\n"
                text += "\n"
            
            # Tracked Processes Section
            text += "📋 TRACKED PROCESSES\n"
            text += "-" * 70 + "\n"
            text += f"Monitored: {len(tracked)} processes\n"
            
            if tracked:
                for pid, info in tracked.items():
                    try:
                        proc = psutil.Process(pid)
                        status = "🟢" if proc.is_running() else "🔴"
                        cpu = proc.cpu_percent(interval=0.1)
                        mem = proc.memory_percent()
                        text += f"  {status} {info['name']} (PID: {pid}) | Priority: {info['priority'].name} | CPU: {cpu}% | Mem: {mem}%\n"
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        text += f"  🔴 {info['name']} (PID: {pid}) [Not accessible]\n"
            else:
                text += "  (No processes being tracked)\n"
            
            text += "\n"
            
            # Recommendations Section
            text += "💡 SMART RECOMMENDATIONS\n"
            text += "-" * 70 + "\n"
            
            recommendations = []
            
            if metrics:
                if metrics.cpu_percent > 80:
                    recommendations.append(f"⚠️  HIGH CPU ({metrics.cpu_percent}%) - Consider reducing workload or prioritizing critical tasks")
                if metrics.memory_percent > 85:
                    recommendations.append(f"⚠️  HIGH MEMORY ({metrics.memory_percent}%) - Close unnecessary applications")
                if metrics.process_count > 400:
                    recommendations.append(f"⚠️  MANY PROCESSES ({metrics.process_count}) - System getting crowded, may impact performance")
                
                if not recommendations:
                    recommendations.append("✅ System running optimally - All metrics within normal range")
            
            if not tracked and self.allocator.running:
                recommendations.append("💡 TIP: Register important processes to monitor resource allocation")
            
            if tracked:
                low_priority_count = sum(1 for info in tracked.values() if info['priority'].value <= 2)
                if low_priority_count > 0 and metrics and metrics.cpu_percent > 70:
                    recommendations.append(f"💡 {low_priority_count} low-priority process(es) can be suspended if needed")
            
            for rec in recommendations:
                text += f"  {rec}\n"
            
            text += "\n" + "=" * 70 + "\n"
            text += "Updated: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "\n"
            
            return text
        except Exception as e:
            self.logger.error(f"Report generation error: {e}")
            return f"❌ Error generating report: {str(e)}\n\nSystem Status: {'Running' if self.allocator.running else 'Stopped'}"
    
    # ========== WORKLOAD TESTING METHODS ==========
    def simulation_cpu(self, intensity: int) -> str:
        """Start CPU workload simulation"""
        if not self.allocator.running:
            return "❌ System not running! Start first."
        intensity = max(0, min(100, int(intensity)))
        result = simulator.start_cpu_workload(intensity, duration=30)
        return result
    
    def simulation_memory(self, size: int) -> str:
        """Start memory workload simulation"""
        if not self.allocator.running:
            return "❌ System not running! Start first."
        size = max(1, min(500, int(size)))
        result = simulator.start_memory_workload(size, duration=30)
        return result
    
    def simulation_io(self, files: int) -> str:
        """Start I/O workload simulation"""
        if not self.allocator.running:
            return "❌ System not running! Start first."
        files = max(1, min(50, int(files)))
        result = simulator.start_io_workload(files, duration=30)
        return result
    
    def simulation_status(self) -> str:
        """Get workload simulation status"""
        return simulator.get_status()
    
    def simulation_stop(self) -> str:
        """Stop all workload simulations"""
        return simulator.stop_all()
    
    def get_available_pids(self) -> Dict[int, str]:
        """Get all available PIDs on the system"""
        pids = {}
        try:
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    pids[proc.info['pid']] = proc.info['name']
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
        except Exception as e:
            self.logger.error(f"Error getting available PIDs: {e}")
        return pids
    
    def show_available_pids(self) -> str:
        """Display available PIDs formatted for UI"""
        pids = self.get_available_pids()
        
        if not pids:
            return "❌ No processes found"
        
        text = "📋 AVAILABLE PROCESSES\n"
        text += "=" * 50 + "\n"
        text += "(Current PID: " + str(os.getpid()) + ")\n\n"
        
        # Sort by PID and show most relevant ones
        sorted_pids = sorted(pids.items())
        
        # Group by process type
        python_procs = [(pid, name) for pid, name in sorted_pids if 'python' in name.lower()]
        user_procs = [(pid, name) for pid, name in sorted_pids if any(x in name.lower() for x in ['code', 'notepad', 'explorer', 'chrome', 'firefox', 'cmd', 'powershell'])]
        
        if python_procs:
            text += "🐍 PYTHON PROCESSES\n"
            for pid, name in python_procs:
                text += f"  PID: {pid:6d} - {name}\n"
            text += "\n"
        
        if user_procs:
            text += "👤 USER APPLICATIONS\n"
            for pid, name in user_procs[:15]:
                text += f"  PID: {pid:6d} - {name}\n"
            text += "\n"
        
        text += f"📊 Total Processes: {len(pids)}\n"
        text += "\n💡 Copy a PID from above and paste in Register field"
        
        return text

# ============================================================================
# CREATE APPLICATION INSTANCE AND GRADIO INTERFACE
# ============================================================================

app = UnifiedResourceAllocatorApp()

def create_interface():
    """Create Gradio interface"""
    with gr.Blocks(title="Dynamic Resource Allocator") as interface:
        gr.Markdown("# 🖥️ Dynamic Resource Allocator (ALL-IN-ONE)")
        
        with gr.Tabs():
            # Control Panel
            with gr.Tab("🎮 Control"):
                with gr.Row():
                    with gr.Column():
                        gr.Markdown("### System Control")
                        start_btn = gr.Button("▶️ Start", size="lg", variant="primary")
                        stop_btn = gr.Button("⏹️ Stop", size="lg", variant="stop")
                        status_out = gr.Textbox(label="Status", lines=3, interactive=False)
                    
                    with gr.Column():
                        gr.Markdown("### Strategy")
                        strategy = gr.Dropdown(["equal", "priority", "performance", "demand"], value="performance", label="Strategy")
                        apply_btn = gr.Button("Apply", size="lg", variant="primary")
                        strategy_out = gr.Textbox(label="Result", lines=3, interactive=False)
                
                start_btn.click(app.start_system, outputs=status_out)
                stop_btn.click(app.stop_system, outputs=status_out)
                apply_btn.click(app.change_strategy, inputs=strategy, outputs=strategy_out)
            
            # Monitor
            with gr.Tab("📊 Monitor"):
                refresh_btn = gr.Button("🔄 Refresh", size="lg", variant="primary")
                status_display = gr.Textbox(label="System Status", lines=15, interactive=False)
                refresh_btn.click(app.get_status, outputs=status_display)
            
            # Program Management
            with gr.Tab("📋 Programs"):
                # Available PIDs section
                with gr.Row():
                    with gr.Column():
                        pid_list_btn = gr.Button("🔍 Show Available PIDs", size="lg", variant="secondary")
                        pid_list_display = gr.Textbox(label="Available Processes", lines=20, interactive=False)
                        pid_list_btn.click(app.show_available_pids, outputs=pid_list_display)
                
                gr.Markdown("---")
                
                with gr.Row():
                    with gr.Column():
                        gr.Markdown("### Register")
                        pid_in = gr.Number(label="PID", precision=0)
                        name_in = gr.Textbox(label="Name")
                        priority_in = gr.Dropdown(["critical", "high", "normal", "low", "background"], value="normal", label="Priority")
                        reg_btn = gr.Button("Register", size="lg", variant="primary")
                        reg_out = gr.Textbox(label="Result", lines=2, interactive=False)
                    
                    with gr.Column():
                        gr.Markdown("### Management")
                        update_pid = gr.Number(label="PID", precision=0)
                        new_priority = gr.Dropdown(["critical", "high", "normal", "low", "background"], value="normal", label="Priority")
                        priority_btn = gr.Button("Update", size="lg", variant="primary")
                        priority_out = gr.Textbox(label="Result", lines=2, interactive=False)
                        
                        gr.Markdown("### Unregister")
                        unreg_pid = gr.Number(label="PID", precision=0)
                        unreg_btn = gr.Button("Unregister", size="lg", variant="stop")
                        unreg_out = gr.Textbox(label="Result", lines=2, interactive=False)
                
                reg_btn.click(app.register_program, inputs=[pid_in, name_in, priority_in], outputs=reg_out)
                priority_btn.click(app.set_priority, inputs=[update_pid, new_priority], outputs=priority_out)
                unreg_btn.click(app.unregister_program, inputs=unreg_pid, outputs=unreg_out)
            
            # Tracked
            with gr.Tab("🎯 Tracked"):
                with gr.Row():
                    with gr.Column():
                        track_btn = gr.Button("🔄 Auto-Refresh", size="lg", variant="primary")
                        refresh_rate = gr.Slider(1, 10, value=2, step=1, label="Refresh every N seconds")
                with gr.Row():
                    track_display = gr.Textbox(label="Tracked Programs & System Status", lines=25, interactive=False)
                
                # Auto-refresh logic
                def auto_refresh_tracked():
                    return app.get_tracked()
                
                track_btn.click(auto_refresh_tracked, outputs=track_display)
                # Trigger initial load
                with gr.Tab("🎯 Tracked"):
                    gr.on(
                        triggers=[track_btn.click],
                        fn=auto_refresh_tracked,
                        outputs=[track_display]
                    )
            
            # Reports
            with gr.Tab("📈 Reports"):
                with gr.Row():
                    with gr.Column(scale=1):
                        report_btn = gr.Button("📊 Full Report", size="lg", variant="primary")
                    with gr.Column(scale=3):
                        gr.Markdown("_Live system analysis with recommendations_")
                
                with gr.Row():
                    report_display = gr.Textbox(label="Performance Analysis", lines=30, interactive=False)
                
                # Auto-refresh logic
                def auto_refresh_report():
                    return app.get_report()
                
                report_btn.click(auto_refresh_report, outputs=report_display)
            
            # Workload Testing
            with gr.Tab("⚡ Workload Test"):
                gr.Markdown("### System Stress Testing")
                
                with gr.Row():
                    with gr.Column():
                        gr.Markdown("#### CPU Stress")
                        cpu_intensity = gr.Slider(0, 100, value=50, step=10, label="Intensity (%)")
                        cpu_btn = gr.Button("Start CPU Load", size="lg", variant="secondary")
                        cpu_out = gr.Textbox(label="Status", lines=2, interactive=False)
                        cpu_btn.click(app.simulation_cpu, inputs=cpu_intensity, outputs=cpu_out)
                    
                    with gr.Column():
                        gr.Markdown("#### Memory Stress")
                        mem_size = gr.Slider(1, 500, value=100, step=50, label="Size (MB)")
                        mem_btn = gr.Button("Start Memory Load", size="lg", variant="secondary")
                        mem_out = gr.Textbox(label="Status", lines=2, interactive=False)
                        mem_btn.click(app.simulation_memory, inputs=mem_size, outputs=mem_out)
                    
                    with gr.Column():
                        gr.Markdown("#### I/O Stress")
                        io_files = gr.Slider(1, 50, value=10, step=5, label="Files")
                        io_btn = gr.Button("Start I/O Load", size="lg", variant="secondary")
                        io_out = gr.Textbox(label="Status", lines=2, interactive=False)
                        io_btn.click(app.simulation_io, inputs=io_files, outputs=io_out)
                
                gr.Markdown("---")
                
                with gr.Row():
                    status_btn = gr.Button("📊 Workload Status", size="lg", variant="primary")
                    stop_btn = gr.Button("⛔ Stop All", size="lg", variant="stop")
                    status_out = gr.Textbox(label="Output", lines=3, interactive=False)
                
                status_btn.click(app.simulation_status, outputs=status_out)
                stop_btn.click(app.simulation_stop, outputs=status_out)
    
    return interface

# ============================================================================
# MAIN APPLICATION
# ============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("🖥️ COMPLETE DYNAMIC RESOURCE ALLOCATOR - ALL-IN-ONE")
    print("=" * 80)
    print("\n✅ Backend Components:")
    print("   • System Monitor (Real-time metrics)")
    print("   • Resource Manager (Dynamic allocation)")
    print("   • Performance Optimizer (Optimization)")
    print("\n✅ Frontend Components:")
    print("   • Gradio Web Interface")
    print("   • Program Registration")
    print("   • System Monitoring")
    print("   • Performance Reports")
    print("\n🌐 Launching on: http://localhost:7860")
    print("=" * 80 + "\n")
    
    interface = create_interface()
    interface.launch(
        server_name="0.0.0.0",
        server_port=7860,
        debug=False
    )
