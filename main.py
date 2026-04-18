"""
Enhanced Main Entry Point for Dynamic Resource Allocator
Integrates system monitoring, resource management, and workload simulation
"""

import argparse
import json
import logging
import multiprocessing
import os
import signal
import sys
import time
from datetime import datetime

from dynamic_allocator import DynamicResourceAllocator
from resource_manager import ProcessPriority, ResourceAllocationStrategy
from workload_simulator import start_simulator

LOG = logging.getLogger(__name__)


def configure_logging() -> None:
    """Configure logging for both console and file output"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)-8s] %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('dynamic_allocator_main.log')
        ],
    )


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(
        description="Dynamic Resource Allocator - Optimizes CPU and memory allocation across programs.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --monitor-only
  python main.py --simulate --cpu-processes 3 --memory-processes 2 --duration 120
  python main.py --config custom_config.json --interactive
  python main.py --simulate --export-report report.json
        """
    )
    
    # Core options
    parser.add_argument(
        "--monitor-only",
        action="store_true",
        help="Run in monitoring-only mode (no resource allocation)"
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Run interactive command-line interface"
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=0,
        help="Run duration in seconds (0 = infinite)"
    )
    
    # Configuration
    parser.add_argument(
        "--config",
        type=str,
        default="config.json",
        help="Path to configuration file"
    )
    parser.add_argument(
        "--save-config",
        type=str,
        help="Save current configuration to file after initialization"
    )
    
    # Allocation settings
    parser.add_argument(
        "--strategy",
        type=str,
        choices=["equal", "priority", "performance", "demand"],
        default="performance",
        help="Resource allocation strategy"
    )
    parser.add_argument(
        "--cpu-threshold",
        type=float,
        default=80.0,
        help="CPU usage threshold for warnings (%)"
    )
    parser.add_argument(
        "--mem-threshold",
        type=float,
        default=85.0,
        help="Memory usage threshold for warnings (%)"
    )
    
    # Simulation options
    parser.add_argument(
        "--simulate",
        action="store_true",
        help="Start workload simulator"
    )
    parser.add_argument(
        "--cpu-processes",
        type=int,
        default=2,
        help="Number of CPU-bound simulator processes"
    )
    parser.add_argument(
        "--memory-processes",
        type=int,
        default=2,
        help="Number of memory-bound simulator processes"
    )
    parser.add_argument(
        "--sim-duration",
        type=int,
        default=60,
        help="Duration of simulated workload (seconds)"
    )
    
    # Reporting
    parser.add_argument(
        "--export-report",
        type=str,
        help="Export performance report to JSON file on exit"
    )
    parser.add_argument(
        "--report-interval",
        type=int,
        default=0,
        help="Generate reports every N seconds (0 = disabled)"
    )
    
    # Monitoring
    parser.add_argument(
        "--monitor-interval",
        type=float,
        default=1.0,
        help="System monitoring interval (seconds)"
    )
    parser.add_argument(
        "--optimize-interval",
        type=float,
        default=5.0,
        help="Optimization check interval (seconds)"
    )
    
    return parser.parse_args()


def create_and_configure_allocator(args: argparse.Namespace) -> DynamicResourceAllocator:
    """Create and configure the resource allocator"""
    allocator = DynamicResourceAllocator()
    
    # Load configuration if it exists
    if os.path.exists(args.config):
        LOG.info(f"Loading configuration from: {args.config}")
        allocator.load_config(args.config)
    
    # Apply command-line overrides
    allocator.config['cpu_threshold_high'] = args.cpu_threshold
    allocator.config['memory_threshold_high'] = args.mem_threshold
    allocator.monitor.sampling_interval = args.monitor_interval
    allocator.optimizer.optimization_interval = args.optimize_interval
    
    # Set allocation strategy
    strategy = ResourceAllocationStrategy[args.strategy.upper()]
    allocator.set_allocation_strategy(strategy)
    
    # Save configuration if requested
    if args.save_config:
        allocator.save_config(args.save_config)
        LOG.info(f"Configuration saved to: {args.save_config}")
    
    return allocator


