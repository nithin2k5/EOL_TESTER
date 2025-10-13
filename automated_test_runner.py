#!/usr/bin/env python3
"""
Automated EOL Test Runner - Bypasses Manual Validations
Runs EOL tests continuously with automatic setup
"""

import tkinter as tk
import time
import threading
from test_console_clone import EOLTesterGUI

class AutomatedTestRunner:
    def __init__(self):
        self.root = None
        self.app = None
        self.running = False
        self.test_count = 0
        self.start_time = time.time()

    def setup_automated_validation(self):
        """Automatically set up required validations for testing"""
        try:
            print("🔧 Setting up automated validations...")

            # Enable all controls (bypass employee validation lock)
            if hasattr(self.app, 'enable_all_controls'):
                self.app.enable_all_controls()
                print("✅ All controls enabled for automated testing")

            return True

        except Exception as e:
            print(f"❌ Error setting up automated validation: {e}")
            return False

    def start_automated_testing(self):
        """Start the automated test loop"""
        try:
            print("🚀 Starting Automated EOL Test Runner")
            print("=" * 60)

            # Create Tkinter root
            self.root = tk.Tk()

            # Initialize the EOL Tester application
            self.app = EOLTesterGUI(self.root)

            # Set running flag
            self.running = True

            # Start automated setup after GUI initialization
            self.root.after(3000, self.initialize_automated_workflow)

            # Start monitoring thread
            monitor_thread = threading.Thread(target=self.monitor_tests, daemon=True)
            monitor_thread.start()

            # Start the GUI main loop
            self.root.mainloop()

        except KeyboardInterrupt:
            print("\n🛑 Automated testing interrupted by user")
            self.stop_testing()
        except Exception as e:
            print(f"❌ Error in automated testing: {e}")
            self.stop_testing()

    def initialize_automated_workflow(self):
        """Initialize automated workflow with bypassed validations"""
        try:
            print("🔧 Initializing automated workflow...")
            self.test_count += 1
            print(f"📊 Test Cycle #{self.test_count}")

            # Set up automated validations
            if not self.setup_automated_validation():
                print("❌ Failed to set up automated validations")
                self.stop_testing()
                return

            # Wait a moment for validations to take effect
            time.sleep(1)

            # Execute the complete EOL workflow in automated mode
            print("🚀 Starting EOL Workflow...")
            success = self.app.execute_complete_eol_workflow(automated_mode=True)

            if success:
                print("✅ Automated EOL workflow started successfully!")
                print("🎯 System will run automated cycles continuously")
                print("💡 Press Ctrl+C to stop automated testing")
                print("=" * 60)
            else:
                print("❌ Failed to start automated workflow")
                self.stop_testing()

        except Exception as e:
            print(f"❌ Error initializing automated workflow: {e}")
            self.stop_testing()

    def monitor_tests(self):
        """Monitor the testing process and provide status updates"""
        cycle_start_time = time.time()

        while self.running:
            try:
                current_time = time.time()
                elapsed_total = current_time - self.start_time
                elapsed_cycle = current_time - cycle_start_time

                # Print status every 30 seconds
                if int(elapsed_cycle) % 30 == 0 and int(elapsed_cycle) > 0:
                    hours, remainder = divmod(int(elapsed_total), 3600)
                    minutes, seconds = divmod(remainder, 60)

                    print("📈 Automated Testing Status:")
                    print(f"   • Total Tests: {self.test_count}")
                    print(f"   • Runtime: {hours:02d}:{minutes:02d}:{seconds:02d}")
                    print(f"   • Process Status: {getattr(self.app, 'process_status', 'UNKNOWN')}")
                    print(f"   • Employee: {getattr(self.app, 'current_employee_id', 'N/A')}")
                    print(f"   • Part Number: {getattr(self.app, 'current_part_number', 'N/A')}")
                    print(f"   • Continuous Active: {getattr(self.app, 'continuous_testing_active', False)}")
                    print("-" * 50)

                time.sleep(1)  # Check every second

            except Exception as e:
                print(f"⚠️  Monitoring error: {e}")
                time.sleep(5)  # Wait longer on error

    def restart_test_cycle(self):
        """Restart a new test cycle"""
        try:
            if self.running:
                print(f"\n🔄 Starting Test Cycle #{self.test_count + 1}")
                self.test_count += 1

                # Wait a moment then restart workflow
                if self.root:
                    self.root.after(1000, self.initialize_automated_workflow)

        except Exception as e:
            print(f"❌ Error restarting test cycle: {e}")

    def stop_testing(self):
        """Stop the automated testing"""
        print("\n🛑 Stopping Automated EOL Testing...")
        self.running = False

        if self.app:
            # Stop the testing process
            self.app.stop_eol_testing_process()

        if self.root:
            try:
                self.root.quit()
                self.root.destroy()
            except:
                pass

        # Print final statistics
        total_time = time.time() - self.start_time
        hours, remainder = divmod(int(total_time), 3600)
        minutes, seconds = divmod(remainder, 60)

        print("📊 Final Automated Test Statistics:")
        print(f"   • Total Test Cycles: {self.test_count}")
        print(f"   • Total Runtime: {hours:02d}:{minutes:02d}:{seconds:02d}")
        print("=" * 60)
        print("✅ Automated testing stopped")

def main():
    """Main function to run automated tests"""
    print("🤖 EOL Automated Test Runner")
    print("This will run EOL tests automatically with bypassed validations")
    print("Press Ctrl+C to stop\n")

    # Create and start the automated test runner
    runner = AutomatedTestRunner()

    try:
        runner.start_automated_testing()
    except KeyboardInterrupt:
        runner.stop_testing()
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        runner.stop_testing()

if __name__ == "__main__":
    main()
