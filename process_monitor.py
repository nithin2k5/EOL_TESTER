"""
Process Status Monitor for EOL Testing System
============================================

This module provides continuous monitoring of PLC process status and automatically
restarts testing cycles when a cycle is completed. It works independently of the
main GUI and can run as a background service.

Features:
- Real-time PLC status monitoring
- Automatic cycle completion detection
- Intelligent restart logic
- Configurable monitoring parameters
- Logging and error handling
- Integration with main test console

Author: EOL Testing System
Version: 1.0
"""

import time
import threading
import json
import os
from datetime import datetime, timedelta
from pymodbus.client import ModbusSerialClient, ModbusTcpClient
from dotenv import load_dotenv
import logging
from typing import Dict, List, Optional, Callable
import queue


class ProcessStatusMonitor:
    """
    Monitors PLC process status and manages automatic cycle restarts
    """
    
    def __init__(self, config_file: str = None):
        """
        Initialize the Process Status Monitor
        
        Args:
            config_file (str): Path to configuration file (optional)
        """
        self.config_file = config_file or "process_monitor_config.json"
        self.running = False
        self.monitoring_thread = None
        self.plc_client = None
        self.plc_connected = False
        
        # Monitoring parameters
        self.monitor_interval = 1.0  # seconds
        self.cycle_timeout = 300  # 5 minutes max per cycle
        self.restart_delay = 5.0  # seconds between cycles
        self.max_consecutive_failures = 3
        
        # Process status tracking
        self.current_cycle_start = None
        self.cycle_count = 0
        self.consecutive_failures = 0
        self.last_status_values = {}
        self.cycle_completion_detected = False
        
        # Callback functions
        self.on_cycle_complete = None
        self.on_cycle_start = None
        self.on_error = None
        self.on_status_change = None
        
        # Status queue for communication with main application
        self.status_queue = queue.Queue()
        self.command_queue = queue.Queue()
        
        # Load configuration
        self.load_configuration()
        self.setup_logging()
        self.load_plc_config()
        
        print("Process Status Monitor initialized")
    
    def load_configuration(self):
        """Load monitoring configuration from file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                
                self.monitor_interval = config.get('monitor_interval', 1.0)
                self.cycle_timeout = config.get('cycle_timeout', 300)
                self.restart_delay = config.get('restart_delay', 5.0)
                self.max_consecutive_failures = config.get('max_consecutive_failures', 3)
                
                print(f"Configuration loaded from {self.config_file}")
            else:
                # Create default configuration
                self.create_default_config()
                print(f"Created default configuration: {self.config_file}")
                
        except Exception as e:
            print(f"Error loading configuration: {e}")
            print("Using default configuration")
    
    def create_default_config(self):
        """Create default configuration file"""
        default_config = {
            "monitor_interval": 1.0,
            "cycle_timeout": 300,
            "restart_delay": 5.0,
            "max_consecutive_failures": 3,
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
        }
        
        try:
            with open(self.config_file, 'w') as f:
                json.dump(default_config, f, indent=4)
        except Exception as e:
            print(f"Error creating default config: {e}")
    
    def setup_logging(self):
        """Setup logging for the monitor"""
        try:
            # Create logs directory if it doesn't exist
            os.makedirs('logs', exist_ok=True)
            
            # Configure logging with UTF-8 encoding
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                handlers=[
                    logging.FileHandler('logs/process_monitor.log', encoding='utf-8'),
                    logging.StreamHandler()
                ]
            )
            
            self.logger = logging.getLogger('ProcessMonitor')
            self.logger.info("Process Monitor logging initialized")
            
        except Exception as e:
            print(f"Error setting up logging: {e}")
            # Fallback to print statements
            self.logger = None
    
    def log(self, message: str, level: str = "INFO"):
        """Log a message"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatted_message = f"[{timestamp}] {level}: {message}"
        
        if self.logger:
            if level == "ERROR":
                self.logger.error(message)
            elif level == "WARNING":
                self.logger.warning(message)
            elif level == "DEBUG":
                self.logger.debug(message)
            else:
                self.logger.info(message)
        else:
            print(formatted_message)
    
    def load_plc_config(self):
        """Load PLC configuration from environment variables"""
        try:
            # Load environment variables
            load_dotenv()
            
            # PLC connection settings
            self.plc_com_port = os.getenv('PLC_COM_PORT', 'COM5').strip("'")
            self.plc_baud_rate = int(os.getenv('PLC_BAUD_RATE', '38400'))
            self.plc_station_id = int(os.getenv('PLC_STATION_ID', '1'))
            
            # TCP settings (if available)
            self.plc_tcp_ip = os.getenv('MODBUS_TCP_IP', '').strip("'")
            self.plc_tcp_port = int(os.getenv('MODBUS_TCP_PORT', '502')) if os.getenv('MODBUS_TCP_PORT') else 502
            
            self.log(f"PLC Config - COM: {self.plc_com_port}, Baud: {self.plc_baud_rate}, Station: {self.plc_station_id}")
            
        except Exception as e:
            self.log(f"Error loading PLC configuration: {e}", "ERROR")
            # Set defaults
            self.plc_com_port = 'COM5'
            self.plc_baud_rate = 38400
            self.plc_station_id = 1
            self.plc_tcp_ip = ''
            self.plc_tcp_port = 502
    
    def connect_to_plc(self) -> bool:
        """Connect to PLC for monitoring"""
        try:
            if self.plc_connected:
                return True
            
            self.log("Attempting to connect to PLC...")
            
            # Try TCP connection first if IP is configured
            if self.plc_tcp_ip:
                try:
                    self.plc_client = ModbusTcpClient(
                        host=self.plc_tcp_ip,
                        port=self.plc_tcp_port,
                        timeout=5
                    )
                    if self.plc_client.connect():
                        self.plc_connected = True
                        self.log(f"PLC connected via TCP - {self.plc_tcp_ip}:{self.plc_tcp_port}")
                        return True
                except Exception as e:
                    self.log(f"TCP connection failed: {e}", "WARNING")
            
            # Try serial connection with multiple ports
            available_ports = self.get_available_ports()
            if not available_ports:
                self.log("No COM ports available", "ERROR")
                return False
            
            # Try configured port first
            ports_to_try = [self.plc_com_port] if self.plc_com_port in available_ports else []
            # Then try other available ports
            for port in available_ports:
                if port not in ports_to_try:
                    ports_to_try.append(port)
            
            for port in ports_to_try:
                try:
                    self.log(f"Trying to connect to {port}...")
                    self.plc_client = ModbusSerialClient(
                        port=port,
                        baudrate=self.plc_baud_rate,
                        bytesize=8,
                        parity='N',
                        stopbits=1,
                        timeout=5
                    )
                    if self.plc_client.connect():
                        self.plc_connected = True
                        self.plc_com_port = port  # Update to working port
                        self.log(f"PLC connected via Serial - {port}")
                        return True
                    else:
                        if self.plc_client:
                            self.plc_client.close()
                except Exception as e:
                    self.log(f"Failed to connect to {port}: {e}", "WARNING")
                    if hasattr(self, 'plc_client') and self.plc_client:
                        try:
                            self.plc_client.close()
                        except:
                            pass
            
            self.log("Serial connection failed on all available ports", "ERROR")
            return False
                
        except Exception as e:
            self.log(f"Error connecting to PLC: {e}", "ERROR")
            return False
    
    def get_available_ports(self):
        """Get list of available COM ports"""
        try:
            import serial.tools.list_ports
            ports = [port.device for port in serial.tools.list_ports.comports()]
            return ports
        except Exception as e:
            self.log(f"Error getting COM ports: {e}", "ERROR")
            return []
    
    def disconnect_plc(self):
        """Disconnect from PLC"""
        try:
            if self.plc_client and self.plc_connected:
                self.plc_client.close()
                self.plc_connected = False
                self.log("PLC disconnected")
        except Exception as e:
            self.log(f"Error disconnecting PLC: {e}", "ERROR")
    
    def read_process_status(self) -> Dict[str, bool]:
        """Read current process status from PLC"""
        if not self.plc_connected or not self.plc_client:
            return {}
        
        try:
            # Read holding registers for process status
            # This is a simplified example - adjust addresses based on your PLC configuration
            status_values = {}
            
            # Read multiple registers at once for efficiency
            result = self.plc_client.read_holding_registers(address=0, count=10)
            
            if not result.isError():
                registers = result.registers
                
                # Map register values to status names (adjust mapping as needed)
                status_mapping = {
                    0: "AUTO",
                    1: "HOME", 
                    2: "PULL1_OK",
                    3: "PULL1_NG",
                    4: "PULL2_OK", 
                    5: "PULL2_NG",
                    6: "TESTRESULT_OK",
                    7: "TESTRESULT_NG"
                }
                
                for reg_index, status_name in status_mapping.items():
                    if reg_index < len(registers):
                        status_values[status_name] = bool(registers[reg_index])
                
                return status_values
            else:
                self.log(f"Error reading PLC registers: {result}", "ERROR")
                return {}
                
        except Exception as e:
            self.log(f"Error reading process status: {e}", "ERROR")
            return {}
    
    def detect_cycle_completion(self, current_status: Dict[str, bool]) -> bool:
        """Detect if a testing cycle has been completed"""
        try:
            # Check for cycle completion indicators
            cycle_complete = (
                current_status.get("TESTRESULT_OK", False) or 
                current_status.get("TESTRESULT_NG", False)
            )
            
            # Additional logic: cycle is complete if we were in progress and now have results
            if cycle_complete and not self.cycle_completion_detected:
                self.log("Cycle completion detected!")
                return True
            
            return False
            
        except Exception as e:
            self.log(f"Error detecting cycle completion: {e}", "ERROR")
            return False
    
    def detect_cycle_start(self, current_status: Dict[str, bool]) -> bool:
        """Detect if a new testing cycle has started"""
        try:
            # Cycle starts when AUTO mode is activated and no cycle is currently active
            cycle_started = current_status.get("AUTO", False)

            # Only start new cycle if:
            # 1. AUTO is on
            # 2. No cycle is currently active (current_cycle_start is None)
            # 3. Previous cycle (if any) has been completed
            if cycle_started and self.current_cycle_start is None and self.cycle_completion_detected:
                self.log("New cycle detected - starting monitoring")
                return True

            return False

        except Exception as e:
            self.log(f"Error detecting cycle start: {e}", "ERROR")
            return False
    
    def restart_cycle(self):
        """Restart the testing cycle for continuous operation"""
        try:
            self.log(f"Restarting testing cycle #{self.cycle_count + 1}...")

            # Reset cycle tracking for continuous operation
            self.cycle_completion_detected = False
            self.current_cycle_start = datetime.now()
            self.cycle_count += 1

            # Send restart command to PLC (adjust based on your PLC logic)
            if self.plc_connected and self.plc_client:
                try:
                    # Method 1: Send AUTO signal to start cycle
                    auto_result = self.plc_client.write_coil(address=67, value=True)  # M0067 = AUTO
                    if not auto_result.isError():
                        self.log("AUTO signal sent to PLC - cycle starting")
                        time.sleep(0.5)  # Brief pulse

                        # Optional: Send additional restart register command
                        restart_result = self.plc_client.write_register(address=100, value=1)
                        if not restart_result.isError():
                            self.log("Restart command sent to PLC")
                            time.sleep(0.5)
                            self.plc_client.write_register(address=100, value=0)
                    else:
                        self.log(f"Failed to send AUTO command: {auto_result}", "WARNING")

                except Exception as plc_error:
                    self.log(f"PLC restart command error: {plc_error}", "WARNING")
                    # Continue anyway - cycle might start automatically

            # Reset consecutive failures on successful restart
            self.consecutive_failures = 0

            # Notify callback if set
            if self.on_cycle_start:
                self.on_cycle_start(self.cycle_count)

            # Add to status queue
            self.status_queue.put({
                'type': 'cycle_restart',
                'cycle_count': self.cycle_count,
                'timestamp': datetime.now()
            })

            self.log(f"Cycle #{self.cycle_count} initiated successfully - monitoring for completion")

        except Exception as e:
            self.log(f"Error restarting cycle: {e}", "ERROR")
            self.consecutive_failures += 1
    
    def check_cycle_timeout(self):
        """Check if current cycle has timed out"""
        if self.current_cycle_start is None:
            return False
        
        elapsed = datetime.now() - self.current_cycle_start
        if elapsed.total_seconds() > self.cycle_timeout:
            self.log(f"Cycle timeout detected! Elapsed: {elapsed.total_seconds():.1f}s", "WARNING")
            return True
        
        return False
    
    def monitoring_loop(self):
        """Main monitoring loop"""
        self.log("Starting process monitoring loop")
        
        while self.running:
            try:
                # Check for commands from main application
                try:
                    command = self.command_queue.get_nowait()
                    self.process_command(command)
                except queue.Empty:
                    pass
                
                # Ensure PLC connection
                if not self.plc_connected:
                    if not self.connect_to_plc():
                        time.sleep(5)  # Wait before retry
                        continue
                
                # Read current process status
                current_status = self.read_process_status()
                
                if current_status:
                    # Check for status changes
                    if current_status != self.last_status_values:
                        self.log(f"Status change: {current_status}")
                        self.last_status_values = current_status.copy()
                        
                        # Notify callback if set
                        if self.on_status_change:
                            self.on_status_change(current_status)
                    
                    # Detect cycle start (only if no cycle is currently active)
                    if self.detect_cycle_start(current_status) and not self.current_cycle_start:
                        self.current_cycle_start = datetime.now()
                        self.cycle_completion_detected = False

                    # Detect cycle completion and handle continuous cycling
                    if self.detect_cycle_completion(current_status):
                        self.cycle_completion_detected = True

                        # Determine result
                        result = "PASS" if current_status.get("TESTRESULT_OK", False) else "FAIL"
                        self.log(f"Cycle #{self.cycle_count} completed: {result}")

                        # Notify callback if set
                        if self.on_cycle_complete:
                            self.on_cycle_complete(current_status)

                        # Add to status queue
                        self.status_queue.put({
                            'type': 'cycle_complete',
                            'status': current_status,
                            'cycle_count': self.cycle_count,
                            'result': result,
                            'timestamp': datetime.now()
                        })

                        # Wait before restarting next cycle
                        self.log(f"Waiting {self.restart_delay}s before next cycle...")
                        time.sleep(self.restart_delay)

                        # Restart cycle automatically for continuous operation
                        self.restart_cycle()
                    
                    # Check for cycle timeout
                    if self.check_cycle_timeout():
                        self.log("Restarting due to timeout")
                        self.restart_cycle()
                
                # Sleep until next monitoring interval
                time.sleep(self.monitor_interval)
                
            except Exception as e:
                self.log(f"Error in monitoring loop: {e}", "ERROR")
                self.consecutive_failures += 1
                
                if self.consecutive_failures >= self.max_consecutive_failures:
                    self.log(f"Too many consecutive failures ({self.consecutive_failures}). Stopping monitor.", "ERROR")
                    break
                
                time.sleep(5)  # Wait before retry
        
        self.log("Monitoring loop stopped")
    
    def process_command(self, command: Dict):
        """Process commands from main application"""
        try:
            cmd_type = command.get('type')
            
            if cmd_type == 'start_monitoring':
                self.log("Start monitoring command received")
                # Already running, just acknowledge
                
            elif cmd_type == 'stop_monitoring':
                self.log("Stop monitoring command received")
                self.stop_monitoring()
                
            elif cmd_type == 'force_restart':
                self.log("Force restart command received")
                self.restart_cycle()
                
            elif cmd_type == 'get_status':
                # Return current status
                self.status_queue.put({
                    'type': 'status_response',
                    'connected': self.plc_connected,
                    'running': self.running,
                    'cycle_count': self.cycle_count,
                    'current_status': self.last_status_values
                })
            
        except Exception as e:
            self.log(f"Error processing command: {e}", "ERROR")
    
    def start_monitoring(self) -> bool:
        """Start the monitoring process"""
        try:
            if self.running:
                self.log("Monitor is already running")
                return True
            
            # Connect to PLC first
            if not self.connect_to_plc():
                self.log("Failed to connect to PLC", "ERROR")
                return False
            
            self.running = True
            self.consecutive_failures = 0
            
            # Start monitoring thread
            self.monitoring_thread = threading.Thread(target=self.monitoring_loop, daemon=True)
            self.monitoring_thread.start()
            
            self.log("Process monitoring started")

            # Initialize for continuous cycling
            self.cycle_completion_detected = True  # Allow first cycle to start
            self.log("Continuous cycling initialized - ready for first cycle")

            return True
            
        except Exception as e:
            self.log(f"Error starting monitoring: {e}", "ERROR")
            return False
    
    def stop_monitoring(self):
        """Stop the monitoring process"""
        try:
            self.running = False
            
            if self.monitoring_thread and self.monitoring_thread.is_alive():
                self.monitoring_thread.join(timeout=5)
            
            self.disconnect_plc()
            self.log("Process monitoring stopped")
            
        except Exception as e:
            self.log(f"Error stopping monitoring: {e}", "ERROR")
    
    def get_status(self) -> Dict:
        """Get current monitor status"""
        return {
            'running': self.running,
            'connected': self.plc_connected,
            'cycle_count': self.cycle_count,
            'consecutive_failures': self.consecutive_failures,
            'current_cycle_start': self.current_cycle_start.isoformat() if self.current_cycle_start else None,
            'last_status': self.last_status_values
        }
    
    def set_callbacks(self, on_cycle_complete: Callable = None, on_cycle_start: Callable = None, 
                     on_error: Callable = None, on_status_change: Callable = None):
        """Set callback functions for events"""
        self.on_cycle_complete = on_cycle_complete
        self.on_cycle_start = on_cycle_start
        self.on_error = on_error
        self.on_status_change = on_status_change


