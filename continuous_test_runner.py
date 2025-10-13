#!/usr/bin/env python3
"""
Continuous EOL Test Runner
Runs EOL tests in a loop repeatedly until stopped
"""

import tkinter as tk
import time
import threading
from test_console_clone import EOLTesterGUI

class ContinuousTestRunner:
    def __init__(self):
        self.root = None
        self.app = None
        self.running = False
        self.test_count = 0
        self.start_time = time.time()

    def start_continuous_testing(self):
        """Start the continuous test loop"""
        try:
            print("🚀 Starting Continuous EOL Test Runner")
            print("=" * 50)

            # Create Tkinter root
            self.root = tk.Tk()

            # Initialize the EOL Tester application
            self.app = EOLTesterGUI(self.root)

            # Set running flag
            self.running = True

            # Start the continuous test workflow after a short delay
            self.root.after(2000, self.initialize_and_start_workflow)

            # Start monitoring thread
            monitor_thread = threading.Thread(target=self.monitor_tests, daemon=True)
            monitor_thread.start()

            # Start the GUI main loop
            self.root.mainloop()

        except KeyboardInterrupt:
            print("\n🛑 Continuous testing interrupted by user")
            self.stop_testing()
        except Exception as e:
            print(f"❌ Error in continuous testing: {e}")
            self.stop_testing()

    def initialize_and_start_workflow(self):
        """Initialize and start the complete EOL workflow"""
        try:
            print("🔧 Initializing EOL Workflow...")
            self.test_count += 1
            print(f"📊 Test Cycle #{self.test_count}")

            # Execute the complete EOL workflow (this starts continuous automated testing)
            success = self.app.execute_complete_eol_workflow()

            if success:
                print("✅ EOL Workflow started successfully - continuous testing active")
                print("🎯 System will run automated cycles until PLC signal goes LOW")
                print("💡 Press Ctrl+C to stop continuous testing")
            else:
                print("❌ Failed to start EOL workflow")
                self.stop_testing()

        except Exception as e:
            print(f"❌ Error initializing workflow: {e}")
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

                    print("📈 Continuous Testing Status:"                    print(f"   • Total Tests: {self.test_count}")
                    print(f"   • Runtime: {hours:02d}:{minutes:02d}:{seconds:02d}")
                    print(f"   • Process Status: {getattr(self.app, 'process_status', 'UNKNOWN')}")
                    print(f"   • Continuous Active: {getattr(self.app, 'continuous_testing_active', False)}")
                    print("-" * 40)

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
                    self.root.after(1000, self.initialize_and_start_workflow)

        except Exception as e:
            print(f"❌ Error restarting test cycle: {e}")

    def stop_testing(self):
        """Stop the continuous testing"""
        print("\n🛑 Stopping Continuous EOL Testing...")
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

        print("📊 Final Test Statistics:"        print(f"   • Total Test Cycles: {self.test_count}")
        print(f"   • Total Runtime: {hours:02d}:{minutes:02d}:{seconds:02d}")
        print("=" * 50)
        print("✅ Continuous testing stopped")

def main():
    """Main function to run continuous tests"""
    print("🔄 EOL Continuous Test Runner")
    print("This will run EOL tests continuously until stopped")
    print("Press Ctrl+C to stop\n")

    # Create and start the continuous test runner
    runner = ContinuousTestRunner()

    try:
        runner.start_continuous_testing()
    except KeyboardInterrupt:
        runner.stop_testing()
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        runner.stop_testing()

if __name__ == "__main__":
    main()
