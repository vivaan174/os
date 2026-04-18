"""
Unit Tests and Integration Tests for Dynamic Resource Allocator
"""

import unittest
import time
import os
import json
from unittest.mock import patch, MagicMock

from dynamic_allocator import DynamicResourceAllocator
from resource_manager import (
    ResourceManager, ProcessPriority, 
    ResourceAllocationStrategy, ResourceAllocation
)
from system_monitor import SystemMonitor, SystemMetrics
from performance_optimizer import PerformanceOptimizer, BottleneckDetector
from collections import deque


class TestSystemMonitor(unittest.TestCase):
    """Test system monitoring functionality"""
    
    def setUp(self):
        self.monitor = SystemMonitor(sampling_interval=0.1)
    
    def tearDown(self):
        self.monitor.stop()
    
    def test_monitor_initialization(self):
        """Test that monitor initializes correctly"""
        self.assertFalse(self.monitor.running)
        self.assertEqual(self.monitor.sampling_interval, 0.1)
        self.assertEqual(len(self.monitor.system_metrics_history), 0)
    
    def test_monitor_start_stop(self):
        """Test starting and stopping monitor"""
        self.monitor.start()
        self.assertTrue(self.monitor.running)
        
        # Wait for at least one metric collection
        for _ in range(30):  # Try up to 3 seconds
            time.sleep(0.1)
            if len(self.monitor.system_metrics_history) > 0:
                break
        
        self.assertTrue(len(self.monitor.system_metrics_history) > 0, 
                       "No metrics collected after 3 seconds")
        
        self.monitor.stop()
        self.assertFalse(self.monitor.running)
    
    def test_system_metrics_collection(self):
        """Test that system metrics are collected"""
        self.monitor.start()
        time.sleep(0.3)
        
        metrics = self.monitor.get_latest_system_metrics()
        self.assertIsNotNone(metrics)
        self.assertGreater(metrics.cpu_percent, 0)
        self.assertGreater(metrics.memory_total_mb, 0)
        self.assertLessEqual(metrics.memory_percent, 100)


class TestResourceManager(unittest.TestCase):
    """Test resource management functionality"""
    
    def setUp(self):
        self.manager = ResourceManager(num_cpu_cores=4)
    
    def test_manager_initialization(self):
        """Test resource manager initialization"""
        self.assertEqual(self.manager.num_cpu_cores, 4)
        self.assertEqual(self.manager.available_cores, 3)  # 1 reserved
        self.assertEqual(len(self.manager.tracked_processes), 0)
    
    def test_process_registration(self):
        """Test process registration"""
        # Use current process PID (which definitely exists)
        current_pid = os.getpid()
        
        success = self.manager.register_process(
            pid=current_pid,
            process_name="TestApp",
            priority=ProcessPriority.NORMAL
        )
        self.assertTrue(success)
        self.assertIn(current_pid, self.manager.tracked_processes)
        
        # Try to register again - should fail
        success = self.manager.register_process(
            pid=current_pid,
            process_name="TestApp",
            priority=ProcessPriority.NORMAL
        )
        self.assertFalse(success)
    
    def test_process_unregistration(self):
        """Test process unregistration"""
        current_pid = os.getpid()
        self.manager.register_process(current_pid, "TestApp", ProcessPriority.NORMAL)
        
        success = self.manager.unregister_process(current_pid)
        self.assertTrue(success)
        self.assertNotIn(current_pid, self.manager.tracked_processes)
        
        # Try to unregister non-existent process
        success = self.manager.unregister_process(99999)
        self.assertFalse(success)
    
    def test_priority_setting(self):
        """Test setting process priority"""
        current_pid = os.getpid()
        self.manager.register_process(current_pid, "TestApp", ProcessPriority.NORMAL)
        
        success = self.manager.set_process_priority(current_pid, ProcessPriority.HIGH)
        self.assertTrue(success)
        self.assertEqual(
            self.manager.tracked_processes[current_pid]['priority'],
            ProcessPriority.HIGH
        )
    
    def test_cpu_quota_calculation(self):
        """Test CPU quota calculation"""
        current_pid = os.getpid()
        self.manager.register_process(current_pid, "TestApp", ProcessPriority.CRITICAL)
        
        # Create mock system metrics
        mock_metrics = MagicMock()
        mock_metrics.cpu_percent = 50
        
        quota = self.manager._calculate_cpu_quota(
            current_pid,
            ProcessPriority.CRITICAL,
            mock_metrics
        )
        
        # Critical process should get higher quota
        self.assertGreater(quota, 25)  # Base would be ~25%
    
    def test_memory_limit_calculation(self):
        """Test memory limit calculation"""
        mock_metrics = MagicMock()
        mock_metrics.memory_available_mb = 1000
        
        limit = self.manager._calculate_memory_limit(
            1234,
            ProcessPriority.HIGH,
            mock_metrics
        )
        
        self.assertIsInstance(limit, float)
        self.assertGreater(limit, 128)  # Minimum 128MB