def main():
    """Main function for standalone continuous cycling operation"""
    print("🚀 Starting Process Status Monitor - CONTINUOUS CYCLING MODE")
    print("=" * 60)

    # Create monitor instance
    monitor = ProcessStatusMonitor()

    # Set up callbacks with enhanced logging
    def on_cycle_complete(status):
        result = "PASS" if status.get("TESTRESULT_OK", False) else "FAIL"
        print(f"✅ CYCLE #{monitor.cycle_count} COMPLETED: {result}")
        print(f"   Status: {status}")
        print("-" * 40)

    def on_cycle_start(cycle_num):
        print(f"🚀 STARTING CYCLE #{cycle_num}")
        print(f"   Time: {datetime.now().strftime('%H:%M:%S')}")

    def on_status_change(status):
        # Only log significant status changes
        active_statuses = {k: v for k, v in status.items() if v}
        if active_statuses:
            print(f"   📊 Status: {active_statuses}")

    monitor.set_callbacks(
        on_cycle_complete=on_cycle_complete,
        on_cycle_start=on_cycle_start,
        on_status_change=on_status_change
    )

    # Display configuration
    print(f"Configuration:")
    print(f"  - Cycle Timeout: {monitor.cycle_timeout}s")
    print(f"  - Restart Delay: {monitor.restart_delay}s")
    print(f"  - Monitor Interval: {monitor.monitor_interval}s")
    print(f"  - Max Failures: {monitor.max_consecutive_failures}")
    print()

    # Start monitoring
    if monitor.start_monitoring():
        try:
            print("🔄 CONTINUOUS MONITORING ACTIVE")
            print("Cycles will run automatically until manually stopped")
            print("Press Ctrl+C to stop monitoring")
            print("=" * 60)

            # Status display loop
            last_cycle_count = 0
            start_time = datetime.now()

            while monitor.running:
                time.sleep(5)  # Update every 5 seconds

                # Display periodic status
                current_time = datetime.now()
                elapsed = current_time - start_time
                stats = monitor.get_status()

                if stats['cycle_count'] != last_cycle_count:
                    print(f"[{current_time.strftime('%H:%M:%S')}] Runtime: {elapsed}, Total Cycles: {stats['cycle_count']}")
                    last_cycle_count = stats['cycle_count']

        except KeyboardInterrupt:
            print(f"\n{'=' * 60}")
            print("🛑 STOPPING CONTINUOUS MONITORING...")

            # Display final statistics
            stats = monitor.get_status()
            end_time = datetime.now()
            total_runtime = end_time - start_time

            print(f"Final Statistics:")
            print(f"  - Total Runtime: {total_runtime}")
            print(f"  - Total Cycles Completed: {stats['cycle_count']}")
            if stats['cycle_count'] > 0:
                avg_cycle_time = total_runtime.total_seconds() / stats['cycle_count']
                print(f"  - Average Cycle Time: {avg_cycle_time:.1f}s")
            print(f"  - Consecutive Failures: {stats['consecutive_failures']}")

            monitor.stop_monitoring()
            print("✅ Monitor stopped successfully")

    else:
        print("❌ Failed to start monitoring")


if __name__ == "__main__":
    main()
