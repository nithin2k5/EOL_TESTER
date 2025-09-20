"""
Start Monitoring System
======================

This script starts the complete monitoring system with both the test console
and the process monitor running together. It provides a unified interface
for operating the EOL testing system with automated cycle management.

Usage:
    python start_monitoring_system.py [--monitor-only] [--console-only]

Features:
- Starts both test console and process monitor
- Handles communication between systems  
- Provides unified control interface
- Automatic error recovery
- Clean shutdown handling

Author: EOL Testing System
Version: 1.0
"""

import sys
import time
import threading
import argparse
import signal
from datetime import datetime
import tkinter as tk
from process_monitor import ProcessStatusMonitor
from process_monitor_integration import ProcessMonitorIntegration


class MonitoringSystemController:
    """
    Controls the complete monitoring system including test console and process monitor
    """
    
    def __init__(self):
        self.running = False
        self.test_console = None
        self.process_monitor = None
        self.monitor_integration = None
        
        # System status
        self.console_running = False
        self.monitor_running = False
        
        # Setup signal handlers for clean shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        print("🎛️ Monitoring System Controller initialized")
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        print(f"\n🛑 Received signal {signum}, shutting down...")
        self.shutdown()
        sys.exit(0)
    
    def start_test_console(self):
        """Start the test console GUI"""
        try:
            print("🖥️ Starting test console...")
            
            # Import and start test console
            from test_console import EOLTesterGUI
            
            # Create GUI in separate thread
            def run_console():
                try:
                    root = tk.Tk()
                    self.test_console = EOLTesterGUI(root)
                    self.console_running = True
                    
                    # Setup integration with process monitor
                    self.setup_console_integration()
                    
                    print("✅ Test console started successfully")
                    root.mainloop()
                    
                except Exception as e:
                    print(f"❌ Error in test console: {e}")
                finally:
                    self.console_running = False
            
            console_thread = threading.Thread(target=run_console, daemon=False)
            console_thread.start()
            
            # Wait a moment for console to initialize
            time.sleep(2)
            
            return True
            
        except Exception as e:
            print(f"❌ Error starting test console: {e}")
            return False
    
    def start_process_monitor(self):
        """Start the process status monitor"""
        try:
            print("📡 Starting process monitor...")
            
            self.process_monitor = ProcessStatusMonitor()
            
            # Setup callbacks
            self.process_monitor.set_callbacks(
                on_cycle_complete=self.on_cycle_complete,
                on_cycle_start=self.on_cycle_start,
                on_status_change=self.on_status_change,
                on_error=self.on_monitor_error
            )
            
            if self.process_monitor.start_monitoring():
                self.monitor_running = True
                print("✅ Process monitor started successfully")
                return True
            else:
                print("❌ Failed to start process monitor")
                return False
                
        except Exception as e:
            print(f"❌ Error starting process monitor: {e}")
            return False
    
    def setup_console_integration(self):
        """Setup integration between console and monitor"""
        try:
            if self.test_console and self.process_monitor:
                self.monitor_integration = ProcessMonitorIntegration(self.test_console)
                self.monitor_integration.monitor = self.process_monitor
                
                print("🔗 Console-Monitor integration established")
                return True
            else:
                print("⚠️ Cannot setup integration - missing components")
                return False
                
        except Exception as e:
            print(f"❌ Error setting up integration: {e}")
            return False
    
    def start_monitoring_system(self, console_enabled=True, monitor_enabled=True):
        """Start the complete monitoring system"""
        try:
            print("🚀 Starting Complete Monitoring System")
            print("=" * 50)
            
            self.running = True
            success = True
            
            # Start process monitor first
            if monitor_enabled:
                if not self.start_process_monitor():
                    success = False
                    print("❌ Process monitor failed to start")
            
            # Start test console
            if console_enabled:
                if not self.start_test_console():
                    success = False
                    print("❌ Test console failed to start")
            
            if success:
                print("\n✅ Monitoring System Started Successfully!")
                print("📋 System Status:")
                print(f"   Console: {'✅ Running' if self.console_running else '❌ Stopped'}")
                print(f"   Monitor: {'✅ Running' if self.monitor_running else '❌ Stopped'}")
                
                if console_enabled:
                    print("\n🎯 System is now running with automated cycle management")
                    print("   • Process monitor detects cycle completion automatically")
                    print("   • Cycles restart automatically after completion")
                    print("   • Status updates appear in test console")
                    print("   • Use test console GUI for manual control")
                
                return True
            else:
                print("❌ Failed to start monitoring system")
                return False
                
        except Exception as e:
            print(f"❌ Error starting monitoring system: {e}")
            return False
    
    def shutdown(self):
        """Shutdown the monitoring system"""
        try:
            print("🛑 Shutting down monitoring system...")
            
            self.running = False
            
            # Stop process monitor
            if self.process_monitor:
                self.process_monitor.stop_monitoring()
                print("✅ Process monitor stopped")
            
            # Stop integration
            if self.monitor_integration:
                self.monitor_integration.stop_integrated_monitoring()
                print("✅ Integration stopped")
            
            # Test console will close with main window
            print("✅ Monitoring system shutdown complete")
            
        except Exception as e:
            print(f"❌ Error during shutdown: {e}")
    
    def get_system_status(self):
        """Get current system status"""
        status = {
            'running': self.running,
            'console_running': self.console_running,
            'monitor_running': self.monitor_running,
            'timestamp': datetime.now().isoformat()
        }
        
        if self.process_monitor:
            status['monitor_status'] = self.process_monitor.get_status()
        
        if self.test_console:
            status['console_connected'] = getattr(self.test_console, 'plc_connected', False)
        
        return status
    
    def wait_for_shutdown(self):
        """Wait for system shutdown"""
        try:
            while self.running:
                time.sleep(1)
                
                # Check if console closed
                if not self.console_running and self.running:
                    print("🖥️ Console closed, shutting down system...")
                    self.shutdown()
                    break
                    
        except KeyboardInterrupt:
            print("\n🛑 Keyboard interrupt received")
            self.shutdown()
    
    # Event callbacks from process monitor
    def on_cycle_complete(self, status):
        """Handle cycle completion"""
        result = "PASS" if status.get("TESTRESULT_OK", False) else "FAIL"
        print(f"🎯 Cycle completed: {result}")
        
        # Update test console if available
        if self.test_console and hasattr(self.test_console, 'safe_update_message'):
            try:
                color = "green" if result == "PASS" else "red"
                self.test_console.root.after(0, 
                    lambda: self.test_console.safe_update_message(f"Auto Cycle: {result}", color))
            except:
                pass
    
    def on_cycle_start(self, cycle_num):
        """Handle cycle start"""
        print(f"🚀 Starting cycle #{cycle_num}")
        
        # Update test console if available
        if self.test_console and hasattr(self.test_console, 'safe_update_message'):
            try:
                self.test_console.root.after(0, 
                    lambda: self.test_console.safe_update_message(f"Starting Cycle #{cycle_num}", "blue"))
            except:
                pass
    
    def on_status_change(self, status):
        """Handle status changes"""
        print(f"📊 Status: {status}")
        
        # Update test console status if available
        if self.test_console and hasattr(self.test_console, 'update_status_labels'):
            try:
                self.test_console.root.after(0, 
                    lambda: self.test_console.update_status_labels(status))
            except:
                pass
    
    def on_monitor_error(self, error_msg):
        """Handle monitor errors"""
        print(f"❌ Monitor error: {error_msg}")
        
        # Update test console if available
        if self.test_console and hasattr(self.test_console, 'safe_update_message'):
            try:
                self.test_console.root.after(0, 
                    lambda: self.test_console.safe_update_message(f"Monitor Error: {error_msg}", "red"))
            except:
                pass


