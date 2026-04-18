"""
Resource Manager Module
Handles dynamic resource allocation and priority adjustments for processes
"""

import psutil
import threading
from dataclasses import dataclass
from typing import Dict, List, Optional, Set
from enum import Enum
import logging


class ProcessPriority(Enum):
    """Process priority levels"""
    CRITICAL = 0      # Cannot be throttled
    HIGH = 1          # Minimal throttling
    NORMAL = 2        # Standard resources
    LOW = 3           # Can be significantly throttled
    BACKGROUND = 4    # Minimal resources


class ResourceAllocationStrategy(Enum):
    """Resource allocation strategies"""
    EQUAL = "equal"              # Equal distribution
    PRIORITY = "priority"         # Based on process priority
    PERFORMANCE = "performance"   # Based on historical performance needs
    DEMAND = "demand"             # Based on current demand


@dataclass
class ResourceAllocation:
    """Represents resource allocation for a process"""
    pid: int
    process_name: str
    cpu_affinity: List[int]  # CPU cores to use
    cpu_quota_percent: float  # Maximum CPU usage percentage
    memory_limit_mb: Optional[float]  # Memory limit in MB
    priority: ProcessPriority
    allocation_reason: str


class ResourceManager:
    """Manages dynamic resource allocation for processes"""
    
    def __init__(self, num_cpu_cores: Optional[int] = None):
        self.num_cpu_cores = num_cpu_cores or psutil.cpu_count()
        self.tracked_processes: Dict[int, Dict] = {}
        self.allocations: Dict[int, ResourceAllocation] = {}
        self.lock = threading.Lock()
        self.logger = self._setup_logger()
        self.strategy = ResourceAllocationStrategy.PERFORMANCE
        self.reserved_cores = 1  # Keep 1 core reserved for system
        self.available_cores = max(1, self.num_cpu_cores - self.reserved_cores)
        self.memory_safety_margin_percent = 10  # Keep 10% memory free
    
    def _setup_logger(self):
        """Setup logging for resource management"""
        logger = logging.getLogger('ResourceManager')
        if not logger.handlers:
            handler = logging.FileHandler('resource_manager.log')
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    
    def register_process(self, pid: int, process_name: str, 
                        priority: ProcessPriority = ProcessPriority.NORMAL) -> bool:
        """Register a process for resource management"""
        with self.lock:
            if pid in self.tracked_processes:
                return False
            
            self.tracked_processes[pid] = {
                'name': process_name,
                'priority': priority,
                'created_at': psutil.Process(pid).create_time(),
                'history': []
            }
            self.logger.info(f"Registered process {process_name} (PID: {pid}) with priority {priority.name}")
            return True
    
    def unregister_process(self, pid: int) -> bool:
        """Unregister a process from resource management"""
        with self.lock:
            if pid in self.tracked_processes:
                del self.tracked_processes[pid]
                if pid in self.allocations:
                    del self.allocations[pid]
                self.logger.info(f"Unregistered process PID: {pid}")
                return True
            return False
    
    def set_process_priority(self, pid: int, priority: ProcessPriority) -> bool:
        """Update the priority of a tracked process"""
        with self.lock:
            if pid not in self.tracked_processes:
                return False
            self.tracked_processes[pid]['priority'] = priority
            self.logger.info(f"Set priority for PID {pid} to {priority.name}")
            return True
    
    def allocate_resources(self, pid: int, system_metrics, strategy: Optional[ResourceAllocationStrategy] = None):
        """
        Allocate resources to a process based on strategy and system metrics
        Returns True if allocation was successful
        """
        if pid not in self.tracked_processes:
            return False
        
        strategy = strategy or self.strategy
        
        try:
            process = psutil.Process(pid)
            process_info = self.tracked_processes[pid]
            priority = process_info['priority']
            
            # Calculate CPU allocation
            cpu_quota = self._calculate_cpu_quota(pid, priority, system_metrics)
            cpu_affinity = self._calculate_cpu_affinity(pid, priority, cpu_quota)
            
            # Calculate memory limit
            memory_limit = self._calculate_memory_limit(pid, priority, system_metrics)
            
            allocation = ResourceAllocation(
                pid=pid,
                process_name=process_info['name'],
                cpu_affinity=cpu_affinity,
                cpu_quota_percent=cpu_quota,
                memory_limit_mb=memory_limit,
                priority=priority,
                allocation_reason=f"Strategy: {strategy.value}"
            )
            
            # Apply allocation
            self._apply_allocation(process, allocation)
            
            with self.lock:
                self.allocations[pid] = allocation
            
            self.logger.info(
                f"Allocated resources to {process_info['name']} (PID: {pid}): "
                f"CPU quota: {cpu_quota}%, Memory: {memory_limit}MB"
            )
            return True
            
        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            self.logger.warning(f"Cannot allocate resources to PID {pid}: {e}")
            return False
    
    def _calculate_cpu_quota(self, pid: int, priority: ProcessPriority, system_metrics) -> float:
        """Calculate CPU quota for a process based on priority and system state"""
        base_quota = 100.0 / len([p for p in self.tracked_processes.values()])
        
        if system_metrics.cpu_percent < 30:
            # Low system load - allow more CPU
            multiplier = 1.5
        elif system_metrics.cpu_percent < 70:
            # Normal load
            multiplier = 1.0
        else:
            # High load - restrict CPU
            multiplier = 0.7
        
        # Apply priority adjustments
        priority_multiplier = {
            ProcessPriority.CRITICAL: 2.0,
            ProcessPriority.HIGH: 1.5,
            ProcessPriority.NORMAL: 1.0,
            ProcessPriority.LOW: 0.6,
            ProcessPriority.BACKGROUND: 0.3
        }
        
        quota = base_quota * multiplier * priority_multiplier.get(priority, 1.0)
        return min(100.0, quota)  # Cap at 100%
    
    def _calculate_cpu_affinity(self, pid: int, priority: ProcessPriority, cpu_quota: float) -> List[int]:
        """Calculate which CPU cores to allocate to a process"""
        cores_needed = max(1, int(self.available_cores * (cpu_quota / 100)))
        
        # Critical processes get access to more cores
        if priority == ProcessPriority.CRITICAL:
            cores_needed = min(self.available_cores, cores_needed * 2)
        # Background processes use fewer cores
        elif priority == ProcessPriority.BACKGROUND:
            cores_needed = max(1, cores_needed // 2)
        
        # Simple round-robin core assignment based on PID
        start_core = (pid % self.available_cores)
        affinity = [(start_core + i) % self.available_cores for i in range(cores_needed)]
        return sorted(set(affinity))  # Return unique cores
    
    def _calculate_memory_limit(self, pid: int, priority: ProcessPriority, system_metrics) -> Optional[float]:
        """Calculate memory limit for a process"""
        available_memory = system_metrics.memory_available_mb
        usable_memory = available_memory * (1 - self.memory_safety_margin_percent / 100)
        
        # Determine how much memory to allocate based on priority
        memory_share = {
            ProcessPriority.CRITICAL: 0.50,    # 50% of available
            ProcessPriority.HIGH: 0.30,        # 30%
            ProcessPriority.NORMAL: 0.15,      # 15%
            ProcessPriority.LOW: 0.04,         # 4%
            ProcessPriority.BACKGROUND: 0.01   # 1%
        }
        
        limit = usable_memory * memory_share.get(priority, 0.15)
        return max(128, limit)  # Minimum 128MB
    
    def _apply_allocation(self, process: psutil.Process, allocation: ResourceAllocation):
        """Apply the calculated allocation to the process"""
        try:
            # Set CPU affinity
            if allocation.cpu_affinity:
                process.cpu_affinity(allocation.cpu_affinity)
            
            # Set process nice value based on priority
            nice_values = {
                ProcessPriority.CRITICAL: -10,
                ProcessPriority.HIGH: -5,
                ProcessPriority.NORMAL: 0,
                ProcessPriority.LOW: 5,
                ProcessPriority.BACKGROUND: 10
            }
            process.nice(nice_values.get(allocation.priority, 0))
            
            # Note: Memory limits require special handling (cgroups on Linux, Job Objects on Windows)
            # This is a placeholder for where that would be implemented
            
        except (psutil.NoSuchProcess, psutil.AccessDenied, OSError) as e:
            self.logger.warning(f"Failed to apply allocation to PID {process.pid}: {e}")
    
    def rebalance_resources(self, system_metrics, top_processes):
        """
        Rebalance resources among all tracked processes based on current system state
        """
        with self.lock:
            pids_to_reallocate = list(self.tracked_processes.keys())
        
        active_processes = {p.pid for p in top_processes}
        
        # Reallocate to active tracked processes
        for pid in pids_to_reallocate:
            if pid in active_processes:
                self.allocate_resources(pid, system_metrics)
            else:
                # Process might be idle, reduce allocation
                with self.lock:
                    if pid in self.allocations:
                        allocation = self.allocations[pid]
                        allocation.cpu_quota_percent = 10  # Minimal quota
                        self.logger.debug(f"Reduced allocation for idle process PID {pid}")
    
    def get_allocation(self, pid: int) -> Optional[ResourceAllocation]:
        """Get current allocation for a process"""
        with self.lock:
            return self.allocations.get(pid)
    
    def get_all_allocations(self) -> List[ResourceAllocation]:
        """Get all current allocations"""
        with self.lock:
            return list(self.allocations.values())
    
    def set_allocation_strategy(self, strategy: ResourceAllocationStrategy):
        """Change the resource allocation strategy"""
        self.strategy = strategy
        self.logger.info(f"Changed allocation strategy to: {strategy.value}")
