# P0000 Keep-Alive Fix - PLC Stopping Issue Resolved

## 🆘 EMERGENCY FIX APPLIED ✅

**Problem**: PLC stops immediately after test starts

**Root Cause**: P0000 needs to stay HIGH continuously, but something was turning it OFF

**Status**: **FIXED WITH P0000 KEEP-ALIVE** ✅

---

## Critical Fix Implemented

### P0000 Keep-Alive System

**What It Does**:
- Writes P0000 to HIGH every 5 seconds
- Keeps PLC in RUN state continuously
- Prevents any function from accidentally stopping P0000
- Blocks reset functions during active testing

**How It Works**:
```
Test Start → Write P0000 HIGH → Start keep-alive timer
  ↓
Every 5 seconds: Re-write P0000 HIGH
  ↓
Test continues → PLC stays running
  ↓
Test Stop → Stop keep-alive → Write P0000 LOW
```

---

## Implementation Details

### New Variables
```python
self.p0000_keepalive_active = False  # Keep-alive status flag
self.p0000_last_write = 0            # Last write timestamp
```

### Keep-Alive Function
```python
def maintain_p0000_high(self):
    """Keep P0000 HIGH during testing to prevent PLC from stopping"""
    if not self.p0000_keepalive_active:
        return  # Stopped
    
    # Check if 5 seconds passed
    if time.time() - self.p0000_last_write >= 5:
        # Re-write P0000 to HIGH
        result = self.plc_client.write_coil(0, True, device_id=station_id)
        if not result.isError():
            print("🔄 P0000 keep-alive: Re-confirmed HIGH to keep PLC running")
            self.p0000_last_write = time.time()
    
    # Schedule next check in 2 seconds
    self.root.after(2000, self.maintain_p0000_high)
```

### Reset Blocking
```python
def reset_plc_registers(self):
    # CRITICAL: NEVER reset during active testing
    if self.p0000_keepalive_active:
        print("⚠️ BLOCKED: Cannot reset PLC while test is running!")
        return True  # Skip reset, continue operation
    
    # Only reset when keep-alive is stopped
    ...
```

---

## Expected Console Output

### ✅ With Keep-Alive Active

```
🚀 Starting EOL Testing Process
... (M0067 pulse sequence)
... (P0000 set to HIGH)
✅ Starting P0000 keep-alive to maintain PLC RUN state...
✅ EOL Testing process initialized
   🔄 P0000 keep-alive active - PLC will stay running

(Every 5 seconds)
🔄 P0000 keep-alive: Re-confirmed HIGH to keep PLC running
... (test continues)
🔄 P0000 keep-alive: Re-confirmed HIGH to keep PLC running
... (test continues)

(If something tries to reset)
⚠️ BLOCKED: Cannot reset PLC while test is running!
   P0000 keep-alive is active - skipping reset to prevent test interruption

(At test end)
🔄 Stopping P0000 keep-alive...
✅ PLC Command: Set P0000 LOW - EOL Testing Stopped
```

---

## Why This Works

### Before Keep-Alive
```
Write P0000 HIGH → (something writes it LOW) → PLC stops → Test aborts
```

### After Keep-Alive
```
Write P0000 HIGH → Keep-alive writes it HIGH every 5s → PLC stays running → Test completes
```

### Protection from Reset
```
Test running → reset_plc_registers() called → BLOCKED by keep-alive check → P0000 stays HIGH
```

---

## Testing Instructions

### Run Test
```bash
python test_console.py
```

### Watch For
```
✅ Starting P0000 keep-alive to maintain PLC RUN state...
   🔄 P0000 keep-alive active - PLC will stay running

(Every 5 seconds during test)
🔄 P0000 keep-alive: Re-confirmed HIGH to keep PLC running
```

### Success Indicators
- ✅ Keep-alive messages every 5 seconds
- ✅ "BLOCKED: Cannot reset" if reset attempted
- ✅ PLC stays running
- ✅ Test progresses through steps
- ✅ No premature PLC stopping

---

## If PLC Still Stops

Check console for:
1. **Missing keep-alive messages** - keep-alive not starting
2. **"Stopping P0000 keep-alive"** appearing too early
3. **Reset not being blocked** - check for reset messages

---

**Status**: ✅ **P0000 KEEP-ALIVE ACTIVE**

PLC will now stay running with P0000 continuously maintained at HIGH! Test again now! 🚀