def print_system_info():
    """Print system information and instructions"""
    print("""
🎛️ EOL Testing Monitoring System
================================

This system provides automated cycle management for your EOL testing:

📡 Process Monitor:
   • Continuously monitors PLC status registers
   • Detects cycle completion automatically
   • Restarts cycles when testing is complete
   • Handles timeouts and error conditions

🖥️ Test Console:
   • Provides GUI interface for manual control
   • Displays real-time status updates
   • Shows automated cycle progress
   • Allows manual intervention when needed

🔗 Integration:
   • Seamless communication between components
   • Real-time status synchronization
   • Unified error handling and logging
   • Clean shutdown coordination

📋 How it works:
   1. Process monitor connects to PLC
   2. Monitor detects when AUTO mode starts (cycle begins)
   3. Monitor watches for TESTRESULT_OK/NG (cycle complete)
   4. After completion, monitor waits and restarts cycle
   5. Test console shows all status updates in real-time

🚀 Ready to start automated EOL testing!
""")


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='EOL Testing Monitoring System')
    parser.add_argument('--monitor-only', action='store_true', 
                       help='Start only the process monitor (no GUI)')
    parser.add_argument('--console-only', action='store_true', 
                       help='Start only the test console (no automated monitoring)')
    parser.add_argument('--info', action='store_true', 
                       help='Show system information and exit')
    
    args = parser.parse_args()
    
    if args.info:
        print_system_info()
        return 0
    
    # Determine what to start
    start_console = not args.monitor_only
    start_monitor = not args.console_only
    
    print_system_info()
    
    # Create and start system controller
    controller = MonitoringSystemController()
    
    try:
        if controller.start_monitoring_system(start_console, start_monitor):
            print("\n🔍 System running... Close test console window or press Ctrl+C to stop")
            
            if start_monitor and not start_console:
                # Monitor-only mode
                print("📡 Process monitor running in standalone mode")
                print("   Monitor will automatically manage testing cycles")
                print("   Press Ctrl+C to stop")
                
                try:
                    while controller.running:
                        time.sleep(1)
                except KeyboardInterrupt:
                    print("\n🛑 Stopping...")
            else:
                # Wait for shutdown
                controller.wait_for_shutdown()
        else:
            print("❌ Failed to start monitoring system")
            return 1
            
    except Exception as e:
        print(f"❌ System error: {e}")
        return 1
    finally:
        controller.shutdown()
    
    print("👋 Monitoring system stopped")
    return 0


if __name__ == "__main__":
    sys.exit(main())

