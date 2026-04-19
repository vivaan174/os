"""
Quick System Startup Script
Starts the Dynamic Resource Allocator system
"""

from dynamic_allocator import DynamicResourceAllocator
import time

print("\n" + "=" * 80)
print("Starting Dynamic Resource Allocator System")
print("=" * 80 + "\n")

allocator = DynamicResourceAllocator()

print("Initializing system components...")
success = allocator.start()

if success:
    print("\n✅ System Started Successfully!\n")
    print("=" * 80)
    print("System Status:")
    print("=" * 80)
    
    # Get and display status
    status = allocator.get_system_status()
    
    print(f"Status: RUNNING")
    print(f"Uptime: {status['uptime_seconds']:.1f} seconds")
    print(f"Strategy: {status['allocation_strategy']}")
    print(f"Tracked Programs: {status.get('tracked_programs', 0)}\n")
    
    if 'system_metrics' in status:
        metrics = status['system_metrics']
        print("System Metrics:")
        print(f"  CPU Usage: {metrics['cpu_percent']:.1f}%")
        print(f"  Memory Usage: {metrics['memory_percent']:.1f}%")
        print(f"  Available Cores: {metrics['cpu_count']}")
        print(f"  Active Processes: {metrics['process_count']}\n")
    
    print("=" * 80)
    print("Web Interface Available:")
    print("  URL: http://localhost:7860")
    print("\nInstructions:")
    print("  1. Open a browser and go to http://localhost:7860")
    print("  2. Use the 'Control Panel' tab to manage the system")
    print("  3. Use 'Program Management' to register/unregister processes")
    print("  4. Monitor metrics in 'System Monitor' tab")
    print("  5. View reports in 'Reports' tab")
    print("\nSystem will keep running. Press Ctrl+C to stop.\n")
    print("=" * 80 + "\n")
    
    try:
        # Keep system running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\nShutting down system...")
        allocator.stop()
        print("System stopped.")
else:
    print("\n❌ Failed to start system!")
    print("Please check logs for details.\n")
