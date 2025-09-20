"""
Integration Script for Adding Process Monitor to Test Console
===========================================================

This script adds the process monitoring functionality to the existing
test_console.py file. It modifies the EOLTesterGUI class to include
process monitoring capabilities.

Usage:
    python add_monitor_to_console.py

This will add the necessary methods and integration code to test_console.py

Author: EOL Testing System  
Version: 1.0
"""

import os
import re


def add_monitor_integration_to_console():
    """Add process monitor integration to the test console"""
    
    console_file = "test_console.py"
    backup_file = "test_console_backup.py"
    
    if not os.path.exists(console_file):
        print(f"❌ {console_file} not found!")
        return False
    
    print(f"🔧 Adding process monitor integration to {console_file}")
    
    # Create backup
    try:
        with open(console_file, 'r') as f:
            content = f.read()
        
        with open(backup_file, 'w') as f:
            f.write(content)
        
        print(f"✅ Backup created: {backup_file}")
        
    except Exception as e:
        print(f"❌ Error creating backup: {e}")
        return False
    
    # Add import statements
    import_additions = '''
# Process Monitor Integration
try:
    from process_monitor_integration import ProcessMonitorIntegration, setup_process_monitoring
    PROCESS_MONITOR_AVAILABLE = True
    print("✅ Process monitor integration available")
except ImportError as e:
    print(f"⚠️ Process monitor not available: {e}")
    PROCESS_MONITOR_AVAILABLE = False
'''
    
    # Find the import section and add our imports
    import_pattern = r'(import queue\s*\n)'
    if re.search(import_pattern, content):
        content = re.sub(import_pattern, r'\1' + import_additions, content)
        print("✅ Added import statements")
    else:
        print("⚠️ Could not find import section, adding at the top")
        content = import_additions + '\n' + content
    
    # Add initialization in __init__ method
    init_addition = '''
        # Process Monitor Integration
        self.process_monitor_integration = None
        self.auto_cycle_monitoring = False
        
        # Initialize process monitor if available
        if PROCESS_MONITOR_AVAILABLE:
            self.initialize_process_monitor()
'''
    
    # Find the end of __init__ method and add our initialization
    init_pattern = r'(self\.root\.protocol\("WM_DELETE_WINDOW", self\.on_closing\)\s*\n)'
    if re.search(init_pattern, content):
        content = re.sub(init_pattern, r'\1' + init_addition, content)
        print("✅ Added initialization code")
    else:
        print("⚠️ Could not find __init__ method end")
    
    # Add the process monitor methods
    monitor_methods = '''
    def initialize_process_monitor(self):
        """Initialize the process monitoring system"""
        try:
            if not PROCESS_MONITOR_AVAILABLE:
                self.safe_update_message("Process monitor not available", "orange")
                return False
            
            self.process_monitor_integration = setup_process_monitoring(self)
            
            if self.process_monitor_integration:
                print("✅ Process monitor integration initialized")
                return True
            else:
                print("❌ Failed to initialize process monitor integration")
                return False
                
        except Exception as e:
            print(f"❌ Error initializing process monitor: {e}")
            return False
    
    def start_automated_monitoring(self):
        """Start automated cycle monitoring"""
        try:
            if not self.process_monitor_integration:
                self.safe_update_message("Process monitor not initialized", "red")
                return False
            
            if self.process_monitor_integration.start_integrated_monitoring():
                self.auto_cycle_monitoring = True
                self.safe_update_message("Automated monitoring started", "green")
                print("✅ Automated cycle monitoring started")
                return True
            else:
                self.safe_update_message("Failed to start automated monitoring", "red")
                return False
                
        except Exception as e:
            print(f"❌ Error starting automated monitoring: {e}")
            self.safe_update_message(f"Monitor start error: {e}", "red")
            return False
    
    def stop_automated_monitoring(self):
        """Stop automated cycle monitoring"""
        try:
            if self.process_monitor_integration:
                self.process_monitor_integration.stop_integrated_monitoring()
                self.auto_cycle_monitoring = False
                self.safe_update_message("Automated monitoring stopped", "orange")
                print("✅ Automated cycle monitoring stopped")
            
        except Exception as e:
            print(f"❌ Error stopping automated monitoring: {e}")
    
    def force_cycle_restart(self):
        """Force restart the current testing cycle"""
        try:
            if self.process_monitor_integration:
                self.process_monitor_integration.force_cycle_restart()
                self.safe_update_message("Cycle restart forced", "blue")
                print("🔄 Forced cycle restart")
            else:
                self.safe_update_message("Process monitor not available", "red")
                
        except Exception as e:
            print(f"❌ Error forcing cycle restart: {e}")
    
    def get_monitoring_status(self):
        """Get current monitoring status"""
        try:
            if self.process_monitor_integration:
                return self.process_monitor_integration.get_integration_status()
            else:
                return {"error": "Process monitor not initialized"}
                
        except Exception as e:
            print(f"❌ Error getting monitoring status: {e}")
            return {"error": str(e)}
    
    def on_automated_cycle_complete(self, cycle_count, status):
        """Callback for when an automated cycle completes"""
        try:
            # Update cycle counter
            self.current_cycle_number = cycle_count
            
            # Determine result
            result = "PASS" if status.get("TESTRESULT_OK", False) else "FAIL"
            
            # Update GUI
            self.safe_update_message(f"Auto Cycle #{cycle_count}: {result}", 
                                   "green" if result == "PASS" else "red")
            
            # Log the completion
            print(f"🎯 Automated cycle #{cycle_count} completed: {result}")
            
            # Update any cycle-specific displays
            if hasattr(self, 'update_cycle_display'):
                self.update_cycle_display(cycle_count, result)
            
        except Exception as e:
            print(f"❌ Error in automated cycle complete callback: {e}")
'''
    
    # Find a good place to add the methods (after the last method in the class)
    # Look for the main() function as a landmark
    main_pattern = r'(def main\(\):)'
    if re.search(main_pattern, content):
        content = re.sub(main_pattern, monitor_methods + '\n\n' + r'\1', content)
        print("✅ Added process monitor methods")
    else:
        print("⚠️ Could not find good insertion point, adding at end")
        content += monitor_methods
    
    # Update the on_closing method to stop monitoring
    closing_pattern = r'(def on_closing\(self\):.*?)(except Exception as e:.*?\n)'
    closing_replacement = r'\1        # Stop automated monitoring\n        if hasattr(self, "auto_cycle_monitoring") and self.auto_cycle_monitoring:\n            self.stop_automated_monitoring()\n        \n        \2'
    
    if re.search(closing_pattern, content, re.DOTALL):
        content = re.sub(closing_pattern, closing_replacement, content, flags=re.DOTALL)
        print("✅ Updated on_closing method")
    
    # Write the updated content
    try:
        with open(console_file, 'w') as f:
            f.write(content)
        
        print(f"✅ Successfully updated {console_file}")
        print(f"📋 Backup available at: {backup_file}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error writing updated file: {e}")
        
        # Restore from backup
        try:
            with open(backup_file, 'r') as f:
                original_content = f.read()
            
            with open(console_file, 'w') as f:
                f.write(original_content)
            
            print(f"✅ Restored original file from backup")
            
        except Exception as restore_error:
            print(f"❌ Error restoring backup: {restore_error}")
        
        return False


