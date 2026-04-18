"""
Dynamic Resource Allocator - Main System Orchestrator
Integrates monitoring, resource management, and optimization components
"""

import threading
import time
import json
from typing import Dict, List, Optional
from datetime import datetime
import logging

from system_monitor import SystemMonitor, SystemMetrics
from resource_manager import ResourceManager, ProcessPriority, ResourceAllocationStrategy
from performance_optimizer import PerformanceOptimizer


class DynamicResourceAllocator:
    """
    Main system that coordinates dynamic resource allocation across multiple programs
    """
    
    def __init__(self):
        self.monitor = SystemMonitor(sampling_interval=1.0)
        self.resource_manager = ResourceManager()
        self.optimizer = PerformanceOptimizer(self.monitor, self.resource_manager)
        self.logger = self._setup_logger()
        self.running = False
        self.metrics_callback = None
        self.config = self._load_default_config()
        self.start_time = None
    
    def _setup_logger(self):
        """Setup main system logger"""
        logger = logging.getLogger('DynamicResourceAllocator')
        logger.handlers.clear()  # Clear existing handlers
        
        handler = logging.FileHandler('resource_allocator.log')
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        logger.setLevel(logging.INFO)
        return logger
    
    def _load_default_config(self) -> Dict:
        """Load default configuration"""
        return {
            'monitoring_interval': 1.0,
            'optimization_interval': 5.0,
            'cpu_threshold_high': 80,
            'cpu_threshold_critical': 95,
            'memory_threshold_high': 85,
            'memory_threshold_critical': 95,
            'allocation_strategy': 'performance',
            'enable_logging': True,
            'max_history_entries': 300,
            'reserved_memory_percent': 10,
        }
    
    def load_config(self, config_path: str) -> bool:
        """Load configuration from JSON file"""
        try:
            with open(config_path, 'r') as f:
                self.config = json.load(f)
            self.logger.info(f"Configuration loaded from {config_path}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to load config: {e}")
            return False
    
    def save_config(self, config_path: str) -> bool:
        """Save current configuration to JSON file"""
        try:
            with open(config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
            self.logger.info(f"Configuration saved to {config_path}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to save config: {e}")
            return False
    
    def start(self) -> bool:
        """Start the dynamic resource allocation system"""
        if self.running:
            self.logger.warning("System already running")
            return False
        
        try:
            self.logger.info("=" * 60)
            self.logger.info("Starting Dynamic Resource Allocator")
            self.logger.info("=" * 60)
            
            # Start all components
            self.monitor.start()
            self.optimizer.start()
            
            # Register monitoring callback
            self.monitor.register_callback(self._on_metrics_updated)
            
            self.running = True
            self.start_time = datetime.now()
            
            self.logger.info("All components started successfully")
            self.logger.info(f"CPU Cores Available: {self.resource_manager.available_cores}")
            self.logger.info(f"Allocation Strategy: {self.resource_manager.strategy.value}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start system: {e}")
            self.running = False
            return False
    
    def stop(self) -> bool:
        """Stop the dynamic resource allocation system"""
        if not self.running:
            return False
        
        try:
            self.logger.info("Stopping Dynamic Resource Allocator...")
            
            self.monitor.stop()
            self.optimizer.stop()
            
            self.running = False
            uptime = (datetime.now() - self.start_time).total_seconds()
            
            self.logger.info(f"System stopped. Uptime: {uptime:.1f} seconds")
            self.logger.info("=" * 60)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")
            return False
    
    def register_program(self, pid: int, program_name: str,
                        priority: ProcessPriority = ProcessPriority.NORMAL) -> bool:
        """Register a program for resource management"""
        if not self.running:
            self.logger.warning("System not running")
            return False
        
        result = self.resource_manager.register_process(pid, program_name, priority)
        if result:
            self.logger.info(f"Registered program: {program_name} (PID: {pid})")
        return result
    
    def unregister_program(self, pid: int) -> bool:
        """Unregister a program from resource management"""
        result = self.resource_manager.unregister_process(pid)
        if result:
            self.logger.info(f"Unregistered program PID: {pid}")
        return result
    
    def set_program_priority(self, pid: int, priority: ProcessPriority) -> bool:
        """Update the priority of a registered program"""
        result = self.resource_manager.set_process_priority(pid, priority)
        if result:
            self.logger.info(f"Updated priority for PID {pid} to {priority.name}")
        return result
    
    def set_allocation_strategy(self, strategy: ResourceAllocationStrategy) -> bool:
        """Change the resource allocation strategy"""
        try:
            self.resource_manager.set_allocation_strategy(strategy)
            self.config['allocation_strategy'] = strategy.value
            self.logger.info(f"Allocation strategy changed to: {strategy.value}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to set allocation strategy: {e}")
            return False
    
    def _on_metrics_updated(self, metrics: SystemMetrics):
        """Callback when new system metrics are available"""
        try:
            # Check for critical conditions
            if metrics.cpu_percent > self.config['cpu_threshold_critical']:
                self.logger.warning(
                    f"CRITICAL: CPU usage at {metrics.cpu_percent}% - triggering emergency throttling"
                )
            
            if metrics.memory_percent > self.config['memory_threshold_critical']:
                self.logger.warning(
                    f"CRITICAL: Memory usage at {metrics.memory_percent}% - activating memory pressure"
                )
            
            # Call registered callback if available
            if self.metrics_callback:
                self.metrics_callback(metrics)
                
        except Exception as e:
            self.logger.error(f"Error in metrics callback: {e}")
    
    def get_system_status(self) -> Dict:
        """Get current system status"""
        metrics = self.monitor.get_latest_system_metrics()
        allocations = self.resource_manager.get_all_allocations()
        optimizer_report = self.optimizer.get_optimization_report()
        
        # Always include basic status even if metrics not ready
        status = {
            'running': self.running,
            'uptime_seconds': (datetime.now() - self.start_time).total_seconds() if self.start_time else 0,
            'allocation_strategy': self.resource_manager.strategy.value,
        }
        
        if not metrics:
            status['error'] = 'No metrics available'
            return status
        
        status.update({
            'system_metrics': {
                'timestamp': metrics.timestamp.isoformat(),
                'cpu_percent': metrics.cpu_percent,
                'cpu_count': metrics.cpu_count,
                'memory_percent': metrics.memory_percent,
                'memory_used_mb': metrics.memory_used_mb,
                'memory_total_mb': metrics.memory_total_mb,
                'memory_available_mb': metrics.memory_available_mb,
                'process_count': metrics.process_count,
            },
            'resource_allocations': len(allocations),
            'tracked_programs': len(self.resource_manager.tracked_processes),
            'optimizer_stats': optimizer_report,
        })
        
        return status
    
    def get_program_status(self, pid: int) -> Optional[Dict]:
        """Get status of a specific program"""
        process_metrics = self.monitor.get_process_metrics(pid)
        allocation = self.resource_manager.get_allocation(pid)
        
        if not process_metrics:
            return None
        
        metrics = list(process_metrics.values())[0]
        
        return {
            'pid': pid,
            'name': metrics.name,
            'cpu_percent': metrics.cpu_percent,
            'memory_mb': metrics.memory_mb,
            'memory_percent': metrics.memory_percent,
            'num_threads': metrics.num_threads,
            'status': metrics.status,
            'allocation': {
                'cpu_quota_percent': allocation.cpu_quota_percent if allocation else None,
                'memory_limit_mb': allocation.memory_limit_mb if allocation else None,
                'cpu_cores': allocation.cpu_affinity if allocation else None,
                'priority': allocation.priority.name if allocation else None,
            } if allocation else None
        }
    
    def get_performance_report(self) -> Dict:
        """Generate a detailed performance report"""
        system_metrics = self.monitor.get_latest_system_metrics()
        top_cpu = self.monitor.get_top_processes('cpu_percent', 10)
        top_memory = self.monitor.get_top_processes('memory_mb', 10)
        optimizer_report = self.optimizer.get_optimization_report()
        
        return {
            'timestamp': datetime.now().isoformat(),
            'system_metrics': {
                'cpu_usage': system_metrics.cpu_percent if system_metrics else 0,
                'memory_usage': system_metrics.memory_percent if system_metrics else 0,
                'total_processes': system_metrics.process_count if system_metrics else 0,
            },
            'top_processes_by_cpu': [
                {
                    'pid': p.pid,
                    'name': p.name,
                    'cpu_percent': p.cpu_percent,
                    'memory_mb': p.memory_mb,
                }
                for p in top_cpu
            ],
            'top_processes_by_memory': [
                {
                    'pid': p.pid,
                    'name': p.name,
                    'cpu_percent': p.cpu_percent,
                    'memory_mb': p.memory_mb,
                }
                for p in top_memory
            ],
            'optimization_stats': optimizer_report,
        }
    
    def export_report(self, filepath: str) -> bool:
        """Export current system status and performance report to JSON"""
        try:
            report = {
                'timestamp': datetime.now().isoformat(),
                'system_status': self.get_system_status(),
                'performance_report': self.get_performance_report(),
            }
            
            with open(filepath, 'w') as f:
                json.dump(report, f, indent=2)
            
            self.logger.info(f"Report exported to {filepath}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to export report: {e}")
            return False
    
    def run_interactive_mode(self):
        """Run the system in interactive mode with command-line interface"""
        print("\n" + "="*60)
        print("Dynamic Resource Allocator - Interactive Mode")
        print("="*60)
        print("\nCommands:")
        print("  start           - Start resource allocation")
        print("  stop            - Stop resource allocation")
        print("  status          - Show system status")
        print("  top             - Show top processes by CPU")
        print("  report          - Show detailed performance report")
        print("  register PID    - Register program for management")
        print("  strategy STR    - Change allocation strategy")
        print("  export FILE     - Export report to JSON file")
        print("  help            - Show this help message")
        print("  exit            - Exit the program")
        print("="*60 + "\n")
        
        self.start()
        
        try:
            while True:
                try:
                    cmd = input(">> ").strip().lower().split()
                    
                    if not cmd:
                        continue
                    
                    if cmd[0] == 'start':
                        if not self.running:
                            self.start()
                    
                    elif cmd[0] == 'stop':
                        self.stop()
                    
                    elif cmd[0] == 'status':
                        status = self.get_system_status()
                        print(json.dumps(status, indent=2))
                    
                    elif cmd[0] == 'top':
                        report = self.get_performance_report()
                        print("\nTop Processes by CPU:")
                        for p in report['top_processes_by_cpu'][:5]:
                            print(f"  {p['pid']:6} {p['name']:30} CPU: {p['cpu_percent']:6.2f}% MEM: {p['memory_mb']:8.2f}MB")
                    
                    elif cmd[0] == 'report':
                        report = self.get_performance_report()
                        print(json.dumps(report, indent=2))
                    
                    elif cmd[0] == 'register' and len(cmd) > 1:
                        pid = int(cmd[1])
                        program_name = ' '.join(cmd[2:]) if len(cmd) > 2 else f"Program_{pid}"
                        self.register_program(pid, program_name)
                    
                    elif cmd[0] == 'strategy' and len(cmd) > 1:
                        strategy_name = cmd[1].upper()
                        strategy = ResourceAllocationStrategy[strategy_name]
                        self.set_allocation_strategy(strategy)
                    
                    elif cmd[0] == 'export' and len(cmd) > 1:
                        self.export_report(cmd[1])
                    
                    elif cmd[0] == 'help':
                        print("\nAvailable commands:")
                        print("  start, stop, status, top, report, register PID, strategy, export FILE, help, exit")
                    
                    elif cmd[0] == 'exit':
                        break
                    
                    else:
                        print("Unknown command. Type 'help' for available commands.")
                
                except ValueError as e:
                    print(f"Invalid input: {e}")
                except Exception as e:
                    print(f"Error: {e}")
        
        finally:
            self.stop()
            print("\nGoodbye!")


# Convenience functions for easy usage
def create_allocator() -> DynamicResourceAllocator:
    """Create and return a new DynamicResourceAllocator instance"""
    return DynamicResourceAllocator()


if __name__ == '__main__':
    allocator = create_allocator()
    allocator.run_interactive_mode()
