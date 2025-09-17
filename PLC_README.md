# PLC Coil Reader

This project includes tools to connect to and read PLC (Programmable Logic Controller) coils and registers using COM Port 4.

## Files Overview

### `plc_coil_reader.py`
Main PLC communication module that provides:
- Connection establishment to PLC via COM4
- Reading of coils (digital inputs/outputs)
- Reading of input registers (analog inputs)
- Reading of holding registers
- Continuous monitoring capabilities
- Error handling and connection management

### `quick_plc_test.py`
Simple test script for:
- Quick connection testing
- Basic coil reading
- Input register testing
- Continuous monitoring mode

### `plc_config.json`
Configuration file containing:
- PLC connection settings (COM port, baudrate, station ID)
- Common addresses to monitor
- Monitoring settings

## Setup Requirements

1. **Python Dependencies:**
   ```bash
   pip install pymodbus pyserial
   ```

2. **Hardware Requirements:**
   - PLC connected to COM Port 4
   - RS-485 serial communication cable
   - Proper PLC configuration

## Usage

### Basic Connection Test
```python
from plc_coil_reader import PLCCoilReader

# Create PLC reader instance
plc = PLCCoilReader(com_port="COM4", baudrate=38400, station_id=1)

# Connect to PLC
if plc.establish_connection():
    print("Connected successfully!")
else:
    print("Connection failed!")
```

### Read Single Coil
```python
# Read coil at address 0
coil_value = plc.read_single_coil(0)
print(f"Coil 0: {'ON' if coil_value else 'OFF'}")
```

### Read Multiple Coils
```python
# Read 10 coils starting from address 100
coil_values = plc.read_multiple_coils(100, 10)
for i, value in enumerate(coil_values):
    print(f"Coil {100+i}: {'ON' if value else 'OFF'}")
```

### Read Input Registers
```python
# Read 4 input registers starting from address 0
registers = plc.read_input_registers(0, 4)
for i, value in enumerate(registers):
    print(f"Input Register {i}: {value}")
```

### Continuous Monitoring
```python
# Monitor specific addresses continuously
addresses_to_monitor = [0, 1, 100, 101]
plc.continuous_monitoring(addresses_to_monitor, interval=1.0)
```

### Quick Test
```bash
python quick_plc_test.py
```

### Monitoring Mode
```bash
python quick_plc_test.py monitor
```

## Configuration

Edit `plc_config.json` to customize:
- COM port settings
- Common addresses to monitor
- Monitoring intervals

## Error Handling

The module includes comprehensive error handling for:
- Connection failures
- Communication timeouts
- Invalid addresses
- PLC not responding

## PLC Connection Settings

Default settings:
- **COM Port:** COM4
- **Baudrate:** 38400
- **Station ID:** 1
- **Data Bits:** 8
- **Parity:** None
- **Stop Bits:** 1
- **Timeout:** 1 second

## Common Issues

1. **Connection Failed:**
   - Check COM port number
   - Verify baudrate settings
   - Ensure PLC is powered on
   - Check cable connections

2. **No Response from PLC:**
   - Verify station ID
   - Check PLC communication settings
   - Ensure proper protocol (Modbus RTU)

3. **Permission Errors:**
   - Run as administrator (Windows)
   - Check COM port permissions

## Integration with Existing Code

The `PLCCoilReader` class can be easily integrated with the existing `test_console.py`:

```python
from plc_coil_reader import PLCCoilReader

# In your existing code
plc_reader = PLCCoilReader()
if plc_reader.establish_connection():
    # Use plc_reader methods for coil/register reading
    coil_value = plc_reader.read_single_coil(address)
```

## Troubleshooting

### Check Available COM Ports
```python
import serial.tools.list_ports
ports = list(serial.tools.list_ports.comports())
for port in ports:
    print(f"Available: {port.device} - {port.description}")
```

### Test Serial Connection
```python
import serial
try:
    ser = serial.Serial('COM4', 38400, timeout=1)
    print("Serial port opened successfully")
    ser.close()
except Exception as e:
    print(f"Serial error: {e}")
```


