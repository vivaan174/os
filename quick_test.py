"""Quick sanity test for Dynamic Resource Allocator"""

import time
from dynamic_allocator import DynamicResourceAllocator
from resource_manager import ProcessPriority, ResourceAllocationStrategy

def test_basic_functionality():
    """Test basic system functionality"""
    print("\n" + "="*60)
    print("Quick Functionality Test")
    print("="*60 + "\n")
    
    try:
        # Test 1: Initialize
        print("1. Initializing allocator...", end=" ")
        allocator = DynamicResourceAllocator()
        print("✓")
        
        # Test 2: Start system
        print("2. Starting system...", end=" ")
        allocator.start()
        print("✓")
        
        # Test 3: Wait for metrics
        print("3. Collecting metrics (5s)...", end=" ")
        time.sleep(5)
        print("✓")
        
        # Test 4: Get status
        print("4. Getting system status...", end=" ")
        status = allocator.get_system_status()
        assert 'running' in status
        assert status['running'] == True
        print("✓")
        
        # Test 5: Register program
        print("5. Registering program...", end=" ")
        import os
        allocator.register_program(os.getpid(), "TestApp", ProcessPriority.NORMAL)
        print("✓")
        
        # Test 6: Change strategy
        print("6. Changing allocation strategy...", end=" ")
        allocator.set_allocation_strategy(ResourceAllocationStrategy.PRIORITY)
        print("✓")
        
        # Test 7: Get report
        print("7. Generating report...", end=" ")
        report = allocator.get_performance_report()
        assert 'system_metrics' in report
        print("✓")
        
        # Test 8: Export report
        print("8. Exporting report...", end=" ")
        allocator.export_report("test_quick.json")
        print("✓")
        
        # Test 9: Stop system
        print("9. Stopping system...", end=" ")
        allocator.stop()
        print("✓")
        
        print("\n" + "="*60)
        print("✓ All tests PASSED!")
        print("="*60 + "\n")
        return True
        
    except Exception as e:
        print(f"\n✗ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = test_basic_functionality()
    exit(0 if success else 1)
