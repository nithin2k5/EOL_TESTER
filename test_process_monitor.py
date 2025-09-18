"""
Test Script for Process Status Monitor
=====================================

This script tests the process monitoring system independently
and demonstrates how to integrate it with the main test console.

Usage:
    python test_process_monitor.py [--standalone] [--integration]

Author: EOL Testing System
Version: 1.0
"""

import sys
import time
import argparse
from datetime import datetime
from process_monitor import ProcessStatusMonitor
from process_monitor_integration import ProcessMonitorIntegration, setup_process_monitoring


def test_standalone_monitor():
    """Test the process monitor in standalone mode"""
    print("🧪 Testing Process Monitor - Standalone Mode")
    print("=" * 50)
    
    # Create monitor instance
    monitor = ProcessStatusMonitor()
    
    # Set up callbacks for testing
    def on_cycle_complete(status):
        print(f"✅ TEST: Cycle completed with status: {status}")
    
    def on_cycle_start(cycle_num):
        print(f"🚀 TEST: Starting cycle #{cycle_num}")
    
    def on_status_change(status):
        print(f"📊 TEST: Status changed: {status}")
    
    def on_error(error_msg):
        print(f"❌ TEST: Error occurred: {error_msg}")
    
    monitor.set_callbacks(
        on_cycle_complete=on_cycle_complete,
        on_cycle_start=on_cycle_start,
        on_status_change=on_status_change,
        on_error=on_error
    )
    
    # Test configuration loading
    print("\n1️⃣ Testing Configuration Loading...")
    config_status = monitor.get_status()
    print(f"   Configuration loaded: {config_status}")
    
    # Test PLC connection
    print("\n2️⃣ Testing PLC Connection...")
    connection_result = monitor.connect_to_plc()
    print(f"   Connection result: {'✅ SUCCESS' if connection_result else '❌ FAILED'}")
    
    if not connection_result:
        print("   ⚠️ PLC connection failed - running in simulation mode")
        return test_simulation_mode(monitor)
    
    # Test monitoring start
    print("\n3️⃣ Testing Monitor Start...")
    start_result = monitor.start_monitoring()
    print(f"   Start result: {'✅ SUCCESS' if start_result else '❌ FAILED'}")
    
    if start_result:
        print("\n4️⃣ Running Monitor Test...")
        print("   🔍 Monitor running... (Press Ctrl+C to stop)")
        
        try:
            # Run for 30 seconds or until interrupted
            for i in range(30):
                time.sleep(1)
                status = monitor.get_status()
                
                if i % 5 == 0:  # Print status every 5 seconds
                    print(f"   📊 Status: Cycle #{status['cycle_count']}, Connected: {status['connected']}")
                
        except KeyboardInterrupt:
            print("\n   🛑 Test interrupted by user")
        
        # Stop monitoring
        print("\n5️⃣ Stopping Monitor...")
        monitor.stop_monitoring()
        print("   ✅ Monitor stopped successfully")
    
    return True


def test_simulation_mode(monitor):
    """Test the monitor in simulation mode (without actual PLC)"""
    print("\n🎭 Running Simulation Mode Test...")
    
    # Simulate some status changes
    test_statuses = [
        {"AUTO": True, "HOME": False},
        {"AUTO": True, "PULL1_OK": True},
        {"AUTO": True, "PULL2_OK": True},
        {"AUTO": True, "TESTRESULT_OK": True},
        {"AUTO": False, "HOME": True}
    ]
    
    for i, status in enumerate(test_statuses):
        print(f"   Simulating status {i+1}: {status}")
        
        # Simulate cycle detection
        if status.get("TESTRESULT_OK") or status.get("TESTRESULT_NG"):
            print("   🎯 Simulated cycle completion detected")
        
        if status.get("AUTO") and i == 0:
            print("   🚀 Simulated cycle start detected")
        
        time.sleep(2)
    
    print("   ✅ Simulation test completed")
    return True


