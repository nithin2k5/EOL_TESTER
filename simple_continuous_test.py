#!/usr/bin/env python3
"""
Simple Continuous Test Runner
Directly triggers the existing continuous testing functionality
"""

import time
import threading
from test_console_clone import EOLTesterGUI
import tkinter as tk

def run_continuous_tests():
    """Run tests continuously using the existing workflow"""
    try:
        print("🚀 Starting Simple Continuous EOL Testing")
        print("=" * 50)

        # Create Tkinter application
        root = tk.Tk()
        app = EOLTesterGUI(root)

        def delayed_workflow_start():
            """Start workflow after GUI is fully initialized"""
            try:
                print("🔧 Starting EOL Workflow...")
                success = app.execute_complete_eol_workflow()

                if success:
                    print("✅ Continuous testing started successfully!")
                    print("🎯 The system will automatically run test cycles in a loop")
                    print("💡 Close the GUI window to stop testing")
                    print("=" * 50)
                else:
                    print("❌ Failed to start continuous testing")
            except Exception as e:
                print(f"❌ Error starting workflow: {e}")

        # Wait for GUI to be fully initialized before starting workflow
        print("⏳ Waiting for GUI initialization...")
        root.after(3000, delayed_workflow_start)  # Wait 3 seconds for GUI setup

        # Start the GUI
        root.mainloop()

    except Exception as e:
        print(f"❌ Error: {e}")
        try:
            root.destroy()
        except:
            pass

def run_multiple_cycles():
    """Run a specific number of test cycles"""
    try:
        num_cycles = int(input("How many test cycles to run? "))

        for cycle in range(1, num_cycles + 1):
            print(f"\n🔄 Starting Test Cycle {cycle}/{num_cycles}")
            print("-" * 30)

            # Create fresh application instance for each cycle
            root = tk.Tk()
            app = EOLTesterGUI(root)

            def start_cycle_workflow():
                """Start workflow for this cycle after GUI initialization"""
                try:
                    success = app.execute_complete_eol_workflow()

                    if success:
                        print(f"✅ Cycle {cycle} started - monitoring...")

                        # Monitor for completion (simplified)
                        start_time = time.time()
                        while time.time() - start_time < 300:  # 5 minute timeout per cycle
                            if hasattr(app, 'process_status') and app.process_status == "LOW":
                                print(f"✅ Cycle {cycle} completed")
                                break
                            time.sleep(1)

                        if time.time() - start_time >= 300:
                            print(f"⏰ Cycle {cycle} timed out after 5 minutes")

                    else:
                        print(f"❌ Cycle {cycle} failed to start")

                except Exception as e:
                    print(f"❌ Error in cycle {cycle}: {e}")
                finally:
                    # Clean up
                    try:
                        root.quit()
                        root.destroy()
                    except:
                        pass

            # Wait for GUI initialization then start workflow
            root.after(3000, start_cycle_workflow)

            # Start GUI for this cycle
            root.mainloop()

            # Brief pause between cycles
            if cycle < num_cycles:
                print(f"⏳ Waiting 3 seconds before next cycle...")
                time.sleep(3)

        print(f"\n🎉 Completed {num_cycles} test cycles!")

    except ValueError:
        print("❌ Please enter a valid number")
    except KeyboardInterrupt:
        print("\n🛑 Testing interrupted by user")
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    """Main menu for test options"""
    print("🔄 EOL Test Runner Options:")
    print("1. Run continuous testing (runs until stopped)")
    print("2. Run specific number of cycles")
    print("3. Exit")

    while True:
        try:
            choice = input("\nSelect option (1-3): ").strip()

            if choice == "1":
                run_continuous_tests()
                break
            elif choice == "2":
                run_multiple_cycles()
                break
            elif choice == "3":
                print("👋 Goodbye!")
                break
            else:
                print("❌ Please select 1, 2, or 3")

        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
