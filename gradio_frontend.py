"""
Gradio-based Web UI for Dynamic Resource Allocator
Provides interactive interface for system monitoring and resource management
"""

import gradio as gr
import threading
import time
import json
from datetime import datetime
from typing import Tuple, List, Dict
import os

from dynamic_allocator import DynamicResourceAllocator
from resource_manager import ProcessPriority, ResourceAllocationStrategy
import psutil


class GradioResourceAllocatorUI:
    """Gradio UI wrapper for Dynamic Resource Allocator"""
    
    def __init__(self):
        self.allocator = DynamicResourceAllocator()
        self.refresh_thread = None
        self.refresh_interval = 2.0
        self.should_refresh = False
        self.auto_refresh = False
        
    def start_system(self) -> str:
        """Start the resource allocator system"""
        if self.allocator.running:
            return "⚠️ System already running!"
        
        success = self.allocator.start()
        if success:
            self.auto_refresh = True
            return "✅ System started successfully!"
        else:
            return "❌ Failed to start system. Check logs."
    
    def stop_system(self) -> str:
        """Stop the resource allocator system"""
        if not self.allocator.running:
            return "⚠️ System not running!"
        
        self.auto_refresh = False
        success = self.allocator.stop()
        if success:
            return "✅ System stopped successfully!"
        else:
            return "❌ Failed to stop system."
    
    def get_system_status(self) -> str:
        """Get comprehensive system status"""
        try:
            status = self.allocator.get_system_status()
            
            status_text = "📊 SYSTEM STATUS\n"
            status_text += "=" * 50 + "\n"
            status_text += f"🔄 Running: {status['running']}\n"
            status_text += f"⏱️ Uptime: {status['uptime_seconds']:.1f} seconds\n"
            status_text += f"🎯 Strategy: {status['allocation_strategy']}\n"
            status_text += f"📋 Tracked Programs: {status.get('tracked_programs', 0)}\n"
            
            if 'system_metrics' in status:
                metrics = status['system_metrics']
                status_text += "\n📈 SYSTEM METRICS\n"
                status_text += "-" * 50 + "\n"
                status_text += f"CPU Usage: {metrics['cpu_percent']:.1f}%\n"
                status_text += f"Available CPU Cores: {metrics['cpu_count']}\n"
                status_text += f"Memory Usage: {metrics['memory_percent']:.1f}%\n"
                status_text += f"Memory Used: {metrics['memory_used_mb']:.0f} MB / {metrics['memory_total_mb']:.0f} MB\n"
                status_text += f"Available Memory: {metrics['memory_available_mb']:.0f} MB\n"
                status_text += f"Active Processes: {metrics['process_count']}\n"
                status_text += f"Timestamp: {metrics['timestamp']}\n"
            else:
                status_text += "\n⚠️ Waiting for first metrics collection...\n"
            
            if 'error' in status:
                status_text += f"\n⚠️ Note: {status['error']}\n"
            
            return status_text
            
        except Exception as e:
            return f"❌ Error getting status: {str(e)}"
    
    def register_program(self, program_pid: int, program_name: str, priority: str) -> str:
        """Register a program for management"""
        if not self.allocator.running:
            return "❌ System not running! Start the system first."
        
        if not program_pid:
            return "❌ Please enter a valid PID"
        
        if not program_name:
            program_name = f"Program_{program_pid}"
        
        try:
            priority_enum = ProcessPriority[priority.upper().replace(" ", "_")]
        except KeyError:
            return f"❌ Invalid priority: {priority}"
        
        try:
            # Verify process exists
            psutil.Process(program_pid)
            
            success = self.allocator.register_program(program_pid, program_name, priority_enum)
            if success:
                return f"✅ Registered: {program_name} (PID: {program_pid}) with priority: {priority}"
            else:
                return f"❌ Failed to register program"
        except psutil.NoSuchProcess:
            return f"❌ Process with PID {program_pid} not found"
        except Exception as e:
            return f"❌ Error: {str(e)}"
    
    def unregister_program(self, program_pid: int) -> str:
        """Unregister a program"""
        if not program_pid:
            return "❌ Please enter a valid PID"
        
        try:
            success = self.allocator.unregister_program(program_pid)
            if success:
                return f"✅ Unregistered program (PID: {program_pid})"
            else:
                return f"❌ Program PID {program_pid} not found"
        except Exception as e:
            return f"❌ Error: {str(e)}"
    
    def change_strategy(self, strategy: str) -> str:
        """Change the allocation strategy"""
        if not self.allocator.running:
            return "❌ System not running!"
        
        try:
            strategy_enum = ResourceAllocationStrategy[strategy.upper().replace(" ", "_")]
            success = self.allocator.set_allocation_strategy(strategy_enum)
            if success:
                return f"✅ Strategy changed to: {strategy}"
            else:
                return f"❌ Failed to change strategy"
        except KeyError:
            return f"❌ Invalid strategy: {strategy}"
        except Exception as e:
            return f"❌ Error: {str(e)}"
    
    def set_priority(self, program_pid: int, priority: str) -> str:
        """Change priority of a program"""
        if not program_pid:
            return "❌ Please enter a valid PID"
        
        try:
            priority_enum = ProcessPriority[priority.upper().replace(" ", "_")]
            success = self.allocator.set_program_priority(program_pid, priority_enum)
            if success:
                return f"✅ Priority updated for PID {program_pid} to: {priority}"
            else:
                return f"❌ Program PID {program_pid} not found"
        except KeyError:
            return f"❌ Invalid priority: {priority}"
        except Exception as e:
            return f"❌ Error: {str(e)}"
    
    def get_performance_report(self) -> str:
        """Get performance analysis report"""
        try:
            report = self.allocator.get_performance_report()
            
            report_text = "📈 PERFORMANCE REPORT\n"
            report_text += "=" * 60 + "\n"
            
            if 'summary' in report:
                summary = report['summary']
                report_text += "\n📊 SUMMARY\n"
                report_text += "-" * 60 + "\n"
                for key, value in summary.items():
                    report_text += f"{key}: {value}\n"
            
            if 'metrics_history' in report:
                metrics = report['metrics_history']
                report_text += "\n📉 RECENT METRICS\n"
                report_text += "-" * 60 + "\n"
                report_text += f"Samples collected: {len(metrics)}\n"
                if metrics:
                    avg_cpu = sum(m.get('cpu_percent', 0) for m in metrics) / len(metrics)
                    avg_mem = sum(m.get('memory_percent', 0) for m in metrics) / len(metrics)
                    report_text += f"Average CPU: {avg_cpu:.1f}%\n"
                    report_text += f"Average Memory: {avg_mem:.1f}%\n"
            
            if 'optimization_recommendations' in report:
                recs = report['optimization_recommendations']
                report_text += "\n💡 RECOMMENDATIONS\n"
                report_text += "-" * 60 + "\n"
                if recs:
                    for i, rec in enumerate(recs[:5], 1):
                        report_text += f"{i}. {rec}\n"
                else:
                    report_text += "System performing optimally\n"
            
            return report_text
            
        except Exception as e:
            return f"❌ Error generating report: {str(e)}"
    
    def export_report(self, filename: str = "resource_report.json") -> str:
        """Export performance report to JSON"""
        try:
            if not filename.endswith('.json'):
                filename += '.json'
            
            report = self.allocator.get_performance_report()
            
            # Convert to serializable format
            def convert_to_serializable(obj):
                if hasattr(obj, '__dict__'):
                    return obj.__dict__
                elif isinstance(obj, (list, tuple)):
                    return [convert_to_serializable(item) for item in obj]
                elif isinstance(obj, dict):
                    return {k: convert_to_serializable(v) for k, v in obj.items()}
                else:
                    return obj
            
            report = convert_to_serializable(report)
            
            filepath = filename
            with open(filepath, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            
            return f"✅ Report exported to: {filepath}"
        except Exception as e:
            return f"❌ Error exporting report: {str(e)}"
    
    def get_running_processes(self) -> str:
        """Get list of running processes"""
        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    info = proc.info
                    processes.append(f"PID: {info['pid']:6} | Name: {info['name'][:30]:30} | CPU: {info['cpu_percent']:6.1f}% | MEM: {info['memory_percent']:6.1f}%")
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            if not processes:
                return "No processes found"
            
            # Sort by PID and limit to 50 most recent
            processes = sorted(processes[:50])
            return "🔍 TOP RUNNING PROCESSES\n" + "=" * 80 + "\n" + "\n".join(processes)
        except Exception as e:
            return f"❌ Error: {str(e)}"
    
    def get_tracked_programs(self) -> str:
        """Get list of tracked programs"""
        try:
            tracked = self.allocator.resource_manager.tracked_processes
            
            if not tracked:
                return "No programs tracked yet"
            
            info = "📋 TRACKED PROGRAMS\n" + "=" * 60 + "\n"
            for pid, process_info in tracked.items():
                priority = process_info.get('priority', 'UNKNOWN')
                allocations = process_info.get('allocations', {})
                info += f"\nPID: {pid}\n"
                info += f"  Name: {process_info.get('name', 'Unknown')}\n"
                info += f"  Priority: {priority}\n"
                info += f"  CPU Quota: {allocations.get('cpu_quota', 0):.1f}%\n"
                info += f"  Memory Limit: {allocations.get('memory_limit_mb', 0):.0f} MB\n"
            
            return info
        except Exception as e:
            return f"❌ Error: {str(e)}"


def create_gradio_interface():
    """Create and return the Gradio interface"""
    ui = GradioResourceAllocatorUI()
    
    with gr.Blocks(title="Dynamic Resource Allocator", theme=gr.themes.Soft()) as interface:
        gr.Markdown(
            """
            # 🖥️ Dynamic Resource Allocator
            Real-time system resource monitoring and optimization platform
            """
        )
        
        with gr.Tabs():
            # ============= CONTROL TAB =============
            with gr.Tab("🎮 Control Panel"):
                with gr.Row():
                    with gr.Column():
                        gr.Markdown("### System Control")
                        start_btn = gr.Button("▶️ Start System", scale=1, size="lg", variant="primary")
                        stop_btn = gr.Button("⏹️ Stop System", scale=1, size="lg", variant="stop")
                        start_output = gr.Textbox(label="Status", lines=2, interactive=False)
                        stop_output = gr.Textbox(label="Status", lines=2, interactive=False)
                    
                    with gr.Column():
                        gr.Markdown("### Strategy Control")
                        strategy_input = gr.Dropdown(
                            choices=["equal", "priority", "performance", "demand"],
                            label="Select Strategy",
                            value="performance"
                        )
                        strategy_btn = gr.Button("🎯 Apply Strategy", size="lg", variant="primary")
                        strategy_output = gr.Textbox(label="Result", lines=2, interactive=False)
                
                start_btn.click(fn=ui.start_system, outputs=start_output)
                stop_btn.click(fn=ui.stop_system, outputs=stop_output)
                strategy_btn.click(fn=ui.change_strategy, inputs=strategy_input, outputs=strategy_output)
            
            # ============= MONITORING TAB =============
            with gr.Tab("📊 System Monitor"):
                status_btn = gr.Button("🔄 Refresh Status", size="lg", variant="primary")
                status_output = gr.Textbox(label="System Status", lines=15, interactive=False, max_lines=20)
                
                status_btn.click(fn=ui.get_system_status, outputs=status_output)
            
            # ============= PROGRAM MANAGEMENT TAB =============
            with gr.Tab("📋 Program Management"):
                with gr.Row():
                    with gr.Column():
                        gr.Markdown("### Register Program")
                        pid_input = gr.Number(label="Process ID (PID)", precision=0)
                        name_input = gr.Textbox(label="Program Name (optional)")
                        priority_input = gr.Dropdown(
                            choices=["critical", "high", "normal", "low", "background"],
                            label="Priority",
                            value="normal"
                        )
                        register_btn = gr.Button("➕ Register", size="lg", variant="primary")
                        register_output = gr.Textbox(label="Result", lines=2, interactive=False)
                    
                    with gr.Column():
                        gr.Markdown("### Update Program")
                        update_pid_input = gr.Number(label="Process ID (PID)", precision=0)
                        new_priority_input = gr.Dropdown(
                            choices=["critical", "high", "normal", "low", "background"],
                            label="New Priority",
                            value="normal"
                        )
                        priority_btn = gr.Button("🔄 Update Priority", size="lg", variant="primary")
                        priority_output = gr.Textbox(label="Result", lines=2, interactive=False)
                
                with gr.Row():
                    gr.Markdown("### Unregister Program")
                    unreg_pid_input = gr.Number(label="Process ID (PID)", precision=0)
                    unreg_btn = gr.Button("❌ Unregister", size="lg", variant="stop")
                    unreg_output = gr.Textbox(label="Result", lines=2, interactive=False)
                
                register_btn.click(fn=ui.register_program, inputs=[pid_input, name_input, priority_input], outputs=register_output)
                priority_btn.click(fn=ui.set_priority, inputs=[update_pid_input, new_priority_input], outputs=priority_output)
                unreg_btn.click(fn=ui.unregister_program, inputs=unreg_pid_input, outputs=unreg_output)
            
            # ============= TRACKING TAB =============
            with gr.Tab("🎯 Tracked Programs"):
                tracked_btn = gr.Button("🔄 Refresh", size="lg", variant="primary")
                tracked_output = gr.Textbox(label="Tracked Programs", lines=20, interactive=False, max_lines=30)
                tracked_btn.click(fn=ui.get_tracked_programs, outputs=tracked_output)
            
            # ============= PROCESSES TAB =============
            with gr.Tab("🔍 System Processes"):
                processes_btn = gr.Button("🔄 Refresh", size="lg", variant="primary")
                processes_output = gr.Textbox(label="Running Processes", lines=25, interactive=False, max_lines=50)
                processes_btn.click(fn=ui.get_running_processes, outputs=processes_output)
            
            # ============= REPORTING TAB =============
            with gr.Tab("📈 Reports"):
                with gr.Row():
                    report_btn = gr.Button("📊 Generate Report", size="lg", variant="primary")
                    export_btn = gr.Button("💾 Export Report", size="lg", variant="primary")
                
                report_filename = gr.Textbox(
                    label="Export Filename",
                    value="resource_report.json",
                    visible=True
                )
                
                report_output = gr.Textbox(label="Performance Report", lines=20, interactive=False, max_lines=30)
                export_output = gr.Textbox(label="Export Status", lines=2, interactive=False)
                
                report_btn.click(fn=ui.get_performance_report, outputs=report_output)
                export_btn.click(fn=ui.export_report, inputs=report_filename, outputs=export_output)
            
            # ============= ABOUT TAB =============
            with gr.Tab("ℹ️ About"):
                gr.Markdown(
                    """
                    ## Dynamic Resource Allocator
                    
                    A comprehensive system for real-time resource monitoring and optimization.
                    
                    ### Features
                    - 🔴 **Real-time Monitoring**: Continuous CPU and memory tracking
                    - ⚙️ **Dynamic Allocation**: Automatic resource redistribution
                    - 👥 **Multi-Program Management**: Support for multiple processes
                    - 📊 **Performance Analytics**: Detailed reporting and analysis
                    - 🎯 **Strategy Selection**: Multiple allocation strategies
                    - 💾 **Report Export**: JSON export functionality
                    
                    ### Allocation Strategies
                    1. **Equal**: Distribute resources equally among programs
                    2. **Priority**: Based on program priority levels
                    3. **Performance**: Optimize for system throughput
                    4. **Demand**: Based on actual resource demand
                    
                    ### Priority Levels
                    - **Critical**: Maximum resources
                    - **High**: Above-average resources
                    - **Normal**: Standard allocation
                    - **Low**: Below-average resources
                    - **Background**: Minimal resources
                    
                    ### Getting Started
                    1. Click "Start System" to initialize
                    2. Register programs you want to manage
                    3. Monitor system status in real-time
                    4. Adjust strategies and priorities as needed
                    5. Export reports for analysis
                    """
                )
    
    return interface


if __name__ == "__main__":
    print("Starting Dynamic Resource Allocator Web Interface...")
    print("Launching Gradio on http://localhost:7860")
    
    interface = create_gradio_interface()
    interface.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True,
        debug=False
    )
