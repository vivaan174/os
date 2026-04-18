"""
System Monitor Module
Provides real-time monitoring of CPU and memory usage for the system and individual processes
"""

import psutil
import threading
import time
from dataclasses import dataclass
from typing import Dict, List, Optional
from datetime import datetime
import json


@dataclass
class ProcessMetrics:
    """Holds performance metrics for a single process"""
    pid: int
    name: str
    cpu_percent: float
    memory_mb: float
    memory_percent: float
    num_threads: int
    status: str
    create_time: float
    priority: int


@dataclass
class SystemMetrics:
    """Holds overall system performance metrics"""
    timestamp: datetime
    cpu_percent: float
    cpu_count: int
    memory_total_mb: float
    memory_used_mb: float
    memory_percent: float
    memory_available_mb: float
    swap_used_mb: float
    swap_percent: float
    disk_usage_percent: Dict[str, float]
    process_count: int


class SystemMonitor:
    """Monitors system and process performance metrics"""
    
    def __init__(self, sampling_interval: float = 1.0):
        self.sampling_interval = sampling_interval
        self.running = False
        self.monitor_thread = None
        self.system_metrics_history: List[SystemMetrics] = []
        self.process_metrics: Dict[int, ProcessMetrics] = {}
        self.lock = threading.Lock()
        self.max_history = 300  # Keep last 5 minutes of data
        self.callbacks = []
        
    def start(self):
        """Start the monitoring thread"""
        if not self.running:
            self.running = True
            self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.monitor_thread.start()
    
    def stop(self):
        """Stop the monitoring thread"""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
    
    def register_callback(self, callback):
        """Register a callback to be called when metrics are updated"""
        self.callbacks.append(callback)
    
    def _notify_callbacks(self, metrics: SystemMetrics):
        """Notify all registered callbacks of new metrics"""
        for callback in self.callbacks:
            try:
                callback(metrics)
            except Exception as e:
                print(f"Error in callback: {e}")
    
    def _monitor_loop(self):
        """Main monitoring loop running in background thread"""
        while self.running:
            try:
                system_metrics = self._collect_system_metrics()
                self._collect_process_metrics()
                
                with self.lock:
                    self.system_metrics_history.append(system_metrics)
                    if len(self.system_metrics_history) > self.max_history:
                        self.system_metrics_history.pop(0)
                
                self._notify_callbacks(system_metrics)
                time.sleep(self.sampling_interval)
                
            except Exception as e:
                print(f"Error in monitoring loop: {e}")
    
    def _collect_system_metrics(self) -> SystemMetrics:
        """Collect overall system performance metrics"""
        cpu_count = psutil.cpu_count()
        cpu_percent = psutil.cpu_percent(interval=0.1)
        
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        disk_usage = {}
        try:
            partitions = psutil.disk_partitions()
            for partition in partitions:
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    disk_usage[partition.mountpoint] = usage.percent
                except:
                    pass
        except:
            pass
        
        return SystemMetrics(
            timestamp=datetime.now(),
            cpu_percent=cpu_percent,
            cpu_count=cpu_count,
            memory_total_mb=memory.total / (1024 ** 2),
            memory_used_mb=memory.used / (1024 ** 2),
            memory_percent=memory.percent,
            memory_available_mb=memory.available / (1024 ** 2),
            swap_used_mb=swap.used / (1024 ** 2),
            swap_percent=swap.percent,
            disk_usage_percent=disk_usage,
            process_count=len(psutil.pids())
        )
    
    def _collect_process_metrics(self):
        """Collect metrics for all running processes"""
        with self.lock:
            current_pids = set(psutil.pids())
            tracked_pids = set(self.process_metrics.keys())
            
            # Remove processes that no longer exist
            for pid in tracked_pids - current_pids:
                del self.process_metrics[pid]
            
            # Update existing and new processes
            for pid in current_pids:
                try:
                    process = psutil.Process(pid)
                    if process.status() != psutil.STATUS_ZOMBIE:
                        with process.oneshot():
                            self.process_metrics[pid] = ProcessMetrics(
                                pid=pid,
                                name=process.name(),
                                cpu_percent=process.cpu_percent(interval=0.01),
                                memory_mb=process.memory_info().rss / (1024 ** 2),
                                memory_percent=process.memory_percent(),
                                num_threads=process.num_threads(),
                                status=process.status(),
                                create_time=process.create_time(),
                                priority=process.nice()
                            )
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    if pid in self.process_metrics:
                        del self.process_metrics[pid]
    
    def get_latest_system_metrics(self) -> Optional[SystemMetrics]:
        """Get the most recent system metrics"""
        with self.lock:
            return self.system_metrics_history[-1] if self.system_metrics_history else None
    
    def get_process_metrics(self, pid: Optional[int] = None) -> Dict[int, ProcessMetrics]:
        """Get metrics for processes. If pid is None, return all processes"""
        with self.lock:
            if pid is None:
                return dict(self.process_metrics)
            return {pid: self.process_metrics[pid]} if pid in self.process_metrics else {}
    
    def get_top_processes(self, metric: str = 'cpu_percent', limit: int = 10) -> List[ProcessMetrics]:
        """Get top N processes by specified metric (cpu_percent or memory_mb)"""
        with self.lock:
            processes = list(self.process_metrics.values())
        
        if metric == 'cpu_percent':
            processes.sort(key=lambda p: p.cpu_percent, reverse=True)
        elif metric == 'memory_mb':
            processes.sort(key=lambda p: p.memory_mb, reverse=True)
        
        return processes[:limit]
    
    def get_metrics_history(self, minutes: int = 5) -> List[SystemMetrics]:
        """Get historical metrics from the last N minutes"""
        with self.lock:
            return list(self.system_metrics_history)
    
    def export_metrics_to_json(self, filepath: str):
        """Export current metrics to JSON file"""
        with self.lock:
            system_metrics = self.system_metrics_history[-1] if self.system_metrics_history else None
            processes = list(self.process_metrics.values())
        
        if not system_metrics:
            return False
        
        data = {
            'timestamp': system_metrics.timestamp.isoformat(),
            'system': {
                'cpu_percent': system_metrics.cpu_percent,
                'cpu_count': system_metrics.cpu_count,
                'memory_total_mb': system_metrics.memory_total_mb,
                'memory_used_mb': system_metrics.memory_used_mb,
                'memory_percent': system_metrics.memory_percent,
                'memory_available_mb': system_metrics.memory_available_mb,
                'swap_used_mb': system_metrics.swap_used_mb,
                'process_count': system_metrics.process_count
            },
            'top_processes': [
                {
                    'pid': p.pid,
                    'name': p.name,
                    'cpu_percent': p.cpu_percent,
                    'memory_mb': p.memory_mb,
                    'memory_percent': p.memory_percent
                }
                for p in self.get_top_processes('cpu_percent', 20)
            ]
        }
        
        try:
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            print(f"Error exporting metrics: {e}")
            return False