def monitor_and_report(allocator: DynamicResourceAllocator, 
                       report_interval: int, 
                       end_time: float):
    """Background thread for periodic reporting"""
    while time.time() < end_time or end_time == 0:
        if report_interval > 0:
            time.sleep(report_interval)
            status = allocator.get_system_status()
            report = allocator.get_performance_report()
            
            metrics = status['system_metrics']
            LOG.info(
                f"System Status - CPU: {metrics['cpu_percent']:.1f}%, "
                f"Memory: {metrics['memory_percent']:.1f}%, "
                f"Processes: {metrics['process_count']}"
            )
        else:
            time.sleep(10)
        
        if time.time() >= end_time and end_time != 0:
            break


def main() -> None:
    """Main entry point"""
    configure_logging()
    args = parse_args()
    
    LOG.info("="*70)
    LOG.info("Dynamic Resource Allocator System Starting")
    LOG.info("="*70)
    
    # Create allocator
    allocator = create_and_configure_allocator(args)
    
    # Start simulator if requested
    simulator_process = None
    if args.simulate:
        LOG.info(f"Starting workload simulator with {args.cpu_processes} CPU and "
                f"{args.memory_processes} memory processes")
        simulator_process = multiprocessing.Process(
            target=start_simulator,
            args=(args.cpu_processes, args.memory_processes, args.sim_duration),
        )
        simulator_process.start()
        LOG.info(f"Simulator process started (PID: {simulator_process.pid})")
        time.sleep(2)
    
    try:
        # Start the allocator
        if not allocator.start():
            LOG.error("Failed to start allocator")
            return
        
        LOG.info(f"Allocation strategy: {allocator.resource_manager.strategy.value}")
        LOG.info(f"CPU Cores available: {allocator.resource_manager.available_cores}")
        LOG.info(f"Monitoring interval: {allocator.monitor.sampling_interval}s")
        LOG.info(f"Optimization interval: {allocator.optimizer.optimization_interval}s")
        
        # Run in interactive mode
        if args.interactive:
            LOG.info("Entering interactive mode...")
            allocator.run_interactive_mode()
        
        # Run for specified duration
        else:
            start_time = time.time()
            end_time = start_time + args.duration if args.duration > 0 else float('inf')
            
            LOG.info(f"Running for {args.duration if args.duration > 0 else 'infinite'} seconds...")
            
            # Start reporting thread if needed
            if args.report_interval > 0:
                report_thread = multiprocessing.Process(
                    target=monitor_and_report,
                    args=(allocator, args.report_interval, end_time),
                )
                report_thread.daemon = True
                report_thread.start()
            
            # Main loop
            while time.time() < end_time:
                try:
                    status = allocator.get_system_status()
                    
                    # Skip if metrics not ready yet
                    if 'error' in status or 'system_metrics' not in status:
                        time.sleep(1)
                        continue
                    
                    metrics = status['system_metrics']
                    
                    # Check thresholds
                    if metrics['cpu_percent'] > args.cpu_threshold:
                        LOG.warning(
                            f"CPU usage high: {metrics['cpu_percent']:.1f}% "
                            f"(threshold: {args.cpu_threshold}%)"
                        )
                    
                    if metrics['memory_percent'] > args.mem_threshold:
                        LOG.warning(
                            f"Memory usage high: {metrics['memory_percent']:.1f}% "
                            f"(threshold: {args.mem_threshold}%)"
                        )
                    
                    time.sleep(5)
                    
                except KeyboardInterrupt:
                    LOG.info("Interrupted by user")
                    break
    
    except KeyboardInterrupt:
        LOG.info("Interrupted by user, shutting down...")
    
    except Exception as e:
        LOG.error(f"Unexpected error: {e}", exc_info=True)
    
    finally:
        # Export report if requested
        if args.export_report:
            LOG.info(f"Exporting report to: {args.export_report}")
            if allocator.export_report(args.export_report):
                LOG.info("Report exported successfully")
            else:
                LOG.error("Failed to export report")
        
        # Stop allocator
        LOG.info("Stopping allocator...")
        allocator.stop()
        
        # Terminate simulator if running
        if simulator_process is not None and simulator_process.is_alive():
            LOG.info("Terminating simulator process...")
            simulator_process.terminate()
            simulator_process.join(timeout=5)
            if simulator_process.is_alive():
                simulator_process.kill()
            LOG.info("Simulator process terminated")
        
        # Final status
        final_status = allocator.get_system_status()
        LOG.info(f"Uptime: {final_status['uptime_seconds']:.1f} seconds")
        LOG.info("="*70)
        LOG.info("Dynamic Resource Allocator System Stopped")
        LOG.info("="*70)


if __name__ == "__main__":
    main()
