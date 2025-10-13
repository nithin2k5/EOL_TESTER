# Quick Start Guide - Real PLC Mode

## ⚡ Fast Setup for Real-Time PLC Testing

---

## Step 1: Pre-flight Check ✈️

Before starting, verify:

```bash
# Check if PLC simulation mode is disabled
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('PLC Mode:', 'SIMULATION' if os.getenv('PLC_SIMULATION_MODE', 'false') == 'true' else 'REAL')"
```

Expected output: `PLC Mode: REAL`

---

## Step 2: Test PLC Connection 🔌

Run the connection test script:

```bash
python test_real_plc_connection.py
```

### Expected Results:
- ✅ Lists available COM ports
- ✅ Confirms your configured port (COM5) is available
- ✅ Connects to PLC successfully
- ✅ Reads test coils to verify communication
- ✅ Shows "PLC CONNECTION TEST: PASSED"

### If Test Fails:
1. **Check physical connections** - Cable, power, etc.
2. **Verify COM port** - Update `.env` if needed
3. **Close other applications** - Release the COM port
4. **Check PLC power** - Ensure PLC is ON and ready

---

## Step 3: Run the Main Application 🚀

```bash
python test_console_clone.py
```

### Startup Sequence:
1. **Configuration loads** from `.env`
2. **PLC connection attempt** on COM5
3. **Success message:** "✅ Real PLC connected successfully!"
4. **PLC indicator:** Green "● CONNECTED"

---

## Step 4: Begin Testing 🧪

1. **Employee Validation:**
   - Scan or enter employee code
   - Wait for validation

2. **Part Selection:**
   - Enter ALC code for the part
   - System loads specifications and image

3. **Start Testing:**
   - Click "START TESTING" button
   - System communicates with real PLC
   - Process status updates in real-time

4. **Monitor Results:**
   - Watch process status labels
   - View real-time data in specifications table
   - See test results appear in history

---

## Troubleshooting 🔧

### PLC Won't Connect

**Symptom:** Red "● DISCONNECTED" indicator

**Solutions:**
```bash
# 1. Check available ports
python -c "import serial.tools.list_ports; [print(p.device, p.description) for p in serial.tools.list_ports.comports()]"

# 2. Test specific port
python test_real_plc_connection.py

# 3. Verify .env configuration
notepad .env
```

### Application Crashes on Start

**Check:**
- Database is running (MySQL on localhost:3306)
- `.env` file exists and is properly formatted
- All required Python packages are installed

### No Data During Testing

**Verify:**
- PLC is in AUTO mode
- Process is actually running on PLC
- Registers are configured correctly in txt_files/

---

## Configuration Files 📁

### Main Config: `.env`
```ini
PLC_SIMULATION_MODE=false  # MUST be false for real PLC
PLC_COM_PORT=COM5
PLC_BAUD_RATE=38400
PLC_STATION_ID=1
```

### PLC Address Files: `txt_files/`
- `ProcessStatus.txt` - Process step addresses
- `HoldRegistersRead.txt` - Data register addresses
- `InputSensors.txt` - Sensor input addresses
- `EmployeeCodes.txt` - Authorized employee codes

---

## Key Differences from Demo Mode

| Feature | Demo Mode ❌ | Real PLC Mode ✅ |
|---------|-------------|------------------|
| PLC Required | No | **Yes** |
| Data Source | Random/Simulated | **Real Hardware** |
| Can run offline | Yes | **No** |
| Test accuracy | Simulated | **Actual** |
| Hardware wear | None | **Real operations** |

---

## Safety Notes ⚠️

When running in Real PLC Mode:

1. **Actual machine control** - Commands are sent to real hardware
2. **Physical movement** - Machine may move during testing
3. **Safety first** - Follow all safety protocols
4. **Emergency stop** - Ensure E-stop is accessible
5. **Authorized personnel** - Only trained operators

---

## Success Checklist ✓

Before starting production testing:

- [ ] PLC connection test passes
- [ ] Database connection verified
- [ ] Employee codes configured
- [ ] Part specifications loaded
- [ ] Machine is safe to operate
- [ ] Emergency stop tested
- [ ] Backup of data created
- [ ] All operators trained

---

## Quick Commands Reference

```bash
# Test PLC connection
python test_real_plc_connection.py

# Run main application
python test_console_clone.py

# Check configuration
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('Config:', os.getenv('PLC_SIMULATION_MODE'))"

# List COM ports
python -c "import serial.tools.list_ports; [print(p.device) for p in serial.tools.list_ports.comports()]"
```

---

## Need Help?

1. **Check logs** - Console output shows detailed status
2. **Review documentation** - See `REAL_PLC_MODE_CHANGES.md`
3. **Test connection** - Run `test_real_plc_connection.py`
4. **Verify config** - Check all `.env` settings

---

## 🎯 You're Ready!

Your system is now configured for **real-time PLC testing**. 

The application will:
- ✅ Connect to actual PLC hardware
- ✅ Read real sensor and register data
- ✅ Send actual control commands
- ✅ Save authentic test results

**Start testing with confidence!** 🚀






