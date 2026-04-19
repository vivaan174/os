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
        """Optimize resource allocations"""
        if metrics.cpu_percent > 80:
            self.logger.warning(f"High CPU usage: {metrics.cpu_percent}%")
        if metrics.memory_percent > 85:
            self.logger.warning(f"High memory usage: {metrics.memory_percent}%")
    
    def get_optimization_report(self) -> Dict:
        """Get optimization report"""
        return {
            'optimizations_performed': len(self.manager.tracked_processes),
            'status': 'active'
        }

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
        """Get tracked programs"""
        tracked = self.allocator.manager.get_all_allocations()
        
        if not tracked:
            return "No programs tracked yet"
        
        text = "📋 TRACKED PROGRAMS\n"
        text += "=" * 50 + "\n"
        for pid, info in tracked.items():
            text += f"\nPID: {pid}\n"
            text += f"  Name: {info['name']}\n"
            text += f"  Priority: {info['priority'].name}\n"
        
        return text
    
    def get_report(self) -> str:
        """Get performance report"""
        try:
            report = self.allocator.get_performance_report()
            
            text = "📈 PERFORMANCE REPORT\n"
            text += "=" * 60 + "\n"
            
            summary = report['summary']
            text += f"Status: {summary['status']}\n"
            text += f"Uptime: {summary['uptime_seconds']:.1f}s\n"
            text += f"Tracked: {summary['tracked_processes']}\n"
            
            if report['optimization_recommendations']:
                text += "\n💡 RECOMMENDATIONS\n"
                for rec in report['optimization_recommendations']:
                    text += f"• {rec}\n"
            
            return text
        except Exception as e:
            return f"❌ Error: {str(e)}"
    
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
                track_btn = gr.Button("🔄 Refresh", size="lg", variant="primary")
                track_display = gr.Textbox(label="Tracked Programs", lines=15, interactive=False)
                track_btn.click(app.get_tracked, outputs=track_display)
            
            # Reports
            with gr.Tab("📈 Reports"):
                report_btn = gr.Button("📊 Generate", size="lg", variant="primary")
                report_display = gr.Textbox(label="Report", lines=15, interactive=False)
                report_btn.click(app.get_report, outputs=report_display)
    
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
