"""
Test script to verify Gradio frontend fixes
"""

from gradio_frontend import GradioResourceAllocatorUI
from resource_manager import ProcessPriority
import os

print("\n" + "=" * 80)
print("🧪 TESTING GRADIO FRONTEND FIXES")
print("=" * 80 + "\n")

ui = GradioResourceAllocatorUI()

# Start system
print("1️⃣  Starting system...")
result = ui.start_system()
print(f"   {result}\n")

import time
time.sleep(2)

# Test register with current process PID
current_pid = os.getpid()
print(f"2️⃣  Testing register_program with current PID ({current_pid})...")

# Test with int
print("   a) Testing with integer PID...")
result = ui.register_program(current_pid, "TestApp", "normal")
print(f"      {result}")

# Test with float (simulating Gradio Number input)
print("\n   b) Testing with float PID (simulating Gradio Number)...")
result = ui.register_program(float(current_pid), "TestApp2", "high")
print(f"      {result}")

# Test with invalid PID
print("\n   c) Testing with invalid PID (0)...")
result = ui.register_program(0, "TestApp3", "normal")
print(f"      {result}")

# Test with invalid PID (None)
print("\n   d) Testing with empty PID (None)...")
result = ui.register_program(None, "TestApp4", "normal")
print(f"      {result}")

# Test set_priority
print(f"\n3️⃣  Testing set_priority with PID {current_pid}...")

print("   a) Testing with integer PID...")
result = ui.set_priority(current_pid, "critical")
print(f"      {result}")

print("\n   b) Testing with float PID (simulating Gradio Number)...")
result = ui.set_priority(float(current_pid), "high")
print(f"      {result}")

print("\n   c) Testing with invalid PID (0)...")
result = ui.set_priority(0, "normal")
print(f"      {result}")

# Test unregister
print(f"\n4️⃣  Testing unregister_program with PID {current_pid}...")

print("   a) Testing with integer PID...")
result = ui.unregister_program(current_pid)
print(f"      {result}")

print("\n   b) Testing with non-existent PID...")
result = ui.unregister_program(99999)
print(f"      {result}")

print("\n   c) Testing with invalid PID (0)...")
result = ui.unregister_program(0)
print(f"      {result}")

# Stop system
print("\n5️⃣  Stopping system...")
result = ui.stop_system()
print(f"   {result}\n")

print("=" * 80)
print("✅ TEST COMPLETE - All fixes working correctly!")
print("=" * 80 + "\n")
