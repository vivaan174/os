"""
Example Usage - Dynamic Resource Allocator
Demonstrates how to use the resource allocation system programmatically
"""

import time
import os
import subprocess
import json
from dynamic_allocator import DynamicResourceAllocator
from resource_manager import ProcessPriority, ResourceAllocationStrategy


class ResourceAllocationDemo:
    """Demo class showing various usage patterns"""
    
    def __init__(self):
        self.allocator = DynamicResourceAllocator()
    
    def demo_basic_usage(self):
        """Demonstrate basic system usage"""
        print("\n" + "="*60)
        print("DEMO 1: Basic System Usage")
        print("="*60)
        
        # Start the system
        print("\n1. Starting resource allocator...")
        self.allocator.start()
        time.sleep(2)
        
        # Get system status
        print("\n2. System Status:")
        status = self.allocator.get_system_status()
        print(f"   CPU Usage: {status['system_metrics']['cpu_percent']:.1f}%")
        print(f"   Memory Usage: {status['system_metrics']['memory_percent']:.1f}%")
        print(f"   Total Processes: {status['system_metrics']['process_count']}")
        print(f"   Tracked Programs: {status['tracked_programs']}")
        
        # Get performance report
        print("\n3. Top 5 Processes by CPU:")
        report = self.allocator.get_performance_report()
        for i, proc in enumerate(report['top_processes_by_cpu'][:5], 1):
            print(f"   {i}. {proc['name']} (PID: {proc['pid']}) - CPU: {proc['cpu_percent']:.2f}%")
        
        print("\n4. Top 5 Processes by Memory:")
        for i, proc in enumerate(report['top_processes_by_memory'][:5], 1):
            print(f"   {i}. {proc['name']} (PID: {proc['pid']}) - Memory: {proc['memory_mb']:.2f}MB")
        
        self.allocator.stop()
        print("\nDemo 1 Complete!\n")
    
    def demo_program_registration(self):
        """Demonstrate registering and managing specific programs"""
        print("\n" + "="*60)
        print("DEMO 2: Program Registration and Priority Management")
        print("="*60)
        
        self.allocator.start()
        time.sleep(1)
        
        # Create test processes
        print("\n1. Creating test processes...")
        
        # Start simple Python processes for testing
        test_processes = []
        try:
            # These commands create simple processes that consume CPU/memory
            cmd = 'import time; [time.sleep(0.1) for _ in range(1000)]'
            
            for i in range(3):
                proc = subprocess.Popen(['python', '-c', cmd])
                test_processes.append(proc)
                print(f"   Started test process {i+1} (PID: {proc.pid})")
                time.sleep(0.5)
            
            time.sleep(2)  # Let processes run
            
            # Register processes with different priorities
            print("\n2. Registering processes with priorities...")
            if test_processes[0].poll() is None:  # Check if still running
                self.allocator.register_program(
                    test_processes[0].pid,
                    "HighPriorityApp",
                    ProcessPriority.HIGH
                )
                print(f"   Registered PID {test_processes[0].pid} as HIGH priority")
            
            if len(test_processes) > 1 and test_processes[1].poll() is None:
                self.allocator.register_program(
                    test_processes[1].pid,
                    "NormalPriorityApp",
                    ProcessPriority.NORMAL
                )
                print(f"   Registered PID {test_processes[1].pid} as NORMAL priority")
            
            # Show program status
            print("\n3. Program Status:")
            for proc in test_processes[:2]:
                if proc.poll() is None:
                    status = self.allocator.get_program_status(proc.pid)
                    if status:
                        print(f"   {status['name']} (PID: {proc.pid}):")
                        print(f"      CPU: {status['cpu_percent']:.2f}%")
                        print(f"      Memory: {status['memory_mb']:.2f}MB")
                        if status['allocation']:
                            print(f"      Allocated CPU Quota: {status['allocation']['cpu_quota_percent']:.1f}%")
        
        finally:
            # Cleanup
            print("\n4. Cleaning up test processes...")
            for proc in test_processes:
                try:
                    proc.terminate()
                    proc.wait(timeout=2)
                except:
                    proc.kill()
            print("   All test processes terminated")
            
            self.allocator.stop()
        
        print("\nDemo 2 Complete!\n")
    
    def demo_allocation_strategies(self):
        """Demonstrate different allocation strategies"""
        print("\n" + "="*60)
        print("DEMO 3: Resource Allocation Strategies")
        print("="*60)
        
        self.allocator.start()
        time.sleep(1)
        
        strategies = [
            ResourceAllocationStrategy.EQUAL,
            ResourceAllocationStrategy.PRIORITY,
            ResourceAllocationStrategy.PERFORMANCE,
            ResourceAllocationStrategy.DEMAND,
        ]
        
        print("\n1. Available Allocation Strategies:")
        for strategy in strategies:
            print(f"   - {strategy.value.upper()}")
        
        print("\n2. Switching strategies and showing effects...")
        
        for strategy in strategies:
            print(f"\n   Applying {strategy.value.upper()} strategy...")
            self.allocator.set_allocation_strategy(strategy)
            time.sleep(3)
            
            status = self.allocator.get_system_status()
            print(f"      System CPU: {status['system_metrics']['cpu_percent']:.1f}%")
            print(f"      System Memory: {status['system_metrics']['memory_percent']:.1f}%")
        
        self.allocator.stop()
        print("\nDemo 3 Complete!\n")
    
    def demo_monitoring_export(self):
        """Demonstrate monitoring and data export"""
        print("\n" + "="*60)
        print("DEMO 4: Monitoring and Data Export")
        print("="*60)
        
        self.allocator.start()
        time.sleep(2)
        
        print("\n1. Real-time monitoring for 10 seconds...")
        for i in range(10):
            status = self.allocator.get_system_status()
            print(f"   [{i+1}] CPU: {status['system_metrics']['cpu_percent']:6.1f}% | "
                  f"Memory: {status['system_metrics']['memory_percent']:6.1f}%")
            time.sleep(1)
        
        print("\n2. Exporting system report...")
        report_file = 'resource_allocation_report.json'
        if self.allocator.export_report(report_file):
            print(f"   Report exported to {report_file}")
            
            # Show report contents
            with open(report_file, 'r') as f:
                report = json.load(f)
            print(f"\n3. Report Summary:")
            print(f"   Timestamp: {report['timestamp']}")
            print(f"   System CPU Usage: {report['system_status']['system_metrics']['cpu_percent']:.1f}%")
            print(f"   System Memory Usage: {report['system_status']['system_metrics']['memory_percent']:.1f}%")
            print(f"   Total Processes: {report['system_status']['system_metrics']['total_processes']}")
        
        self.allocator.stop()
        print("\nDemo 4 Complete!\n")
    
    def demo_performance_optimization(self):
        """Demonstrate performance optimization features"""
        print("\n" + "="*60)
        print("DEMO 5: Performance Optimization")
        print("="*60)
        
        self.allocator.start()
        time.sleep(2)
        
        print("\n1. System Performance Overview:")
        status = self.allocator.get_system_status()
        print(f"   Current Uptime: {status['uptime_seconds']:.1f} seconds")
        print(f"   Allocation Strategy: {status['allocation_strategy']}")
        
        print("\n2. Optimization Statistics:")
        opt_stats = status['optimizer_stats']
        print(f"   Total Optimizations: {opt_stats['total_optimizations']}")
        print(f"   Successful Reallocations: {opt_stats['successful_reallocations']}")
        print(f"   Bottlenecks Resolved: {opt_stats['bottlenecks_resolved']}")
        if opt_stats['total_optimizations'] > 0:
            success_rate = (opt_stats['successful_reallocations'] / opt_stats['total_optimizations']) * 100
            print(f"   Success Rate: {success_rate:.1f}%")
        
        print("\n3. Current System Allocations:")
        allocations = self.allocator.resource_manager.get_all_allocations()
        if allocations:
            print(f"   Total Active Allocations: {len(allocations)}")
            for alloc in allocations[:5]:  # Show first 5
                print(f"      {alloc.process_name} (PID: {alloc.pid}):")
                print(f"         CPU Quota: {alloc.cpu_quota_percent:.1f}%")
                print(f"         Priority: {alloc.priority.name}")
        else:
            print("   No active allocations")
        
        self.allocator.stop()
        print("\nDemo 5 Complete!\n")
    
    def run_all_demos(self):
        """Run all demonstrations"""
        print("\n" + "="*70)
        print(" "*15 + "Dynamic Resource Allocator Demonstrations")
        print("="*70)
        
        try:
            self.demo_basic_usage()
            time.sleep(1)
            
            self.demo_program_registration()
            time.sleep(1)
            
            self.demo_allocation_strategies()
            time.sleep(1)
            
            self.demo_monitoring_export()
            time.sleep(1)
            
            self.demo_performance_optimization()
            
            print("\n" + "="*70)
            print("All demonstrations completed successfully!")
            print("="*70 + "\n")
            
        except KeyboardInterrupt:
            print("\n\nDemo interrupted by user")
            self.allocator.stop()
        except Exception as e:
            print(f"\nError during demo: {e}")
            self.allocator.stop()


def simple_usage_example():
    """Simple example of basic usage"""
    print("\n" + "="*60)
    print("Simple Usage Example")
    print("="*60 + "\n")
    
    # Create allocator
    allocator = DynamicResourceAllocator()
    
    # Start system
    print("Starting resource allocator...")
    allocator.start()
    
    # Let it run for a bit
    print("Running for 5 seconds...")
    time.sleep(5)
    
    # Get status
    status = allocator.get_system_status()
    print(f"\nSystem Status:")
    print(f"  CPU Usage: {status['system_metrics']['cpu_percent']:.1f}%")
    print(f"  Memory Usage: {status['system_metrics']['memory_percent']:.1f}%")
    print(f"  Running Programs: {status['tracked_programs']}")
    
    # Stop system
    allocator.stop()
    print("\nResource allocator stopped.\n")


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'simple':
        simple_usage_example()
    else:
        demo = ResourceAllocationDemo()
        demo.run_all_demos()
