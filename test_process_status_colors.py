import tkinter as tk
from test_console_clone import EOLTesterGUI
import time

def test_process_status_colors():
    """Test process status label color changes after test completion"""

    # Create the application
    root = tk.Tk()
    app = EOLTesterGUI(root)

    print("🔧 Testing Process Status Label Color Changes")
    print("=" * 50)

    # Function to simulate employee validation
    def simulate_employee_validation():
        try:
            if hasattr(app, 'emp_entry'):
                app.emp_entry.delete(0, tk.END)
                app.emp_entry.insert(0, 'S041')
                app.validate_employee_code()
                print("✅ Employee validation completed with S041")
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
        except Exception as e:
            print(f"❌ JIG SCAN error: {e}")

    # Function to monitor status label colors
    def monitor_status_colors(step_name):
        print(f"\n🎨 {step_name} - Status Label Colors:")
        if hasattr(app, 'status_labels') and app.status_labels:
            for label_name, label_widget in app.status_labels.items():
                current_color = label_widget.cget('bg')
                print(f"   {label_name}: {current_color}")
        else:
            print("   ❌ Status labels not found")

    # Schedule the test sequence
    root.after(1000, lambda: print("⏳ Starting test sequence..."))

    # Step 1: Employee validation
    root.after(2000, simulate_employee_validation)

    # Step 2: ALC code entry
    root.after(4000, simulate_alc_entry)

    # Step 3: JIG SCAN entry
    def delayed_jig_scan():
        if hasattr(app, 'validated_alc_code') and app.validated_alc_code:
            simulate_jig_scan()
        else:
            print("⏳ Waiting for ALC validation to complete...")
            root.after(1000, delayed_jig_scan)

    root.after(6000, delayed_jig_scan)

    # Step 4: Monitor initial colors (should be Deep Sky Blue)
    root.after(8000, lambda: monitor_status_colors("INITIAL STATE"))

    # Step 5: Check colors after test completion (should be Green/Lime or OrangeRed)
    root.after(12000, lambda: monitor_status_colors("AFTER TEST COMPLETION"))

    # Step 6: Final monitoring
    root.after(14000, lambda: print("\n🏁 Test sequence completed"))

    # Start the GUI main loop
    root.mainloop()

if __name__ == "__main__":
    test_process_status_colors()
