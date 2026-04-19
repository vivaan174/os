"""
Gradio Frontend Demo Script
Tests and demonstrates the Gradio-based UI functionality
"""

import sys
import time
from gradio_frontend import GradioResourceAllocatorUI
from resource_manager import ProcessPriority, ResourceAllocationStrategy


def print_banner():
    """Print demo banner"""
    print("\n" + "=" * 80)
    print("🖥️  DYNAMIC RESOURCE ALLOCATOR - GRADIO FRONTEND DEMO")
    print("=" * 80 + "\n")


def demo_system_control():
    """Demonstrate system control"""
    print("1️⃣  SYSTEM CONTROL DEMO")
    print("-" * 80)
    
    ui = GradioResourceAllocatorUI()
    
    print("Starting system...")
    result = ui.start_system()
    print(f"  {result}\n")
    
    time.sleep(2)
    
    print("Getting system status...")
    status = ui.get_system_status()
    print(status)
    print()
    
    return ui


def demo_program_management(ui):
    """Demonstrate program management"""
    print("\n2️⃣  PROGRAM MANAGEMENT DEMO")
    print("-" * 80)
    
    current_pid = 12345  # Placeholder
    
    print(f"Attempting to register program (PID: {current_pid})...")
    result = ui.register_program(current_pid, "TestApp", "high")
    print(f"  {result}\n")
    
    print(f"Attempting to set priority (PID: {current_pid})...")
    result = ui.set_priority(current_pid, "critical")
    print(f"  {result}\n")


def demo_strategy_switching(ui):
    """Demonstrate strategy switching"""
    print("\n3️⃣  STRATEGY SWITCHING DEMO")
    print("-" * 80)
    
    strategies = ["equal", "priority", "performance", "demand"]
    
    for strategy in strategies:
        print(f"Switching to {strategy} strategy...")
        result = ui.change_strategy(strategy)
        print(f"  {result}")
        time.sleep(0.5)
    
    print()


def demo_reporting(ui):
    """Demonstrate reporting functionality"""
    print("\n4️⃣  REPORTING DEMO")
    print("-" * 80)
    
    print("Generating performance report...")
    report = ui.get_performance_report()
    print(report)
    print()


def demo_process_monitoring(ui):
    """Demonstrate process monitoring"""
    print("\n5️⃣  PROCESS MONITORING DEMO")
    print("-" * 80)
    
    print("Getting running processes...")
    processes = ui.get_running_processes()
    lines = processes.split('\n')[:10]  # Show first 10 lines
    print("\n".join(lines))
    print("  ... (showing first 10 processes)\n")


def demo_cleanup(ui):
    """Cleanup demo"""
    print("\n6️⃣  SYSTEM CLEANUP")
    print("-" * 80)
    
    print("Stopping system...")
    result = ui.stop_system()
    print(f"  {result}\n")


def show_interface_info():
    """Show information about the Gradio interface"""
    print("\n" + "=" * 80)
    print("📊 GRADIO INTERFACE OVERVIEW")
    print("=" * 80 + "\n")
    
    interface_info = """
    🎮 CONTROL PANEL
    ├─ System Control: Start/Stop the resource allocator
    ├─ Strategy Control: Select and apply allocation strategies
    │  └─ Strategies: Equal, Priority, Performance, Demand
    └─ Real-time feedback on all operations

    📊 SYSTEM MONITOR
    ├─ CPU Usage: Real-time percentage and core count
    ├─ Memory Usage: Current usage, total, and available
    ├─ Process Count: Active processes on system
    ├─ Uptime: System runtime
    └─ Allocation Strategy: Current strategy in use

    📋 PROGRAM MANAGEMENT
    ├─ Register Program: Add process by PID and priority
    ├─ Update Program: Change priority for tracked programs
    ├─ Unregister Program: Remove process from management
    └─ Priority Levels: Critical, High, Normal, Low, Background

    🎯 TRACKED PROGRAMS
    ├─ View all registered programs
    ├─ Display PID, name, and priority
    ├─ Show resource allocations:
    │  ├─ CPU Quota (%): Percentage of CPU cores
    │  └─ Memory Limit (MB): Maximum memory allocation
    └─ Real-time update on refresh

    🔍 SYSTEM PROCESSES
    ├─ List all running processes with:
    │  ├─ Process ID (PID)
    │  ├─ Process Name
    │  ├─ CPU Usage (%)
    │  └─ Memory Usage (%)
    ├─ Sortable by PID
    ├─ Top 50 most recent processes
    └─ Auto-refresh capability

    📈 REPORTS
    ├─ Performance Analysis:
    │  ├─ System metrics summary
    │  ├─ Historical data trends
    │  ├─ Metrics history (last 5 samples)
    │  └─ Optimization recommendations
    ├─ Export Functionality:
    │  ├─ JSON format export
    │  ├─ Customizable filename
    │  └─ Full report serialization
    └─ Data persistence

    ℹ️  ABOUT
    └─ Feature overview, strategies, and getting started guide

    🖥️  TECHNICAL FEATURES
    ├─ Real-time metrics collection every 1 second
    ├─ Dynamic optimization every 5 seconds
    ├─ Multi-threaded background monitoring
    ├─ Thread-safe resource allocation
    ├─ Comprehensive error handling
    ├─ Detailed logging on all operations
    ├─ JSON-based configuration
    ├─ Process priority adjustment via OS
    ├─ CPU affinity management
    ├─ Memory quota enforcement
    └─ Bottleneck detection and reporting

    🎨 USER INTERFACE
    ├─ Responsive web-based design
    ├─ Smooth Gradio theme
    ├─ Tab-based organization
    ├─ Real-time status updates
    ├─ Color-coded feedback (✅ ❌ ⚠️)
    ├─ Emoji indicators for clarity
    └─ Mobile-compatible layout

    📡 NETWORK
    ├─ Local Server: http://localhost:7860
    ├─ Network Access: 0.0.0.0:7860
    ├─ WebSocket-based real-time communication
    ├─ No external dependencies for networking
    └─ Automatic browser launch on startup

    """
    print(interface_info)


def main():
    """Run the demo"""
    print_banner()
    
    try:
        # Run system control demo
        ui = demo_system_control()
        
        # Wait for metrics to collect
        print("⏳ Collecting metrics (5 seconds)...")
        time.sleep(5)
        
        # Demonstrate other features
        demo_program_management(ui)
        demo_strategy_switching(ui)
        demo_reporting(ui)
        demo_process_monitoring(ui)
        demo_cleanup(ui)
        
        # Show interface info
        show_interface_info()
        
        print("\n" + "=" * 80)
        print("✅ DEMO COMPLETE!")
        print("=" * 80)
        print("\n📊 To launch the full Gradio interface, run:")
        print("   python gradio_frontend.py")
        print("\n🌐 Then open: http://localhost:7860 in your browser\n")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Demo interrupted by user")
        if 'ui' in locals():
            ui.stop_system()
    except Exception as e:
        print(f"\n❌ Error during demo: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
