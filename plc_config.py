"""
PLC Process Controller Configuration
Adjust these settings for your specific PLC setup
"""

# PLC Connection Settings
PLC_SETTINGS = {
    'com_port': 'COM3',           # Change to your PLC COM port
    'baud_rate': 115200,          # Change to your PLC baud rate  
    'station_id': 1,              # Change to your PLC station ID
    'timeout': 1.0,               # Communication timeout in seconds
}

# Process Control Settings
PROCESS_SETTINGS = {
    'step_duration': 3.0,         # How long each step runs (seconds)
    'cycle_delay': 2.0,           # Delay between cycles (seconds)
    'max_manual_cycles': 20,      # Safety limit for manual mode
    'monitor_timeout': 30.0,      # How long to monitor in auto mode (seconds)
}

# Process Steps Configuration  
PROCESS_STEPS = {
    'addresses': [
        'M0067',  # AUTO
        'M0068',  # HOME
        'M0076',  # 1st PULL PASS
        'M0085',  # 1st PULL NG
        'M0078',  # 2nd PULL PASS
        'M0087',  # 2nd PULL NG
        'M0075',  # TEST RESULT PASS
        'M0079',  # TEST RESULT NG
    ],
    'names': [
        'AUTO',
        'HOME', 
        '1st PULL PASS',
        '1st PULL NG',
        '2nd PULL PASS',
        '2nd PULL NG',
        'TEST RESULT PASS',
        'TEST RESULT NG',
    ]
}

# Control registers
CONTROL_REGISTERS = {
    'plc_enable': 'P0000',        # Main PLC enable (P0000)
    'test_pass': 'M0075',         # Test result PASS
    'test_ng': 'M0079',           # Test result NG
}

# Logging Settings
LOGGING_SETTINGS = {
    'log_level': 'INFO',          # DEBUG, INFO, WARNING, ERROR
    'log_to_file': True,          # Save logs to file
    'log_filename': 'plc_controller.log',
    'show_timestamps': True,      # Include timestamps in output
}

def get_plc_settings():
    """Get PLC connection settings"""
    return PLC_SETTINGS.copy()

def get_process_settings():
    """Get process control settings"""  
    return PROCESS_SETTINGS.copy()

def get_process_steps():
    """Get process steps configuration"""
    return PROCESS_STEPS.copy()

def get_control_registers():
    """Get control register addresses"""
    return CONTROL_REGISTERS.copy()

def get_logging_settings():
    """Get logging configuration"""
    return LOGGING_SETTINGS.copy()
