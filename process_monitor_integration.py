"""
Process Monitor Integration Module
=================================

This module provides integration between the main test console (test_console.py)
and the process status monitor (process_monitor.py). It handles communication,
status updates, and coordination between the two systems.

Features:
- Seamless integration with existing test console
- Real-time status synchronization
- Event-driven communication
- GUI status updates
- Error handling and recovery

Author: EOL Testing System
Version: 1.0
"""

import threading
import queue
import time
from datetime import datetime
from typing import Dict, Optional, Callable
from process_monitor import ProcessStatusMonitor


class ProcessMonitorIntegration:
    """
    Integration layer between main test console and process monitor
    """
    
    def __init__(self, main_app_instance=None):
        """
        Initialize the integration module
        
        Args:
            main_app_instance: Reference to the main EOLTesterGUI instance
        """
        self.main_app = main_app_instance
        self.monitor = None
        self.integration_active = False
        self.status_update_thread = None
        
        # Communication queues
        self.gui_update_queue = queue.Queue()
        self.monitor_command_queue = queue.Queue()
        
        # Status tracking
        self.last_gui_update = None
        self.monitor_status = {}
        
        print("🔗 Process Monitor Integration initialized")
    
    def initialize_monitor(self, config_file: str = None) -> bool:
        """
        Initialize the process monitor
        
        Args:
            config_file (str): Path to monitor configuration file
            
        Returns:
            bool: True if initialization successful
        """
        try:
            self.monitor = ProcessStatusMonitor(config_file)
            
            # Set up callbacks
            self.monitor.set_callbacks(
                on_cycle_complete=self._on_cycle_complete,
                on_cycle_start=self._on_cycle_start,
                on_status_change=self._on_status_change,
                on_error=self._on_error
            )
            
            print("✅ Process monitor initialized successfully")
            return True
            
        except Exception as e:
            print(f"❌ Error initializing process monitor: {e}")
            return False
    
    def start_integrated_monitoring(self) -> bool:
        """
        Start the integrated monitoring system
        
        Returns:
            bool: True if started successfully
        """
        try:
            if not self.monitor:
                if not self.initialize_monitor():
                    return False
            
            # Start the process monitor
            if not self.monitor.start_monitoring():
                print("❌ Failed to start process monitor")
                return False
            
            # Start integration services
            self.integration_active = True
            
            # Start status update thread
            self.status_update_thread = threading.Thread(
                target=self._status_update_loop, 
                daemon=True
            )
            self.status_update_thread.start()
            
            print("✅ Integrated monitoring system started")
            return True
            
        except Exception as e:
            print(f"❌ Error starting integrated monitoring: {e}")
            return False
    
    def stop_integrated_monitoring(self):
        """Stop the integrated monitoring system"""
        try:
            self.integration_active = False
            
            if self.monitor:
                self.monitor.stop_monitoring()
            
            if self.status_update_thread and self.status_update_thread.is_alive():
                self.status_update_thread.join(timeout=3)
            
            print("✅ Integrated monitoring system stopped")
            
        except Exception as e:
            print(f"❌ Error stopping integrated monitoring: {e}")
    
    def _status_update_loop(self):
        """Main loop for processing status updates and GUI communication"""
        while self.integration_active:
            try:
                # Process monitor status updates
                if self.monitor and self.monitor.status_queue:
                    try:
                        status_update = self.monitor.status_queue.get_nowait()
                        self._process_status_update(status_update)
                    except queue.Empty:
                        pass
                
                # Process GUI update requests
                try:
                    gui_update = self.gui_update_queue.get_nowait()
                    self._process_gui_update(gui_update)
                except queue.Empty:
                    pass
                
                # Update GUI status periodically
                self._update_gui_status()
                
                time.sleep(0.1)  # 10Hz update rate
                
            except Exception as e:
                print(f"Error in status update loop: {e}")
                time.sleep(1)
    
    def _process_status_update(self, update: Dict):
        """Process status updates from the monitor"""
        try:
            update_type = update.get('type')
            timestamp = update.get('timestamp', datetime.now())
            
            if update_type == 'cycle_complete':
                self._handle_cycle_complete(update)
            elif update_type == 'cycle_restart':
                self._handle_cycle_restart(update)
            elif update_type == 'status_change':
                self._handle_status_change(update)
            elif update_type == 'error':
                self._handle_error(update)
            
            # Store for GUI updates
            self.monitor_status = update
            
        except Exception as e:
            print(f"Error processing status update: {e}")
    
    def _handle_cycle_complete(self, update: Dict):
        """Handle cycle completion event"""
        try:
            cycle_count = update.get('cycle_count', 0)
            status = update.get('status', {})
            
            print(f"🎯 Cycle #{cycle_count} completed: {status}")
            
            # Update main application if available
            if self.main_app:
                # Schedule GUI update in main thread
                if hasattr(self.main_app, 'root'):
                    self.main_app.root.after(0, lambda: self._update_main_app_cycle_complete(cycle_count, status))
            
        except Exception as e:
            print(f"Error handling cycle complete: {e}")
    
    def _handle_cycle_restart(self, update: Dict):
        """Handle cycle restart event"""
        try:
            cycle_count = update.get('cycle_count', 0)
            
            print(f"🔄 Cycle #{cycle_count} restarted")
            
            # Update main application if available
            if self.main_app:
                if hasattr(self.main_app, 'root'):
                    self.main_app.root.after(0, lambda: self._update_main_app_cycle_restart(cycle_count))
            
        except Exception as e:
            print(f"Error handling cycle restart: {e}")
    
    def _handle_status_change(self, update: Dict):
        """Handle status change event"""
        try:
            status = update.get('status', {})
            
            # Update main application status display
            if self.main_app:
                if hasattr(self.main_app, 'root'):
                    self.main_app.root.after(0, lambda: self._update_main_app_status(status))
            
        except Exception as e:
            print(f"Error handling status change: {e}")
    
    def _handle_error(self, update: Dict):
        """Handle error event"""
        try:
            error_msg = update.get('message', 'Unknown error')
            error_type = update.get('error_type', 'GENERAL')
            
            print(f"❌ Monitor Error [{error_type}]: {error_msg}")
            
            # Update main application error display
            if self.main_app:
                if hasattr(self.main_app, 'safe_update_message'):
                    self.main_app.root.after(0, lambda: self.main_app.safe_update_message(f"Monitor Error: {error_msg}", "red"))
            
        except Exception as e:
            print(f"Error handling error event: {e}")
    
    def _update_main_app_cycle_complete(self, cycle_count: int, status: Dict):
        """Update main app when cycle completes"""
        try:
            if hasattr(self.main_app, 'safe_update_message'):
                result = "PASS" if status.get("TESTRESULT_OK", False) else "FAIL"
                self.main_app.safe_update_message(f"Cycle #{cycle_count} Complete: {result}", "green" if result == "PASS" else "red")
            
            # Update cycle counter if available
            if hasattr(self.main_app, 'current_cycle_number'):
                self.main_app.current_cycle_number = cycle_count
            
            # Trigger any additional cycle complete logic
            if hasattr(self.main_app, 'on_automated_cycle_complete'):
                self.main_app.on_automated_cycle_complete(cycle_count, status)
                
        except Exception as e:
            print(f"Error updating main app for cycle complete: {e}")
    
    def _update_main_app_cycle_restart(self, cycle_count: int):
        """Update main app when cycle restarts"""
        try:
            if hasattr(self.main_app, 'safe_update_message'):
                self.main_app.safe_update_message(f"Starting Cycle #{cycle_count}", "blue")
            
            # Reset any test parameters
            if hasattr(self.main_app, 'reset_test_parameters'):
                self.main_app.reset_test_parameters()
                
        except Exception as e:
            print(f"Error updating main app for cycle restart: {e}")
    
    def _update_main_app_status(self, status: Dict):
        """Update main app status display"""
        try:
            # Update process status labels if they exist
            if hasattr(self.main_app, 'update_status_labels'):
                self.main_app.update_status_labels(status)
            
            # Update any status indicators
            if hasattr(self.main_app, 'update_process_indicator'):
                if status.get("AUTO", False):
                    self.main_app.update_process_indicator("RUNNING")
                elif status.get("HOME", False):
                    self.main_app.update_process_indicator("HOME")
                else:
                    self.main_app.update_process_indicator("IDLE")
                    
        except Exception as e:
            print(f"Error updating main app status: {e}")
    
    def _update_gui_status(self):
        """Update GUI with current monitor status"""
        try:
            current_time = datetime.now()
            
            # Only update every 2 seconds to avoid overwhelming the GUI
            if (self.last_gui_update is None or 
                (current_time - self.last_gui_update).total_seconds() >= 2):
                
                if self.monitor:
                    monitor_status = self.monitor.get_status()
                    
                    # Update main app if available
                    if self.main_app and hasattr(self.main_app, 'root'):
                        self.main_app.root.after(0, lambda: self._apply_gui_status_update(monitor_status))
                
                self.last_gui_update = current_time
                
        except Exception as e:
            print(f"Error updating GUI status: {e}")
    
    def _apply_gui_status_update(self, status: Dict):
        """Apply status updates to the GUI (runs in main thread)"""
        try:
            # Update connection status
            if hasattr(self.main_app, 'plc_connected'):
                self.main_app.plc_connected = status.get('connected', False)
            
            # Update cycle information
            if hasattr(self.main_app, 'current_cycle_number'):
                self.main_app.current_cycle_number = status.get('cycle_count', 0)
            
            # Update any monitor-specific status displays
            if hasattr(self.main_app, 'monitor_status_label'):
                running_status = "ACTIVE" if status.get('running', False) else "INACTIVE"
                self.main_app.monitor_status_label.config(text=f"Monitor: {running_status}")
                
        except Exception as e:
            print(f"Error applying GUI status update: {e}")
    
    def _process_gui_update(self, update: Dict):
        """Process GUI update requests"""
        try:
            update_type = update.get('type')
            
            if update_type == 'force_restart':
                self.force_cycle_restart()
            elif update_type == 'pause_monitoring':
                self.pause_monitoring()
            elif update_type == 'resume_monitoring':
                self.resume_monitoring()
            elif update_type == 'get_status':
                return self.get_monitor_status()
                
        except Exception as e:
            print(f"Error processing GUI update: {e}")
    
    # Callback implementations
    def _on_cycle_complete(self, status: Dict):
        """Callback for cycle completion"""
        self.monitor_status['last_cycle_complete'] = datetime.now()
        self.monitor_status['last_status'] = status
    
    def _on_cycle_start(self, cycle_num: int):
        """Callback for cycle start"""
        self.monitor_status['current_cycle'] = cycle_num
        self.monitor_status['cycle_start_time'] = datetime.now()
    
    def _on_status_change(self, status: Dict):
        """Callback for status changes"""
        self.monitor_status['current_plc_status'] = status
        self.monitor_status['last_status_change'] = datetime.now()
    
    def _on_error(self, error_msg: str):
        """Callback for errors"""
        self.monitor_status['last_error'] = error_msg
        self.monitor_status['last_error_time'] = datetime.now()
    
    # Public interface methods
    def force_cycle_restart(self):
        """Force a cycle restart"""
        try:
            if self.monitor:
                self.monitor.command_queue.put({'type': 'force_restart'})
                print("🔄 Force restart command sent to monitor")
        except Exception as e:
            print(f"Error forcing cycle restart: {e}")
    
    def pause_monitoring(self):
        """Pause the monitoring (but keep connection)"""
        try:
            if self.monitor:
                self.monitor.command_queue.put({'type': 'pause'})
                print("⏸️ Monitoring paused")
        except Exception as e:
            print(f"Error pausing monitoring: {e}")
    
    def resume_monitoring(self):
        """Resume the monitoring"""
        try:
            if self.monitor:
                self.monitor.command_queue.put({'type': 'resume'})
                print("▶️ Monitoring resumed")
        except Exception as e:
            print(f"Error resuming monitoring: {e}")
    
    def get_monitor_status(self) -> Dict:
        """Get current monitor status"""
        try:
            if self.monitor:
                return self.monitor.get_status()
            return {}
        except Exception as e:
            print(f"Error getting monitor status: {e}")
            return {}
    
    def is_monitoring_active(self) -> bool:
        """Check if monitoring is active"""
        return self.integration_active and (self.monitor is not None) and self.monitor.running
    
    def get_integration_status(self) -> Dict:
        """Get integration status information"""
        return {
            'integration_active': self.integration_active,
            'monitor_initialized': self.monitor is not None,
            'monitor_running': self.monitor.running if self.monitor else False,
            'monitor_connected': self.monitor.plc_connected if self.monitor else False,
            'last_update': self.last_gui_update.isoformat() if self.last_gui_update else None,
            'status': self.monitor_status
        }


# Convenience function for easy integration
def setup_process_monitoring(main_app_instance, config_file: str = None) -> ProcessMonitorIntegration:
    """
    Convenience function to set up process monitoring integration
    
    Args:
        main_app_instance: The main EOLTesterGUI instance
        config_file (str): Path to monitor configuration file
        
    Returns:
        ProcessMonitorIntegration: Configured integration instance
    """
    try:
        integration = ProcessMonitorIntegration(main_app_instance)
        
        if integration.initialize_monitor(config_file):
            print("✅ Process monitoring integration setup complete")
            return integration
        else:
            print("❌ Failed to setup process monitoring integration")
            return None
            
    except Exception as e:
        print(f"❌ Error setting up process monitoring: {e}")
        return None
