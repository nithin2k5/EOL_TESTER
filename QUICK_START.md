# EOL Tester - Quick Start Guide

## 🚀 Launch Application

```bash
python test_console.py
```

---

## 📋 Testing Workflow

### Step 1: Employee Validation
- **Enter Employee ID:** `S041`
- **Press:** `Enter`
- **Expected:** ✅ Green validation message

### Step 2: Load Part
- **Enter ALC Code:** `sample2`
- **Press:** `Enter`
- **Expected:** ✅ Part loaded, START TESTING button enabled

### Step 3: Start Test
- **Click:** `START TESTING` button
- **Expected:** ✅ PLC monitoring begins, process labels update

### Step 4: Monitor Test
- **Watch:** Process status labels turn GREEN as each step activates
- **Labels:** AUTO → HOME → 1st PULL → 2nd PULL → TEST RESULT
- **Expected:** ✅ Real-time updates from PLC

### Step 5: Test Completion
- **Automatic:** Test completes based on PLC readings
- **Expected:** ✅ Results saved to database automatically

---

## 🔧 Automated Test Sequence

```bash
python execute_test_sequence.py
```

**This will:**
1. Validate Employee S041
2. Load Part sample2
3. Generate lot number
4. Monitor PLC for 60 seconds
5. Save test results

---

## ⚙️ Configuration

### Database Settings
- **Host:** localhost
- **Port:** 3306
- **User:** root
- **Password:** 12345
- **Database:** EOL

### PLC Settings
- **COM Port:** COM5
- **Baud Rate:** 38400
- **Station ID:** 1

### Test Data
- **Employee ID:** S041
- **ALC Code:** sample2
- **Part Number:** sampel2

---

## 🎯 Process Status Labels

Labels change color to indicate status:

| Color | Status | Meaning |
|-------|--------|---------|
| 🔵 Blue (#00BFFF) | Ready/Completed | Step not active or already completed |
| 🟢 Green | Active | Step currently executing (PLC coil HIGH) |

**Process Steps:**
1. **AUTO** - Automatic mode activated
2. **HOME** - Return to home position
3. **1st PULL** - First pull test
4. **2nd PULL** - Second pull test
5. **TEST RESULT** - Final result determination

---

## 📊 Test Specifications

The system monitors and validates:

1. **LOAD (KGS)**
   - Range: 100-200
   - Device: Load cell

2. **LENGTH (MM)**
   - Range: 1-5
   - Device: Position sensor

Results are automatically compared against specifications and marked as PASS/NG.

---

## ❌ Troubleshooting

### Issue: "Employee validation required"
**Solution:** Enter Employee ID S041 first

### Issue: "Part Number Required"
**Solution:** Enter ALC Code sample2 before clicking START TESTING

### Issue: "PLC not connected"
**Solution:** Application continues in monitoring mode - test can still run

### Issue: Loadcell errors
**Solution:** Errors are automatically suppressed - application continues normally

---

## 📝 Notes

- **Loadcells:** Optional - system works without them
- **PLC Connection:** If PLC not available, system runs in monitoring mode
- **Database:** Must be running and accessible
- **COM Port:** Ensure no other application is using COM5

---

## ✅ Success Indicators

You'll know everything is working when:
1. ✅ Employee ID validates (green message)
2. ✅ Part loads (model name displayed)
3. ✅ START TESTING button becomes enabled
4. ✅ Process labels turn green during test
5. ✅ Test completes and saves to database

---

**For detailed test results, see:** `TEST_RESULTS.md`


