"""
Performance Optimizer Module
Analyzes system performance and makes intelligent resource reallocation decisions
"""

import threading
import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple
from collections import deque
import statistics
import logging


@dataclass
class PerformanceMetric:
    """Stores a performance metric for a process over time"""
    timestamp: float
    cpu_percent: float
    memory_percent: float
    response_time_ms: Optional[float]  # Application-level metric if available


class PerformanceOptimizer:
    """
    Optimizes resource allocation by analyzing performance trends
    and detecting bottlenecks
    """
    
    def __init__(self, monitor, resource_manager, window_size: int = 60):
        self.monitor = monitor
        self.resource_manager = resource_manager
        self.window_size = window_size  # Number of samples to track
        self.performance_history: Dict[int, deque] = {}
        self.bottleneck_processes: Set[int] = set()
        self.throttled_processes: Set[int] = set()
        self.optimization_stats: Dict[str, float] = {
            'total_optimizations': 0,
            'successful_reallocations': 0,
            'bottlenecks_resolved': 0
        }
        self.lock = threading.Lock()
        self.logger = self._setup_logger()
        self.running = False
        self.optimizer_thread = None
        self.optimization_interval = 5  # Seconds between optimizations
    
    def _setup_logger(self):
        """Setup logging for performance optimizer"""
        logger = logging.getLogger('PerformanceOptimizer')
        if not logger.handlers:
            handler = logging.FileHandler('performance_optimizer.log')
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    
    def start(self):
        """Start the performance optimization loop"""
        if not self.running:
            self.running = True
            self.optimizer_thread = threading.Thread(target=self._optimization_loop, daemon=True)
            self.optimizer_thread.start()
            self.logger.info("Performance optimizer started")
    
    def stop(self):
        """Stop the performance optimization loop"""
        self.running = False
        if self.optimizer_thread:
            self.optimizer_thread.join(timeout=5)
        self.logger.info("Performance optimizer stopped")
    
    def _optimization_loop(self):
        """Main optimization loop running in background thread"""
        while self.running:
            try:
                system_metrics = self.monitor.get_latest_system_metrics()
                if system_metrics is None:
                    time.sleep(self.optimization_interval)
                    continue
                
                # Collect performance data
                self._update_performance_history()
                
                # Detect bottlenecks
                bottlenecks = self._detect_bottlenecks()
                
                # Perform optimization
                if bottlenecks or system_metrics.cpu_percent > 80 or system_metrics.memory_percent > 85:
                    self._optimize_allocations(system_metrics, bottlenecks)
                
                time.sleep(self.optimization_interval)
                
            except Exception as e:
                self.logger.error(f"Error in optimization loop: {e}")
    
    def _update_performance_history(self):
        """Update performance history for all tracked processes"""
        processes = self.monitor.get_process_metrics()
        current_time = time.time()
        
        with self.lock:
            for pid, metrics in processes.items():
                if pid not in self.performance_history:
                    self.performance_history[pid] = deque(maxlen=self.window_size)
                
                perf_metric = PerformanceMetric(
                    timestamp=current_time,
                    cpu_percent=metrics.cpu_percent,
                    memory_percent=metrics.memory_percent,
                    response_time_ms=None
                )
                self.performance_history[pid].append(perf_metric)
    
    def _detect_bottlenecks(self) -> Dict[int, str]:
        """
        Detect processes causing performance bottlenecks
        Returns dict mapping PID to bottleneck reason
        """
        bottlenecks = {}
        system_metrics = self.monitor.get_latest_system_metrics()
        
        if not system_metrics:
            return bottlenecks
        
        with self.lock:
            for pid, history in self.performance_history.items():
                if len(history) < 3:
                    continue
                
                recent_samples = list(history)[-10:]  # Last 10 samples
                
                # Calculate statistics
                cpu_values = [s.cpu_percent for s in recent_samples]
                mem_values = [s.memory_percent for s in recent_samples]
                
                avg_cpu = statistics.mean(cpu_values)
                avg_mem = statistics.mean(mem_values)
                cpu_variance = statistics.variance(cpu_values) if len(cpu_values) > 1 else 0
                
                # Detect high CPU usage
                if avg_cpu > 80:
                    bottlenecks[pid] = f"High CPU utilization ({avg_cpu:.1f}%)"
                
                # Detect high memory usage
                if avg_mem > 85:
                    bottlenecks[pid] = f"High memory utilization ({avg_mem:.1f}%)"
                
                # Detect erratic CPU usage (potential thrashing)
                if cpu_variance > 500:
                    bottlenecks[pid] = f"Erratic CPU usage (variance: {cpu_variance:.1f})"
        
        with self.lock:
            self.bottleneck_processes = set(bottlenecks.keys())
        
        return bottlenecks
    
    def _optimize_allocations(self, system_metrics, bottlenecks: Dict[int, str]):
        """Optimize resource allocations based on detected bottlenecks"""
        self.optimization_stats['total_optimizations'] += 1
        
        # Get top processes to prioritize
        top_by_cpu = self.monitor.get_top_processes('cpu_percent', limit=10)
        top_by_memory = self.monitor.get_top_processes('memory_mb', limit=10)
        
        # Deduplicate by PID (avoid trying to hash ProcessMetrics objects)
        seen_pids = set()
        top_processes = []
        for process in top_by_cpu + top_by_memory:
            if process.pid not in seen_pids:
                seen_pids.add(process.pid)
                top_processes.append(process)
        
        # Priority handling for bottlenecks
        if bottlenecks:
            self._handle_bottlenecks(bottlenecks)
            self.optimization_stats['bottlenecks_resolved'] += len(bottlenecks)
        
        # Rebalance resources among tracked processes
        allocations_made = 0
        for process in top_processes:
            if self.resource_manager.allocate_resources(process.pid, system_metrics):
                allocations_made += 1
        
        if allocations_made > 0:
            self.optimization_stats['successful_reallocations'] += allocations_made
            self.logger.info(
                f"Reallocation completed: {allocations_made} processes adjusted. "
                f"System CPU: {system_metrics.cpu_percent}%, Memory: {system_metrics.memory_percent}%"
            )
    
    def _handle_bottlenecks(self, bottlenecks: Dict[int, str]):
        """Handle detected bottlenecks by adjusting allocations"""
        system_metrics = self.monitor.get_latest_system_metrics()
        if not system_metrics:
            return
        
        for pid, reason in bottlenecks.items():
            self.logger.warning(f"Bottleneck detected for PID {pid}: {reason}")
            
            # For high-demand processes, increase allocation
            try:
                current_allocation = self.resource_manager.get_allocation(pid)
                if current_allocation:
                    # Try to increase CPU allocation
                    current_allocation.cpu_quota_percent = min(
                        100,
                        current_allocation.cpu_quota_percent * 1.2
                    )
                    self.logger.info(
                        f"Increased CPU quota for PID {pid} to {current_allocation.cpu_quota_percent:.1f}%"
                    )
            except Exception as e:
                self.logger.warning(f"Failed to handle bottleneck for PID {pid}: {e}")
    
    def _estimate_process_impact(self, pid: int) -> float:
        """Estimate the impact of a process on overall system performance (0-1)"""
        system_metrics = self.monitor.get_latest_system_metrics()
        if not system_metrics:
            return 0
        
        with self.lock:
            if pid not in self.performance_history:
                return 0
            
            history = list(self.performance_history[pid])
            if not history:
                return 0
            
            recent_samples = history[-10:]
            avg_cpu = statistics.mean([s.cpu_percent for s in recent_samples])
            avg_mem = statistics.mean([s.memory_percent for s in recent_samples])
        
        # Impact score (normalized)
        cpu_impact = avg_cpu / 100
        mem_impact = avg_mem / 100
        total_impact = (cpu_impact * 0.6 + mem_impact * 0.4)  # CPU weighted higher
        
        return min(1.0, total_impact)
    
    def suggest_process_priority(self, pid: int):
        """Suggest a process priority based on performance impact"""
        impact = self._estimate_process_impact(pid)
        
        from resource_manager import ProcessPriority
        
        if impact > 0.8:
            return ProcessPriority.CRITICAL
        elif impact > 0.6:
            return ProcessPriority.HIGH
        elif impact > 0.4:
            return ProcessPriority.NORMAL
        elif impact > 0.2:
            return ProcessPriority.LOW
        else:
            return ProcessPriority.BACKGROUND
    
    def get_optimization_report(self) -> Dict:
        """Generate a report of optimization activities"""
        with self.lock:
            stats = dict(self.optimization_stats)
        
        return {
            'current_bottlenecks': len(self.bottleneck_processes),
            'optimization_stats': stats,
            'performance_history_size': len(self.performance_history),
            'success_rate': (
                stats['successful_reallocations'] / max(1, stats['total_optimizations'])
            ) if stats['total_optimizations'] > 0 else 0
        }