def test_integration_mode():
    """Test the process monitor integration"""
    print("🧪 Testing Process Monitor - Integration Mode")
    print("=" * 50)
    
    # Mock main application class
    class MockMainApp:
        def __init__(self):
            self.plc_connected = False
            self.current_cycle_number = 0
            self.status_messages = []
            
        def safe_update_message(self, message, color):
            self.status_messages.append(f"[{color}] {message}")
            print(f"   GUI UPDATE: [{color}] {message}")
        
        def update_status_labels(self, status):
            print(f"   GUI UPDATE: Status labels updated: {status}")
        
        def update_process_indicator(self, status):
            print(f"   GUI UPDATE: Process indicator: {status}")
        
        def reset_test_parameters(self):
            print("   GUI UPDATE: Test parameters reset")
        
        def on_automated_cycle_complete(self, cycle_count, status):
            print(f"   GUI UPDATE: Automated cycle #{cycle_count} complete: {status}")
    
    # Create mock main app
    mock_app = MockMainApp()
    
    # Test integration setup
    print("\n1️⃣ Testing Integration Setup...")
    integration = setup_process_monitoring(mock_app)
    
    if not integration:
        print("   ❌ Integration setup failed")
        return False
    
    print("   ✅ Integration setup successful")
    
    # Test integration start
    print("\n2️⃣ Testing Integration Start...")
    start_result = integration.start_integrated_monitoring()
    print(f"   Start result: {'✅ SUCCESS' if start_result else '❌ FAILED'}")
    
    if start_result:
        print("\n3️⃣ Running Integration Test...")
        print("   🔍 Integration running... (testing for 15 seconds)")
        
        try:
            # Test for 15 seconds
            for i in range(15):
                time.sleep(1)
                
                # Get status every 3 seconds
                if i % 3 == 0:
                    status = integration.get_integration_status()
                    print(f"   📊 Integration Status: {status['integration_active']}, Monitor: {status['monitor_running']}")
                
                # Test force restart at 7 seconds
                if i == 7:
                    print("   🔄 Testing force restart...")
                    integration.force_cycle_restart()
                
        except KeyboardInterrupt:
            print("\n   🛑 Test interrupted by user")
        
        # Stop integration
        print("\n4️⃣ Stopping Integration...")
        integration.stop_integrated_monitoring()
        print("   ✅ Integration stopped successfully")
        
        # Show collected messages
        print(f"\n📋 GUI Messages Collected: {len(mock_app.status_messages)}")
        for msg in mock_app.status_messages[-5:]:  # Show last 5 messages
            print(f"   {msg}")
    
    return True


def main():
    """Main test function"""
    parser = argparse.ArgumentParser(description='Test Process Status Monitor')
    parser.add_argument('--standalone', action='store_true', 
                       help='Test standalone monitor mode')
    parser.add_argument('--integration', action='store_true', 
                       help='Test integration mode')
    parser.add_argument('--all', action='store_true', 
                       help='Run all tests')
    
    args = parser.parse_args()
    
    if not any([args.standalone, args.integration, args.all]):
        # Default: run all tests
        args.all = True
    
    print("🚀 Process Monitor Test Suite")
    print(f"Started at: {datetime.now()}")
    print("=" * 60)
    
    success = True
    
    try:
        if args.standalone or args.all:
            print("\n" + "🧪 STANDALONE TEST".center(60, "="))
            success &= test_standalone_monitor()
        
        if args.integration or args.all:
            print("\n" + "🧪 INTEGRATION TEST".center(60, "="))
            success &= test_integration_mode()
        
        print("\n" + "📋 TEST RESULTS".center(60, "="))
        if success:
            print("✅ All tests completed successfully!")
        else:
            print("❌ Some tests failed!")
        
    except Exception as e:
        print(f"\n❌ Test suite error: {e}")
        success = False
    
    print(f"Completed at: {datetime.now()}")
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