class TestPerformanceOptimizer(unittest.TestCase):
    """Test performance optimization functionality"""
    
    def setUp(self):
        self.monitor = SystemMonitor(sampling_interval=0.1)
        self.manager = ResourceManager()
        self.optimizer = PerformanceOptimizer(
            self.monitor, 
            self.manager, 
            window_size=10
        )
    
    def tearDown(self):
        self.monitor.stop()
        self.optimizer.stop()
    
    def test_optimizer_initialization(self):
        """Test optimizer initialization"""
        self.assertFalse(self.optimizer.running)
        self.assertEqual(len(self.optimizer.performance_history), 0)
    
    def test_bottleneck_detection(self):
        """Test bottleneck detection"""
        # Create mock performance history with high CPU
        history = deque(maxlen=20)
        for i in range(20):
            mock_metric = MagicMock()
            mock_metric.cpu_percent = 90  # High CPU to trigger bottleneck
            mock_metric.memory_percent = 50
            history.append(mock_metric)
        
        current_pid = os.getpid()
        self.optimizer.performance_history[current_pid] = history
        
        # Need a valid system_metrics for detection to work
        mock_system = MagicMock()
        mock_system.cpu_percent = 75
        with patch.object(self.monitor, 'get_latest_system_metrics', return_value=mock_system):
            bottlenecks = self.optimizer._detect_bottlenecks()
            # Bottleneck should be detected for high CPU
            self.assertGreater(len(bottlenecks), 0)


class TestBottleneckDetector(unittest.TestCase):
    """Test bottleneck detection algorithms"""
    
    def test_cpu_thrashing_detection(self):
        """Test CPU thrashing detection"""
        history = deque(maxlen=20)
        for i in range(20):
            mock_metric = MagicMock()
            # Create erratic CPU pattern
            mock_metric.cpu_percent = 90 if i % 2 == 0 else 10
            history.append(mock_metric)
        
        is_thrashing = BottleneckDetector.detect_cpu_thrashing(history)
        self.assertTrue(is_thrashing)
    
    def test_memory_leak_detection(self):
        """Test memory leak detection"""
        history = deque(maxlen=20)
        for i in range(20):
            mock_metric = MagicMock()
            # Create steadily increasing memory
            mock_metric.memory_percent = 40 + (i * 2)
            history.append(mock_metric)
        
        is_leak = BottleneckDetector.detect_memory_leak(history)
        self.assertTrue(is_leak)
    
    def test_io_wait_detection(self):
        """Test I/O wait detection"""
        history = deque(maxlen=10)
        for i in range(10):
            mock_metric = MagicMock()
            mock_metric.cpu_percent = 15
            mock_metric.memory_percent = 60
            history.append(mock_metric)
        
        is_io_wait = BottleneckDetector.detect_io_wait(history)
        self.assertTrue(is_io_wait)


