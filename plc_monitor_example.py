"""
PLC Monitor Integration Example
================================
Shows how to integrate PLCMonitor into your EOL testing application.

This example demonstrates:
- Setting up PLC monitor with GUI labels
- Starting/stopping monitoring
- Handling callbacks for status changes
- Managing P0000 keep-alive
- Tracking test progress
"""

import tkinter as tk
from tkinter import messagebox
from plc_monitor import PLCMonitor
import os
import datetime


class EOLTestApplication:
    """Example EOL test application using PLCMonitor"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("EOL Test - PLC Monitor Example")
        self.root.geometry("800x600")
        
        # Create GUI
        self.create_gui()
        
        # Initialize PLC Monitor
        self.plc_monitor = PLCMonitor(
            root=self.root,
            status_labels=self.status_labels
        )
        
        # Load process addresses
        self.plc_monitor.load_process_addresses()
        
        # Set up callbacks
        self.setup_callbacks()
        
        # Test state
        self.test_running = False
        self.current_lot_number = None
        
    def create_gui(self):
        """Create the GUI interface"""
        
        # Title
        title_frame = tk.Frame(self.root, bg="#FFB6C1", height=40)
        title_frame.pack(fill="x")
        
        title_label = tk.Label(
            title_frame,
            text="EOL TEST - PLC Monitor",
            bg="#FFB6C1",
            font=("Arial", 16, "bold")
        )
        title_label.pack(pady=5)
        
        # Status Labels Frame
        status_frame = tk.Frame(self.root, bg="#f0f0f0")
        status_frame.pack(fill="x", pady=20, padx=20)
        
        tk.Label(
            status_frame,
            text="Process Status:",
            font=("Arial", 12, "bold"),
            bg="#f0f0f0"
        ).pack(anchor="w", padx=10, pady=5)
        
        # Create status labels
        labels_container = tk.Frame(status_frame, bg="#f0f0f0")
        labels_container.pack(fill="x", padx=10, pady=10)
        
        self.status_labels = {}
        label_configs = [
            {'name': 'auto', 'text': 'AUTO'},
            {'name': 'home', 'text': 'HOME'},
            {'name': '1st', 'text': '1st PULL\n(Load Test)'},
            {'name': '2nd', 'text': '2nd PULL\n(Length Test)'},
            {'name': 'test', 'text': 'TEST\nRESULT'}
        ]
        
        for config in label_configs:
            label = tk.Label(
                labels_container,
                text=config['text'],
                bg="#00BFFF",
                fg="black",
                font=("Arial", 10, "bold"),
                relief="raised",
                borderwidth=2,
                width=15,
                height=3
            )
            label.pack(side="left", padx=5)
            self.status_labels[config['name']] = label
        
        # Control Panel
        control_frame = tk.Frame(self.root, bg="#e0e0e0")
        control_frame.pack(fill="x", pady=10, padx=20)
        
        tk.Label(
            control_frame,
            text="Control Panel:",
            font=("Arial", 12, "bold"),
            bg="#e0e0e0"
        ).pack(anchor="w", padx=10, pady=5)
        
        button_frame = tk.Frame(control_frame, bg="#e0e0e0")
        button_frame.pack(fill="x", padx=10, pady=10)
        
        # Control Buttons
        self.connect_btn = tk.Button(
            button_frame,
            text="📡 Connect PLC",
            command=self.connect_plc,
            bg="#4CAF50",
            fg="white",
            font=("Arial", 10, "bold"),
            width=15,
            height=2
        )
        self.connect_btn.pack(side="left", padx=5)
        
        self.start_btn = tk.Button(
            button_frame,
            text="▶️ Start Test",
            command=self.start_test,
            bg="#2196F3",
            fg="white",
            font=("Arial", 10, "bold"),
            width=15,
            height=2,
            state='disabled'
        )
        self.start_btn.pack(side="left", padx=5)
        
        self.stop_btn = tk.Button(
            button_frame,
            text="⏹️ Stop Test",
            command=self.stop_test,
            bg="#f44336",
            fg="white",
            font=("Arial", 10, "bold"),
            width=15,
            height=2,
            state='disabled'
        )
        self.stop_btn.pack(side="left", padx=5)
        
        self.reset_btn = tk.Button(
            button_frame,
            text="🔄 Reset",
            command=self.reset_test,
            bg="#FF9800",
            fg="white",
            font=("Arial", 10, "bold"),
            width=15,
            height=2
        )
        self.reset_btn.pack(side="left", padx=5)
        
        # Progress Display
        progress_frame = tk.Frame(self.root, bg="#f5f5f5")
        progress_frame.pack(fill="both", expand=True, pady=10, padx=20)
        
        tk.Label(
            progress_frame,
            text="Test Progress:",
            font=("Arial", 12, "bold"),
            bg="#f5f5f5"
        ).pack(anchor="w", padx=10, pady=5)
        
        # Progress bar placeholder
        self.progress_label = tk.Label(
            progress_frame,
            text="0/8 Steps Complete (0%)",
            font=("Arial", 14),
            bg="#f5f5f5",
            fg="#2196F3"
        )
        self.progress_label.pack(pady=10)
        
        # Log Display
        log_frame = tk.Frame(progress_frame, bg="#f5f5f5")
        log_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        scrollbar = tk.Scrollbar(log_frame)
        scrollbar.pack(side="right", fill="y")
        
        self.log_text = tk.Text(
            log_frame,
            height=10,
            yscrollcommand=scrollbar.set,
            font=("Consolas", 9),
            bg="white"
        )
        self.log_text.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.log_text.yview)
        
        # Status Bar
        self.status_bar = tk.Label(
            self.root,
            text="Ready - Connect to PLC to begin",
            bg="#FFB6C1",
            font=("Arial", 10),
            anchor="w"
        )
        self.status_bar.pack(fill="x", side="bottom")
        
    def setup_callbacks(self):
        """Set up PLC monitor callbacks"""
        self.plc_monitor.on_status_change = self.on_plc_status_change
        self.plc_monitor.on_step_complete = self.on_step_complete
    
    def log(self, message):
        """Add message to log"""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.log_text.insert("end", f"[{timestamp}] {message}\n")
        self.log_text.see("end")
    
    def update_status(self, message, color="black"):
        """Update status bar"""
        self.status_bar.config(text=message, fg=color)
    
    def update_progress(self):
        """Update progress display"""
        progress = self.plc_monitor.get_progress()
        self.progress_label.config(
            text=f"{progress['visited_steps']}/{progress['total_steps']} Steps Complete ({progress['progress_percent']:.0f}%)"
        )
    
    def connect_plc(self):
        """Connect to PLC"""
        self.log("Connecting to PLC...")
        
        if self.plc_monitor.connect_to_plc():
            self.log("✅ PLC Connected Successfully")
            self.update_status("PLC Connected", "green")
            self.connect_btn.config(state='disabled')
            self.start_btn.config(state='normal')
        else:
            self.log("❌ PLC Connection Failed")
            self.update_status("PLC Connection Failed", "red")
            messagebox.showerror("Connection Error", "Failed to connect to PLC")
    
    def start_test(self):
        """Start EOL test"""
        try:
            self.log("🚀 Starting EOL Test...")
            
            # Start monitoring
            if self.plc_monitor.start_monitoring():
                self.log("✅ PLC Monitoring Started")
                
                # Start P0000 keep-alive
                self.plc_monitor.start_p0000_keepalive()
                self.log("✅ P0000 Keep-Alive Started")
                
                # Update UI
                self.test_running = True
                self.start_btn.config(state='disabled')
                self.stop_btn.config(state='normal')
                self.update_status("Test Running - Monitoring PLC...", "blue")
                
                # Generate lot number
                self.current_lot_number = self.generate_lot_number()
                self.log(f"📋 LOT Number: {self.current_lot_number}")
                
            else:
                self.log("❌ Failed to Start Monitoring")
                messagebox.showerror("Error", "Failed to start PLC monitoring")
                
        except Exception as e:
            self.log(f"❌ Error: {e}")
            messagebox.showerror("Error", f"Failed to start test: {e}")
    
    def stop_test(self):
        """Stop EOL test"""
        self.log("⏹️ Stopping EOL Test...")
        
        # Stop keep-alive
        self.plc_monitor.stop_p0000_keepalive()
        self.log("🛑 P0000 Keep-Alive Stopped")
        
        # Stop monitoring
        self.plc_monitor.stop_monitoring()
        self.log("🛑 PLC Monitoring Stopped")
        
        # Write P0000 LOW
        self.plc_monitor.write_plc_coil("P0000", False)
        self.log("📝 P0000 Set to LOW")
        
        # Update UI
        self.test_running = False
        self.stop_btn.config(state='disabled')
        self.start_btn.config(state='normal')
        self.update_status("Test Stopped", "orange")
    
    def reset_test(self):
        """Reset test for new cycle"""
        self.log("🔄 Resetting Test...")
        
        # Reset step tracking
        self.plc_monitor.reset_step_tracking()
        
        # Reset labels to default
        for label in self.status_labels.values():
            label.config(bg="#00BFFF", fg="black")
        
        # Reset progress
        self.progress_label.config(text="0/8 Steps Complete (0%)")
        
        # Clear current lot
        self.current_lot_number = None
        
        self.log("✅ Test Reset Complete")
        self.update_status("Ready for New Test", "green")
    
    def on_plc_status_change(self, status_values, active_step):
        """Callback when PLC status changes"""
        self.log(f"📊 Status Change: {active_step} is now active")
        self.update_progress()
    
    def on_step_complete(self, address, label_key, step_num):
        """Callback when a step completes"""
        self.log(f"✅ Step {step_num} Complete: {address} ({label_key.upper()})")
        self.update_progress()
        
        # Check if test is complete
        progress = self.plc_monitor.get_progress()
        if progress['visited_steps'] >= progress['total_steps']:
            self.on_test_complete()
    
    def on_test_complete(self):
        """Handle test completion"""
        self.log("🎉 TEST COMPLETE - All steps finished!")
        self.update_status("Test Complete - All Steps Passed", "green")
        
        # Auto-stop test
        self.root.after(2000, self.stop_test)
        
        # Show completion message
        messagebox.showinfo(
            "Test Complete",
            f"EOL Test completed successfully!\nLOT: {self.current_lot_number}"
        )
    
    def generate_lot_number(self):
        """Generate simple lot number"""
        import datetime
        now = datetime.datetime.now()
        return f"{now.strftime('%y%m%d')}I1GA0000001"
    
    def on_closing(self):
        """Handle window close"""
        if self.test_running:
            if messagebox.askyesno("Confirm Exit", "Test is running. Stop test and exit?"):
                self.stop_test()
                self.plc_monitor.disconnect_plc()
                self.root.destroy()
        else:
            self.plc_monitor.disconnect_plc()
            self.root.destroy()


def main():
    """Main entry point"""
    root = tk.Tk()
    app = EOLTestApplication(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()

