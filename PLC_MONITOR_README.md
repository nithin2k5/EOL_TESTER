# PLC Monitor Module

A standalone, reusable module for PLC coil monitoring and GUI label updates in EOL testing applications.

## 📁 Files Created

1. **`plc_monitor.py`** - Main PLC monitoring module
2. **`plc_monitor_example.py`** - Complete example application
3. **`PLC_MONITOR_README.md`** - This documentation

## 🎯 Features

### PLCMonitor Class

- ✅ **PLC Connection Management**
  - TCP and Serial Modbus support
  - Automatic reconnection
  - Connection health monitoring

- ✅ **Coil Reading**
  - Individual coil reads (M registers)
  - 100ms delay between reads to prevent PLC overload
  - Error handling and retry logic

- ✅ **Label Updates**
  - Automatic GUI label color updates
  - Green = Active/Visited
  - Blue = Not visited
  - Tracks step progression

- ✅ **P0000 Keep-Alive**
  - Maintains P0000 HIGH during testing
  - Refreshes every 5 seconds
  - Prevents PLC from halting

- ✅ **Step Tracking**
  - Tracks which steps have been visited
  - Detects step transitions
  - Progress calculation

- ✅ **Callbacks**
  - `on_status_change` - Called when PLC status changes
  - `on_step_complete` - Called when a step completes

## 🚀 Quick Start

### 1. Basic Usage

```python
import tkinter as tk
from plc_monitor import PLCMonitor

# Create window and labels
root = tk.Tk()
status_labels = {
    'auto': tk.Label(root, text="AUTO", bg="#00BFFF"),
    'home': tk.Label(root, text="HOME", bg="#00BFFF"),
    # ... more labels
}

# Create monitor
monitor = PLCMonitor(root, status_labels)

# Load addresses
monitor.load_process_addresses()

# Connect to PLC
if monitor.connect_to_plc():
    # Start monitoring
    monitor.start_monitoring()
    
    # Start keep-alive
    monitor.start_p0000_keepalive()
```

### 2. With Callbacks

```python
def on_status_change(status_values, active_step):
    print(f"Status changed: {active_step} active")

def on_step_complete(address, label_key, step_num):
    print(f"Step {step_num} complete: {address}")

monitor.on_status_change = on_status_change
monitor.on_step_complete = on_step_complete
```

### 3. Track Progress

```python
progress = monitor.get_progress()
print(f"Progress: {progress['visited_steps']}/{progress['total_steps']}")
print(f"Visited: {progress['visited_addresses']}")
print(f"Remaining: {progress['remaining_steps']}")
```

## 📋 Configuration

### Environment Variables (.env)

```bash
# PLC Connection Settings
PLC_COM_PORT=COM5
PLC_BAUD_RATE=38400
PLC_STATION_ID=1

# TCP Settings (optional)
MODBUS_TCP_IP=192.168.1.100
MODBUS_TCP_PORT=502
```

### Process Addresses File

Create `txt_files/ProcessStatus.txt`:
```
M0067,M0068,M0076,M0085,M0078,M0087,M0075,M0079
```

## 🔧 API Reference

### PLCMonitor Class

#### Initialization
```python
monitor = PLCMonitor(root, status_labels)
```

**Parameters:**
- `root` - Tkinter root window
- `status_labels` - Dictionary of label widgets

#### Methods

**Connection**
```python
monitor.connect_to_plc()           # Connect to PLC
monitor.disconnect_plc()           # Disconnect from PLC
```

**Reading/Writing**
```python
status = monitor.read_plc_coils()  # Returns {address: True/False}
monitor.write_plc_coil(address, value)  # Write to coil
```

**Monitoring**
```python
monitor.start_monitoring()         # Start monitoring loop
monitor.stop_monitoring()          # Stop monitoring loop
monitor.monitoring_interval = 2000 # Set interval (ms)
```

**Keep-Alive**
```python
monitor.start_p0000_keepalive()   # Start P0000 keep-alive
monitor.stop_p0000_keepalive()    # Stop P0000 keep-alive
```

**Progress**
```python
monitor.get_progress()            # Get progress dict
monitor.reset_step_tracking()     # Reset for new cycle
```

**Callbacks**
```python
monitor.on_status_change = func   # Set status change callback
monitor.on_step_complete = func   # Set step complete callback
```

### Callback Signatures