class BottleneckDetector:
    """Advanced bottleneck detection algorithms"""
    
    @staticmethod
    def detect_cpu_thrashing(history: deque, threshold: float = 500) -> bool:
        """Detect when a process is thrashing (rapid CPU fluctuations)"""
        if len(history) < 5:
            return False
        
        samples = list(history)[-20:]
        cpu_values = [s.cpu_percent for s in samples]
        
        if len(cpu_values) < 2:
            return False
        
        variance = statistics.variance(cpu_values)
        return variance > threshold
    
    @staticmethod
    def detect_memory_leak(history: deque, check_duration: int = 10) -> bool:
        """Detect potential memory leaks (steady memory increase)"""
        if len(history) < check_duration:
            return False
        
        recent_samples = list(history)[-check_duration:]
        mem_values = [s.memory_percent for s in recent_samples]
        
        # Check if memory is consistently increasing
        increases = sum(1 for i in range(1, len(mem_values)) if mem_values[i] > mem_values[i-1])
        return increases >= len(mem_values) - 2
    
    @staticmethod
    def detect_io_wait(history: deque) -> bool:
        """Detect potential I/O wait (low CPU, high memory with disk activity pattern)"""
        if len(history) < 5:
            return False
        
        recent_samples = list(history)[-10:]
        cpu_values = [s.cpu_percent for s in recent_samples]
        mem_values = [s.memory_percent for s in recent_samples]
        
        avg_cpu = statistics.mean(cpu_values)
        avg_mem = statistics.mean(mem_values)
        
        # Low CPU but high memory suggests I/O wait
        return avg_cpu < 20 and avg_mem > 50