def create_monitor_config():
    """Create a default process monitor configuration"""
    config_content = '''{
    "monitor_interval": 1.0,
    "cycle_timeout": 300,
    "restart_delay": 3.0,
    "max_consecutive_failures": 5,
    "process_status_addresses": {
        "AUTO": "M0067",
        "HOME": "M0068", 
        "PULL1_OK": "M0076",
        "PULL1_NG": "M0085",
        "PULL2_OK": "M0078",
        "PULL2_NG": "M0087",
        "TESTRESULT_OK": "M0075",
        "TESTRESULT_NG": "M0079"
    },
    "cycle_completion_indicators": [
        "TESTRESULT_OK",
        "TESTRESULT_NG"
    ],
    "logging": {
        "level": "INFO",
        "file": "process_monitor.log",
        "max_size_mb": 10,
        "backup_count": 5
    }
}'''
    
    config_file = "process_monitor_config.json"
    
    try:
        with open(config_file, 'w') as f:
            f.write(config_content)
        
        print(f"✅ Created configuration file: {config_file}")
        return True
        
    except Exception as e:
        print(f"❌ Error creating config file: {e}")
        return False


def main():
    """Main integration function"""
    print("🚀 Process Monitor Integration Setup")
    print("=" * 50)
    
    success = True
    
    # Step 1: Add integration to test console
    print("\n1️⃣ Adding integration to test console...")
    if add_monitor_integration_to_console():
        print("   ✅ Integration added successfully")
    else:
        print("   ❌ Failed to add integration")
        success = False
    
    # Step 2: Create configuration file
    print("\n2️⃣ Creating monitor configuration...")
    if create_monitor_config():
        print("   ✅ Configuration created successfully")
    else:
        print("   ❌ Failed to create configuration")
        success = False
    
    # Step 3: Provide usage instructions
    print("\n3️⃣ Integration Complete!")
    if success:
        print("""
✅ Process Monitor Integration Setup Complete!

📋 What was added:
   • Process monitor integration imports
   • Initialization code in __init__
   • Automated monitoring methods
   • Cycle completion callbacks
   • Configuration file

🚀 How to use:
   1. Run your test console normally: python test_console.py
   2. The process monitor will initialize automatically
   3. Use the new monitoring features in your GUI
   4. Monitor will automatically detect and restart cycles

🔧 New methods available:
   • start_automated_monitoring()
   • stop_automated_monitoring() 
   • force_cycle_restart()
   • get_monitoring_status()

📁 Files created/modified:
   • test_console.py (modified)
   • test_console_backup.py (backup)
   • process_monitor_config.json (config)
        """)
    else:
        print("❌ Integration setup failed. Check error messages above.")
    
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())