```python
def on_status_change(status_values: dict, active_step: str):
    """
    Called when PLC status changes
    
    Args:
        status_values: Dict of {address: True/False}
        active_step: Currently active step address
    """
    pass

def on_step_complete(address: str, label_key: str, step_num: int):
    """
    Called when a step completes
    
    Args:
        address: Step address (e.g., "M0067")
        label_key: Label name (e.g., "auto")
        step_num: Step number (1-8)
    """
    pass
```

## 🎨 Label Color Scheme

| Color | Meaning | When Applied |
|-------|---------|--------------|
| **Blue (#00BFFF)** | Not visited | Default state |
| **Green** | Active or Visited | When step is HIGH or completed |

## 📊 Process Addresses Mapping

Default mapping (configurable via ProcessStatus.txt):

| Index | Address | Label | Description |
|-------|---------|-------|-------------|
| 0 | M0067 | auto | AUTO mode |
| 1 | M0068 | home | HOME position |
| 2 | M0076 | 1st | 1st PULL (Load Test) |
| 3 | M0085 | 2nd | 2nd PULL (Length Test) |
| 4 | M0078 | test | TEST RESULT |
| 5 | M0087 | - | Additional step |
| 6 | M0075 | - | PASS result |
| 7 | M0079 | - | NG result |

## 🧪 Running the Example

### Test with PLC
```bash
python plc_monitor_example.py
```

### Test Standalone Monitor
```bash
python plc_monitor.py
```

The standalone version includes a built-in test GUI.

## 🔄 Integration with test_console.py

To use in your existing application:

```python
from plc_monitor import PLCMonitor

class EOLTesterGUI:
    def __init__(self, root):
        # ... existing code ...
        
        # Replace PLC code with PLCMonitor
        self.plc_monitor = PLCMonitor(root, self.process_status_labels)
        self.plc_monitor.load_process_addresses()
        
        # Set callbacks
        self.plc_monitor.on_status_change = self.handle_plc_status_change
        self.plc_monitor.on_step_complete = self.handle_step_complete
    
    def start_eol_testing_process(self):
        # Connect and start monitoring
        if self.plc_monitor.connect_to_plc():
            self.plc_monitor.start_monitoring()
            self.plc_monitor.start_p0000_keepalive()
    
    def handle_plc_status_change(self, status_values, active_step):
        # Your custom logic here
        pass
    
    def handle_step_complete(self, address, label_key, step_num):
        # Your custom logic here
        pass
```

## ⚠️ Important Notes

### Keep-Alive Behavior
- P0000 is written HIGH when keep-alive starts
- Re-written every 5 seconds to maintain HIGH
- Prevents PLC from halting during test
- Must be stopped explicitly to end test

### Read Timing
- 100ms delay between individual coil reads
- Prevents PLC communication overload
- Configurable via `time.sleep()` in `read_plc_coils()`

### Connection Recovery
- Automatic reconnection on socket close
- Error counter tracks consecutive failures
- After 5 errors, manual intervention required

## 🐛 Troubleshooting

### PLC Won't Connect
1. Check COM port in `.env` file
2. Verify PLC is powered on
3. Check cable connections
4. Try both TCP and Serial

### Labels Not Updating
1. Ensure `status_labels` dict is correct
2. Check `process_addresses` are loaded
3. Verify monitoring is started
4. Check PLC coils are actually changing

### PLC Keeps Halting
1. Verify keep-alive is started
2. Check P0000 is being written
3. Ensure `p0000_keepalive_active = True`
4. Monitor console for keep-alive messages

### Steps Not Being Tracked
1. Check `process_addresses` file exists
2. Verify addresses match PLC configuration
3. Ensure callbacks are set
4. Check console for step detection messages

## 📝 Example Output

Console output when running:
```
PLC Monitor initialized
Loaded 8 process addresses: ['M0067', 'M0068', ...]
Connecting to PLC...
✅ PLC connected via TCP: 192.168.1.100:502
✅ PLC monitoring started
✅ P0000 keep-alive started
🎯 NEW STEP: M0067 (auto) - Step 1/8
✅ auto → GREEN (active)
🔄 Keep-alive: P0000 refreshed HIGH
📍 Step transition: M0067 → M0068
🎯 NEW STEP: M0068 (home) - Step 2/8
...
```

## 📚 Additional Resources

- See `test_console.py` for full implementation example
- Check `.env.example` for configuration template
- Refer to Modbus documentation for protocol details

## 🔐 License

Same license as the main EOL_TESTER project.

---

**Created:** 2025-01-13  
**Version:** 1.0  
**Author:** EOL Testing Team


