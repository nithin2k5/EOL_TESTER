import tkinter as tk
from test_console_clone import EOLTesterGUI
import time
import threading

def test_eol_process():
    """Test the EOL testing process with sample2"""

    # Create the application
    root = tk.Tk()
    app = EOLTesterGUI(root)

    print("🔧 EOL Tester Application Started")
    print("📊 Current Status:")
    print(f"   PLC Status: {getattr(app, 'plc_indicator_status', 'Unknown')}")
    print(f"   Process Status: {getattr(app, 'process_status', 'Unknown')}")

    # Function to simulate employee validation
    def simulate_employee_validation():
        try:
            if hasattr(app, 'emp_entry'):
                app.emp_entry.delete(0, tk.END)
                app.emp_entry.insert(0, 'S041')
                app.validate_employee_code()
                print("✅ Employee validation completed with S041")
            else:
                print("❌ Employee entry field not found")
        except Exception as e:
            print(f"❌ Employee validation error: {e}")

    # Function to simulate ALC code entry
    def simulate_alc_entry():
        try:
            if hasattr(app, 'alc_entry'):
                app.alc_entry.delete(0, tk.END)
                app.alc_entry.insert(0, 'sample2')
                app.process_alc_code()
                print("✅ ALC code 'sample2' validated - ready for JIG SCAN")
            else:
                print("❌ ALC entry field not found")
        except Exception as e:
            print(f"❌ ALC entry error: {e}")

    # Function to simulate JIG SCAN entry
    def simulate_jig_scan():
        try:
            if hasattr(app, 'additional_entry2'):
                app.additional_entry2.delete(0, tk.END)
                app.additional_entry2.insert(0, 'sample2')
                app.process_jig_scan()
                print("✅ JIG SCAN 'sample2' entered")
            else:
                print("❌ JIG SCAN entry field not found")
        except Exception as e:
            print(f"❌ JIG SCAN error: {e}")

    # Function to start testing
    def start_testing():
        try:
            app.start_eol_testing_process()
            print("✅ Testing started")

            # Monitor testing progress
            monitor_testing()
        except Exception as e:
            print(f"❌ Testing start error: {e}")

    # Function to monitor testing indicators
    def monitor_testing():
        try:
            print("\n📈 Monitoring Testing Process...")

            # Check status labels dictionary
            if hasattr(app, 'status_labels') and app.status_labels:
                print("Status Indicators:")
                for label_name, label_widget in app.status_labels.items():
                    current_text = label_widget.cget('text')
                    current_color = label_widget.cget('bg')
                    print(f"   {label_name}: '{current_text}' (Color: {current_color})")
            else:
                print("❌ Status indicators not found")

            # Check individual status labels as fallback
            status_label_map = {
                'AUTO': 'auto_label',
                'HOME': 'home_label',
                '1ST': '1st_label',
                '2ND': '2nd_label',
                'TEST': 'test_label'
            }
            print("\nIndividual Status Labels:")
            for display_name, attr_name in status_label_map.items():
                if hasattr(app, attr_name):
                    label_widget = getattr(app, attr_name)
                    current_text = label_widget.cget('text')
                    current_color = label_widget.cget('bg')
                    print(f"   {display_name}: '{current_text}' (Color: {current_color})")
                else:
                    print(f"   {display_name}: Not found")

            # Check sensor labels
            if hasattr(app, 'placed_labels'):
                print("\nSensor Labels:")
                for label_text, label_widget in app.placed_labels.items():
                    current_text = label_widget.cget('text')
                    current_color = label_widget.cget('bg')
                    print(f"   {label_text}: '{current_text}' (Color: {current_color})")
            else:
                print("❌ Sensor labels not found")

            # Check specifications grid
            if hasattr(app, 'spec_tree') and app.spec_tree:
                print("\n📋 Specifications Grid:")
                for item in app.spec_tree.get_children():
                    values = app.spec_tree.item(item)['values']
                    if len(values) >= 7:
                        description = values[0]
                        device = values[1]
                        unit = values[2]
                        min_val = values[3]
                        max_val = values[4]
                        actual = values[5]
                        result = values[6]
                        print(f"   {device}: Min={min_val}, Max={max_val}, Actual={actual}, Result={result}")
            else:
                print("❌ Specifications tree not found")

            # Check overall process status
            print(f"\nProcess Status: {getattr(app, 'process_status', 'Unknown')}")
            if hasattr(app, 'status_indicator'):
                indicator_text = app.status_indicator.cget('text')
                indicator_color = app.status_indicator.cget('fg')
                print(f"Process Indicator: '{indicator_text}' (Color: {indicator_color})")

            # Check test counters
            print(f"Pass Counter: {getattr(app, 'passCounter', 'Unknown')}")
            print(f"Fail Counter: {getattr(app, 'failCounter', 'Unknown')}")

        except Exception as e:
            print(f"❌ Monitoring error: {e}")

    # Function to check PLC simulation
    def check_plc_simulation():
        try:
            print("\n🔌 PLC Connection Status:")
            print(f"   Simulation Mode: {app.dev_config.get('plc_simulation_mode', 'Unknown')}")
            print(f"   PLC Client: {app.plc_client is not None}")
            print(f"   Process Status: {getattr(app, 'process_status', 'Unknown')}")
            if hasattr(app, 'plc_indicator'):
                indicator_text = app.plc_indicator.cget('text')
                indicator_color = app.plc_indicator.cget('fg')
                print(f"   PLC Indicator: '{indicator_text}' (Color: {indicator_color})")
        except Exception as e:
            print(f"❌ PLC status check error: {e}")

    # Function to monitor PLC status after testing starts
    def monitor_plc_after_start():
        try:
            print("\n🔄 PLC Status After Testing Start:")
            if hasattr(app, 'plc_indicator'):
                indicator_text = app.plc_indicator.cget('text')
                indicator_color = app.plc_indicator.cget('fg')
                print(f"   PLC Indicator: '{indicator_text}' (Color: {indicator_color})")
                print(f"   Process Status: {getattr(app, 'process_status', 'Unknown')}")
        except Exception as e:
            print(f"❌ PLC monitoring error: {e}")

    # Schedule the test sequence
    root.after(1000, lambda: print("⏳ Starting test sequence..."))

    # Step 1: Employee validation
    root.after(2000, simulate_employee_validation)

    # Step 2: ALC code entry
    root.after(4000, simulate_alc_entry)

    # Step 3: Wait for ALC validation and JIG SCAN entry
    def delayed_jig_scan():
        if hasattr(app, 'validated_alc_code') and app.validated_alc_code:
            simulate_jig_scan()
        else:
            print("⏳ Waiting for ALC validation to complete...")
            root.after(1000, delayed_jig_scan)

    root.after(6000, delayed_jig_scan)

    # Step 4: Check PLC status
    root.after(8000, check_plc_simulation)

    # Step 5: Start testing (should auto-start after part load)
    root.after(10000, lambda: print("⏳ Testing should auto-start after part load..."))

    # Step 6: Monitor PLC status after testing starts
    root.after(12000, monitor_plc_after_start)

    # Step 7: Final monitoring
    root.after(14000, monitor_testing)
    root.after(16000, lambda: print("\n🏁 Test sequence completed"))

    # Start the GUI main loop
    root.mainloop()

if __name__ == "__main__":
    test_eol_process()