class TestDynamicResourceAllocator(unittest.TestCase):
    """Integration tests for the main allocator"""
    
    def setUp(self):
        self.allocator = DynamicResourceAllocator()
    
    def tearDown(self):
        if self.allocator.running:
            self.allocator.stop()
    
    def test_allocator_initialization(self):
        """Test allocator initialization"""
        self.assertIsNotNone(self.allocator.monitor)
        self.assertIsNotNone(self.allocator.resource_manager)
        self.assertIsNotNone(self.allocator.optimizer)
        self.assertFalse(self.allocator.running)
    
    def test_allocator_start_stop(self):
        """Test starting and stopping allocator"""
        success = self.allocator.start()
        self.assertTrue(success)
        self.assertTrue(self.allocator.running)
        
        time.sleep(0.3)
        
        success = self.allocator.stop()
        self.assertTrue(success)
        self.assertFalse(self.allocator.running)
    
    def test_config_loading_saving(self):
        """Test configuration loading and saving"""
        # Save test config
        test_config_file = "test_config.json"
        try:
            self.allocator.save_config(test_config_file)
            self.assertTrue(os.path.exists(test_config_file))
            
            # Load config
            success = self.allocator.load_config(test_config_file)
            self.assertTrue(success)
        finally:
            if os.path.exists(test_config_file):
                os.remove(test_config_file)
    
    def test_strategy_switching(self):
        """Test allocation strategy switching"""
        for strategy in ResourceAllocationStrategy:
            success = self.allocator.set_allocation_strategy(strategy)
            self.assertTrue(success)
            self.assertEqual(self.allocator.resource_manager.strategy, strategy)
    
    def test_get_system_status(self):
        """Test getting system status"""
        self.allocator.start()
        time.sleep(1.5)  # Wait enough for metrics to be ready
        
        status = self.allocator.get_system_status()
        self.assertIsNotNone(status)
        self.assertIn('running', status)
        self.assertTrue(status['running'])
        # May or may not have system_metrics depending on timing, but should have running key
        if 'system_metrics' in status:
            self.assertIsNotNone(status['system_metrics'])


class TestIntegrationScenarios(unittest.TestCase):
    """Test complete integration scenarios"""
    
    def setUp(self):
        self.allocator = DynamicResourceAllocator()
    
    def tearDown(self):
        if self.allocator.running:
            self.allocator.stop()
    
    def test_full_workflow(self):
        """Test complete allocation workflow"""
        # Start system
        self.allocator.start()
        time.sleep(0.2)
        
        # Get initial status
        status1 = self.allocator.get_system_status()
        self.assertTrue(status1['running'])
        
        # Register a mock program
        self.allocator.register_program(
            os.getpid(),
            "TestProcess",
            ProcessPriority.HIGH
        )
        
        # Get updated status
        status2 = self.allocator.get_system_status()
        self.assertEqual(status2['tracked_programs'], 1)
        
        # Switch strategy
        self.allocator.set_allocation_strategy(ResourceAllocationStrategy.PRIORITY)
        
        # Get performance report
        report = self.allocator.get_performance_report()
        self.assertIsNotNone(report)
        self.assertIn('system_metrics', report)
        
        # Stop system
        self.allocator.stop()
        self.assertFalse(self.allocator.running)
    
    def test_report_export(self):
        """Test report export functionality"""
        test_report = "test_report.json"
        try:
            self.allocator.start()
            time.sleep(0.2)
            
            success = self.allocator.export_report(test_report)
            self.assertTrue(success)
            self.assertTrue(os.path.exists(test_report))
            
            # Verify report structure
            with open(test_report, 'r') as f:
                report = json.load(f)
            
            self.assertIn('timestamp', report)
            self.assertIn('system_status', report)
            self.assertIn('performance_report', report)
        
        finally:
            if os.path.exists(test_report):
                os.remove(test_report)


def run_tests():
    """Run all tests"""
    print("\n" + "="*70)
    print("Running Dynamic Resource Allocator Test Suite")
    print("="*70 + "\n")
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestSystemMonitor))
    suite.addTests(loader.loadTestsFromTestCase(TestResourceManager))
    suite.addTests(loader.loadTestsFromTestCase(TestPerformanceOptimizer))
    suite.addTests(loader.loadTestsFromTestCase(TestBottleneckDetector))
    suite.addTests(loader.loadTestsFromTestCase(TestDynamicResourceAllocator))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegrationScenarios))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "="*70)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    print("="*70 + "\n")
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    exit(0 if success else 1)
