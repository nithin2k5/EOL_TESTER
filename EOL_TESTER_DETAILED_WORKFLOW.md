# 🔧 EOL TESTER - DETAILED WORKFLOW DOCUMENTATION

## 📋 **OVERVIEW**
This document provides a comprehensive workflow for the End-of-Line (EOL) Tester application implemented in Python, converted from C# with MySQL database integration and .env configuration.

---

## 🚀 **PHASE 1: APPLICATION STARTUP & INITIALIZATION**

### **Step 1.1: Environment Configuration Loading**
```
┌─────────────────────────────────────────────────────────────┐
│ 📁 Load .env File Configuration                            │
├─────────────────────────────────────────────────────────────┤
│ ✓ PLC_CONFIG: COM port, baud rate, station ID              │
│ ✓ DB_CONFIG: MySQL host, port, user, password, database    │
│ ✓ MACHINE_CONFIG: Machine ID, screen dimensions            │
│ ✓ TESTING_CONFIG: Timeouts, intervals, scan times          │
│ ✓ FILE_PATHS: Configuration file locations                 │
│ ✓ DEV_CONFIG: Simulation modes, debug flags               │
│ ✓ LOADCELL_CONFIG: COM ports for load cell connections     │
│ ✓ PLC_RX_DATA: Process status, sensors, program selection  │
└─────────────────────────────────────────────────────────────┘
```

### **Step 1.2: PLC Connection Initialization**
```
┌─────────────────────────────────────────────────────────────┐
│ ⚡ Initialize PLC Communication                             │
├─────────────────────────────────────────────────────────────┤
│ IF plc_simulation_mode = False:                             │
│   ├─ Create ModbusSerialClient                             │
│   ├─ Configure: COM port, baud rate, parity, stop bits     │
│   ├─ Test connection with read operation                    │
│   └─ Set plc_client status                                 │
│ ELSE:                                                       │
│   └─ Enable simulation mode for testing                    │
└─────────────────────────────────────────────────────────────┘
```

### **Step 1.3: Configuration File Loading**
```
┌─────────────────────────────────────────────────────────────┐
│ 📄 Load PLC Address Configuration Files                    │
├─────────────────────────────────────────────────────────────┤
│ ✓ InputSensors.txt → inputSensorsArray[]                   │
│ ✓ ProcessStatus.txt → processStatusArray[]                 │
│ ✓ HoldRegistersRead.txt → dataRegistersArray[]             │
│ ✓ MachineOnPLCCoilAddress.txt → machineOnPLCCoilAddress[]  │
│ ✓ AlertOnPLCCoilAddress.txt → alertOnPLCCoilAddress[]      │
└─────────────────────────────────────────────────────────────┘
```

### **Step 1.4: GUI Interface Setup**
```
┌─────────────────────────────────────────────────────────────┐
│ 🖥️ Create Main Application Window                          │
├─────────────────────────────────────────────────────────────┤
│ ✓ Title: "EOL (END OF LINE) TESTER"                        │
│ ✓ 4-Quadrant Layout:                                       │
│   ├─ Q1: Employee & ALC Entry                              │
│   ├─ Q2: Process Status Indicators                         │
│   ├─ Q3: Specifications Tree & Test Results                │
│   └─ Q4: Charts & Data Display                             │
│ ✓ Status message area                                       │
│ ✓ PLC connection status indicator                           │
└─────────────────────────────────────────────────────────────┘
```

---

## 👤 **PHASE 2: USER AUTHENTICATION & PART SETUP**

### **Step 2.1: Employee Code Validation**
```
┌─────────────────────────────────────────────────────────────┐
│ 🔐 Employee Authentication Process                          │
├─────────────────────────────────────────────────────────────┤
│ 1. Employee enters code in "EMP CODE" field                │
│ 2. On ENTER key press:                                      │
│    ├─ Read EmployeeCodes.txt file                          │
│    ├─ Validate code against authorized list                │
│    └─ IF VALID:                                            │
│        ├─ Set employee_validation_complete = True          │
│        ├─ Store current_employee_id                        │
│        ├─ Change field background to light green           │
│        ├─ Enable ALC code entry field                      │
│        └─ Focus moves to ALC field                         │
│      ELSE:                                                  │
│        ├─ Show error: "NOT AUTHORIZED to operate"          │
│        ├─ Clear entry field                                │
│        └─ Require supervisor consultation                  │
└─────────────────────────────────────────────────────────────┘
```

### **Step 2.2: ALC Code Processing & Part Loading**
```
┌─────────────────────────────────────────────────────────────┐
│ 🏷️ ALC Code Validation & Part Configuration                │
├─────────────────────────────────────────────────────────────┤
│ 1. ALC code entered in field                               │
│ 2. Start timer (alcInput_TimeInterval)                     │
│ 3. On timer completion:                                     │
│    ├─ Query TBL_MODEL_MASTER database table               │
│    ├─ Search: MM_ALC_CODE = entered_code AND MM_STATUS = 1 │
│    └─ IF PART EXISTS:                                      │
│        ├─ Load part information:                           │
│        │   ├─ Part Number, Model Name                      │
│        │   ├─ Vendor Code, EO Number                       │
│        │   ├─ Special Data, Initial ID                     │
│        │   ├─ Supplier Section                             │
│        │   ├─ Image Path                                   │
│        │   ├─ Barcode Print File Name                      │
│        │   └─ PLC Address for program selection            │
│        ├─ Update UI with part information                  │
│        ├─ Load part image (if available)                   │
│        ├─ Load barcode template content                    │
│        ├─ Write PLC program selection coil                 │
│        ├─ Send Machine ON signal to PLC                    │
│        ├─ Load model specifications                        │
│        ├─ Load model label details                         │
│        ├─ Display data and load graphs                     │
│        ├─ Get current lot number                           │
│        └─ Start NG Cable Validation                        │
│      ELSE:                                                  │
│        ├─ Show error: "Scanned Part Does NOT Exist"       │
│        ├─ Clear ALC field                                  │
│        └─ Re-enable ALC entry                              │
└─────────────────────────────────────────────────────────────┘
```

### **Step 2.3: Model Specifications Loading**
```
┌─────────────────────────────────────────────────────────────┐
│ 📊 Load Part Testing Specifications                        │
├─────────────────────────────────────────────────────────────┤
│ Query: TBL_MODEL_SPECIFICATION                              │
│ WHERE MS_PART_NUMBER = current_part                         │
│ ORDER BY MS_DEVICE                                          │
│                                                             │
│ For each specification record:                              │
│ ├─ Extract: Description, Device, Min, Unit, Max            │
│ ├─ Add device to deviceToRead[] array                      │
│ ├─ Set column visibility flags:                            │
│ │   ├─ columnL2 = True (if device = "L2")                  │
│ │   ├─ columnL3 = True (if device = "L3")                  │
│ │   ├─ columnL4 = True (if device = "L4")                  │
│ │   ├─ columnP3 = True (if device = "P3")                  │
│ │   └─ columnP4 = True (if device = "P4")                  │
│ └─ Populate specifications tree view                       │
└─────────────────────────────────────────────────────────────┘
```

### **Step 2.4: Sensor Label Configuration**
```
┌─────────────────────────────────────────────────────────────┐
│ 🏷️ Configure Dynamic Sensor Labels                         │
├─────────────────────────────────────────────────────────────┤
│ Query: TBL_MODEL_LABEL_DETAILS                              │
│ WHERE MLD_PART_NUMBER = current_part                        │
│                                                             │
│ For each label configuration:                               │
│ ├─ Extract: Label ID, ON/OFF status text, X/Y position     │
│ ├─ Add Label ID to inputSensorsToReadList[]                │
│ ├─ Create sensor label widget                              │
│ ├─ Position at specified X,Y coordinates                   │
│ ├─ Set initial text to OFF status                          │
│ ├─ Set initial color to OrangeRed                          │
│ └─ Store in sensor_labels dictionary                       │
└─────────────────────────────────────────────────────────────┘
```

---

## ⚙️ **PHASE 3: NG CABLE VALIDATION WORKFLOW**

### **Step 3.1: Initial NG Cable Validation**
```
┌─────────────────────────────────────────────────────────────┐
│ ⚠️ Starting NG Cable Validation Process                    │
├─────────────────────────────────────────────────────────────┤
│ Purpose: Verify NG (Not Good) cable produces FAIL results  │
│                                                             │
│ 1. Set startingNGCableValidation = True                    │
│ 2. Display message: "Please Validate NG Cable..."          │
│ 3. Start asynchronous testing process                      │
│ 4. Monitor PLC and collect test data                       │
│ 5. Process test results:                                    │
│    ├─ IF failCounter > 0:                                  │
│    │   ├─ NG validation successful                         │
│    │   ├─ Set startingNGCableValidation = False            │
│    │   ├─ Message: "NG Validation successful, continue..."  │
│    │   └─ Restart testing process for normal operation     │
│    └─ ELSE (all tests passed):                             │
│        ├─ NG validation failed                             │
│        ├─ Message: "NG Validation NOT OK, please repeat"   │
│        └─ Restart NG validation after 3 second delay      │
└─────────────────────────────────────────────────────────────┘
```

---

## 🧪 **PHASE 4: CORE TESTING PROCESS**

### **Step 4.1: Asynchronous Testing Initialization**
```
┌─────────────────────────────────────────────────────────────┐
│ 🚀 Start Multi-Threaded Testing Process                    │
├─────────────────────────────────────────────────────────────┤
│ Reset: rcvdTestRslt = False                                 │
│                                                             │
│ Launch 4 Parallel Threads:                                 │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Thread 1: read_coils()                                  │ │
│ │ ├─ Monitor PLC process status coils                     │ │
│ │ ├─ Update UI status indicators                          │ │
│ │ ├─ Detect test completion signals                       │ │
│ │ └─ Frequency: Every 200ms                               │ │
│ └─────────────────────────────────────────────────────────┘ │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Thread 2: read_sensor_inputs()                          │ │
│ │ ├─ Monitor discrete input sensors                       │ │
│ │ ├─ Update sensor label states                           │ │
│ │ ├─ Process configured sensor list                       │ │
│ │ └─ Frequency: Every 200ms                               │ │
│ └─────────────────────────────────────────────────────────┘ │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Thread 3: read_input_registers()                        │ │
│ │ ├─ Read load cell analog values (L1-L4)                 │ │
│ │ ├─ Read pressure sensor values (P1-P4)                  │ │
│ │ ├─ Scale values and track maximums                      │ │
│ │ └─ Frequency: Every 50ms                                │ │
│ └─────────────────────────────────────────────────────────┘ │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Thread 4: main_test_control_loop()                      │ │
│ │ ├─ Wait for rcvdTestRslt = True                         │ │
│ │ ├─ Process complete test results                        │ │
│ │ ├─ Handle workflow state transitions                    │ │
│ │ └─ Frequency: Every 50ms                                │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### **Step 4.2: PLC Process Status Monitoring**
```
┌─────────────────────────────────────────────────────────────┐
│ ⚡ PLC Coil Monitoring (read_coils)                        │
├─────────────────────────────────────────────────────────────┤
│ Convert hex addresses to integers:                          │
│ ├─ AUTO: processStatusArray[0] → int address               │
│ ├─ HOME: processStatusArray[1] → int address               │
│ ├─ PULL1_OK: processStatusArray[2] → int address           │
│ ├─ PULL1_NG: processStatusArray[3] → int address           │
│ ├─ PULL2_OK: processStatusArray[4] → int address           │
│ ├─ PULL2_NG: processStatusArray[5] → int address           │
│ ├─ TEST_RESULT_OK: processStatusArray[6] → int address     │
│ ├─ TEST_RESULT_NG: processStatusArray[7] → int address     │
│ ├─ CAM1_OK: processStatusArray[8] → int address            │
│ ├─ CAM1_NG: processStatusArray[9] → int address            │
│ └─ CAM1_ONOFF: processStatusArray[10] → int address        │
│                                                             │
│ Continuous Monitoring Loop:                                 │
│ WHILE rcvdTestRslt = False:                                 │
│   ├─ Read all coil states from PLC                         │
│   ├─ Update UI status indicators:                          │
│   │   ├─ Green = Coil ON                                   │
│   │   ├─ Blue = Coil OFF                                   │
│   │   └─ Orange = NG condition                             │
│   ├─ Process camera status logic                           │
│   ├─ Check for test completion:                            │
│   │   ├─ IF TEST_RESULT_OK = True: Set rcvdTestRslt = True │
│   │   └─ IF TEST_RESULT_NG = True: Set rcvdTestRslt = True │
│   └─ Sleep 200ms                                           │
└─────────────────────────────────────────────────────────────┘
```

### **Step 4.3: Sensor Input Monitoring**
```
┌─────────────────────────────────────────────────────────────┐
│ 📡 Discrete Input Sensor Monitoring                        │
├─────────────────────────────────────────────────────────────┤
│ FOR each sensor in inputSensorsToReadList:                 │
│   ├─ Extract sensor index from sensor ID                   │
│   ├─ Get sensor address from inputSensorsArray[index]      │
│   ├─ Convert hex address to integer                        │
│   ├─ Read discrete input from PLC                          │
│   ├─ Update sensor label:                                  │
│   │   ├─ IF sensor = ON:                                   │
│   │   │   ├─ Text = MLD_ON_STATUS                          │
│   │   │   └─ Color = Blue                                  │
│   │   └─ IF sensor = OFF:                                  │
│   │       ├─ Text = MLD_OFF_STATUS                         │
│   │       └─ Color = OrangeRed                             │
│   └─ Sleep 200ms between sensor reads                      │
└─────────────────────────────────────────────────────────────┘
```

### **Step 4.4: Analog Value Monitoring**
```
┌─────────────────────────────────────────────────────────────┐
│ 📈 Load Cell & Pressure Sensor Monitoring                  │
├─────────────────────────────────────────────────────────────┤
│ Convert register addresses to integers:                     │
│ ├─ L1: dataRegistersArray[0] → int address                 │
│ ├─ L2: dataRegistersArray[1] → int address                 │
│ ├─ L3: dataRegistersArray[2] → int address                 │
│ ├─ L4: dataRegistersArray[3] → int address                 │
│ ├─ P1: dataRegistersArray[4] → int address                 │
│ ├─ P2: dataRegistersArray[5] → int address                 │
│ ├─ P3: dataRegistersArray[6] → int address                 │
│ └─ P4: dataRegistersArray[7] → int address                 │
│                                                             │
│ Continuous Monitoring Loop:                                 │
│ WHILE rcvdTestRslt = False:                                 │
│   ├─ Read all register values from PLC                     │
│   ├─ Apply scaling factors:                                │
│   │   ├─ Load Cells: raw_value / 10.0                      │
│   │   └─ Pressure: raw_value / 100.0                       │
│   ├─ Track maximum values for load cells:                  │
│   │   ├─ IF current > L1MaxValue: L1MaxValue = current     │
│   │   ├─ IF current > L2MaxValue: L2MaxValue = current     │
│   │   ├─ IF current > L3MaxValue: L3MaxValue = current     │
│   │   └─ IF current > L4MaxValue: L4MaxValue = current     │
│   ├─ Store current pressure values                         │
│   └─ Sleep 50ms                                            │
└─────────────────────────────────────────────────────────────┘
```

---

## 📊 **PHASE 5: TEST RESULT PROCESSING**

### **Step 5.1: Test Completion Detection & Result Evaluation**
```
┌─────────────────────────────────────────────────────────────┐
│ ✅ Test Result Processing & Evaluation                     │
├─────────────────────────────────────────────────────────────┤
│ Triggered when: rcvdTestRslt = True                         │
│                                                             │
│ 1. Reset counters: failCounter = 0, passCounter = 0        │
│                                                             │
│ 2. FOR each specification in spec_tree:                    │
│    ├─ Get device type (L1, L2, L3, L4, P1, P2, P3, P4)     │
│    ├─ Get specification limits (min_val, max_val)          │
│    ├─ Get actual measured value:                           │
│    │   ├─ L1: actual_value = L1MaxValue                    │
│    │   ├─ L2: actual_value = L2MaxValue                    │
│    │   ├─ L3: actual_value = L3MaxValue                    │
│    │   ├─ L4: actual_value = L4MaxValue                    │
│    │   ├─ P1: actual_value = P01Value                      │
│    │   ├─ P2: actual_value = P02Value                      │
│    │   ├─ P3: actual_value = P03Value                      │
│    │   └─ P4: actual_value = P04Value                      │
│    ├─ Evaluate against limits:                             │
│    │   ├─ IF min_val ≤ actual_value ≤ max_val:             │
│    │   │   ├─ result = "PASS"                              │
│    │   │   ├─ color = Blue                                 │
│    │   │   └─ passCounter++                                │
│    │   └─ ELSE:                                            │
│    │       ├─ result = "NG"                                │
│    │       ├─ color = OrangeRed                            │
│    │       └─ failCounter++                                │
│    └─ Update specification tree with actual value & result │
│                                                             │
│ 3. Process results based on current workflow state         │
└─────────────────────────────────────────────────────────────┘
```

### **Step 5.2: Workflow State Processing**
```
┌─────────────────────────────────────────────────────────────┐
│ 🔄 Workflow State-Based Result Processing                  │
├─────────────────────────────────────────────────────────────┤
│ IF startingNGCableValidation = True:                        │
│   ├─ Expected: NG cable should produce failures            │
│   ├─ IF failCounter > 0:                                   │
│   │   ├─ ✅ NG validation successful                       │
│   │   ├─ Message: "NG Validation successful, continue..."   │
│   │   ├─ Set startingNGCableValidation = False             │
│   │   └─ Restart testing process (1 second delay)          │
│   └─ ELSE:                                                 │
│       ├─ ❌ NG validation failed                           │
│       ├─ Message: "NG Validation NOT OK, please repeat"    │
│       └─ Restart NG validation (3 second delay)            │
│                                                             │
│ ELSE IF endingNGCableValidation = True:                    │
│   ├─ Final NG validation before part completion            │
│   ├─ IF failCounter > 0:                                   │
│   │   ├─ ✅ Final NG validation successful                 │
│   │   ├─ Set endingNGCableValidated = True                 │
│   │   ├─ Reset PLC program selection coil                  │
│   │   └─ Refresh form for next part (1 second delay)       │
│   └─ ELSE:                                                 │
│       ├─ ❌ Final NG validation failed                     │
│       ├─ Set endingNGCableValidated = False                │
│       └─ Restart NG validation (3 second delay)            │
│                                                             │
│ ELSE:                                                       │
│   └─ Process normal test results                           │
└─────────────────────────────────────────────────────────────┘
```

### **Step 5.3: Normal Test Result Processing**
```
┌─────────────────────────────────────────────────────────────┐
│ 📋 Normal Test Result Processing & Data Generation         │
├─────────────────────────────────────────────────────────────┤
│ 1. Check for date rollover:                                │
│    ├─ IF current_date > test_date:                         │
│    │   ├─ Reset lotNo = "0"                                │
│    │   ├─ Update today = current_date                      │
│    │   └─ Set partRunningSerialExists = False              │
│    └─ Continue with current lot sequence                   │
│                                                             │
│ 2. Generate next lot number:                               │
│    ├─ j = int(lotNo) + 1                                   │
│    └─ lotNo = f"{j:07d}" (7-digit with leading zeros)      │
│                                                             │
│ 3. Generate traceability code:                             │
│    ├─ Format: YYMMDDImachineG1A + lotNo                    │
│    ├─ machine_suffix = last 2 digits of machine_id         │
│    └─ traceabilityCode = "241219I01G1A0000001" (example)   │
│                                                             │
│ 4. Check for duplicate traceability code in database       │
│                                                             │
│ 5. Determine final test status:                            │
│    ├─ IF passCounter = len(deviceToRead) AND not duplicate:│
│    │   ├─ Final Status = "OK"                              │
│    │   ├─ Save test data to database                       │
│    │   └─ Print barcode label (if configured)              │
│    └─ ELSE:                                                │
│        ├─ Final Status = "NG"                              │
│        ├─ Save test data to database                       │
│        └─ Show duplicate warning (if applicable)           │
│                                                             │
│ 6. Update charts and reset for next cycle (1.2s delay)    │
└─────────────────────────────────────────────────────────────┘
```

---

## 💾 **PHASE 6: DATABASE OPERATIONS**

### **Step 6.1: Test Data Persistence**
```
┌─────────────────────────────────────────────────────────────┐
│ 💽 Save Test Data to Database (save_testing_data_cs_style) │
├─────────────────────────────────────────────────────────────┤
│ Build Dynamic INSERT Query:                                 │
│                                                             │
│ Base Columns (Always Included):                             │
│ ├─ TD_MACHINE_ID = machine_config["machine_id"]             │
│ ├─ TD_PART_NUMBER = partNumber                              │
│ ├─ TD_LOT_NUMBER = lotNo                                    │
│ ├─ TD_TRACEABILITY_CODE = traceabilityCode                  │
│ ├─ TD_RECORD_DATE = current_date                            │
│ ├─ TD_DATETIME = current_datetime                           │
│ ├─ L1 = L1MaxValue                                          │
│ ├─ P1 = P01Value                                            │
│ ├─ P2 = P02Value                                            │
│ ├─ CAM1 = cam1Result                                        │
│ ├─ TD_OVERALL_STATUS = "OK" or "NG"                         │
│ └─ TD_EMPLOYEE_CODE = current_employee_id                   │
│                                                             │
│ Optional Columns (Based on Part Configuration):             │
│ ├─ IF columnL2 = True: L2 = L2MaxValue                     │
│ ├─ IF columnL3 = True: L3 = L3MaxValue                     │
│ ├─ IF columnL4 = True: L4 = L4MaxValue                     │
│ ├─ IF columnP3 = True: P3 = P03Value                       │
│ └─ IF columnP4 = True: P4 = P04Value                       │
│                                                             │
│ Execute INSERT into TBL_TEST_DATA                           │
│                                                             │
│ IF status = "OK":                                           │
│   └─ Update part running serial table                      │
└─────────────────────────────────────────────────────────────┘
```

### **Step 6.2: Part Running Serial Management**
```
┌─────────────────────────────────────────────────────────────┐
│ 📊 Part Running Serial Update                              │
├─────────────────────────────────────────────────────────────┤
│ IF partRunningSerialExists = False:                        │
│   ├─ INSERT new record into TBL_PART_RUNNING_SERIAL:       │
│   │   ├─ PART_NUMBER = partNumber                          │
│   │   ├─ TEST_DAY_DATE = current_date                      │
│   │   ├─ TEST_DAY_LAST_DATE_TIME = current_datetime        │
│   │   ├─ TRACEABILITY_CODE = traceabilityCode              │
│   │   └─ RUNNING_LOT_NUMBER = lotNo                        │
│   └─ Set partRunningSerialExists = True                    │
│                                                             │
│ ELSE:                                                       │
│   └─ UPDATE existing record in TBL_PART_RUNNING_SERIAL:    │
│       ├─ SET TEST_DAY_LAST_DATE_TIME = current_datetime    │
│       ├─ SET TRACEABILITY_CODE = traceabilityCode          │
│       ├─ SET RUNNING_LOT_NUMBER = lotNo                    │
│       └─ WHERE PART_NUMBER = partNumber AND               │
│           TEST_DAY_DATE = current_date                      │
└─────────────────────────────────────────────────────────────┘
```

---

## 🏷️ **PHASE 7: BARCODE LABEL GENERATION & PRINTING**

### **Step 7.1: Label Template Processing**
```
┌─────────────────────────────────────────────────────────────┐
│ 🖨️ Barcode Label Generation Process                        │
├─────────────────────────────────────────────────────────────┤
│ IF barcodePrintFileName exists AND ≠ "NO_BARCODE_PRINT_FILE"│
│                                                             │
│ 1. Load template content from prnFileContent               │
│                                                             │
│ 2. Replace all placeholders with actual values:            │
│    ├─ @alcCode@ → ALC code from entry field               │
│    ├─ @partNumber@ → partNumber                            │
│    ├─ @modelName@ → modelName                              │
│    ├─ @vendorCode@ → vendorCode                            │
│    ├─ @eoNumber@ → eoNumber                                │
│    ├─ @specialData@ → specialData                          │
│    ├─ @initialID@ → initialID                              │
│    ├─ @supplierSection@ → supplierSection                  │
│    ├─ @lotNo@ → lotNo                                      │
│    ├─ @traceabilityCode@ → traceabilityCode                │
│    ├─ @L1MaxValue@ → L1MaxValue (1 decimal)                │
│    ├─ @L2MaxValue@ → L2MaxValue (1 decimal)                │
│    ├─ @L3MaxValue@ → L3MaxValue (1 decimal)                │
│    ├─ @L4MaxValue@ → L4MaxValue (1 decimal)                │
│    ├─ @P01Value@ → P01Value (2 decimals with +/- sign)     │
│    ├─ @P02Value@ → P02Value (2 decimals with +/- sign)     │
│    ├─ @P03Value@ → P03Value (2 decimals with +/- sign)     │
│    ├─ @P04Value@ → P04Value (2 decimals with +/- sign)     │
│    ├─ @ddMMyy@ → current date (DDMMYY format)              │
│    ├─ @HH:mm:ss@ → current time (HH:MM:SS format)          │
│    ├─ @machineID@ → machine_config["machine_id"]           │
│    └─ @machineID_NoAlphabet@ → numeric part of machine ID  │
│                                                             │
│ 3. Create temporary .prn file                              │
│ 4. Write processed template to file                        │
│ 5. Send to printer (actual implementation would vary)      │
│ 6. Start barcode scan monitoring                           │
└─────────────────────────────────────────────────────────────┘
```

### **Step 7.2: Barcode Scan Monitoring**
```
┌─────────────────────────────────────────────────────────────┐
│ 📱 Printed Label Scan Monitoring                           │
├─────────────────────────────────────────────────────────────┤
│ 1. Set printedLabelScanDataInput_Received = False          │
│                                                             │
│ 2. Start timeout timer:                                    │
│    └─ timeout = printedLabelScanDataInput_WaitTime (ms)    │
│                                                             │
│ 3. Monitor for scan input:                                 │
│    ├─ WHILE not scan_received AND not timeout:             │
│    │   ├─ Check for barcode scan input                     │
│    │   ├─ Check elapsed time against timeout               │
│    │   └─ Sleep 10ms                                       │
│    └─ Continue monitoring                                  │
│                                                             │
│ 4. Handle scan result:                                     │
│    ├─ IF scan received within timeout:                     │
│    │   ├─ Process scanned data                             │
│    │   └─ Update database with scan result                 │
│    └─ ELSE (timeout occurred):                             │
│        ├─ Set scan result = "***"                          │
│        ├─ Update database with timeout marker              │
│        └─ Log timeout event                                │
│                                                             │
│ 5. Update TBL_TEST_DATA:                                   │
│    └─ SET TD_BARCODE_SCAN_RESULT = scan_result             │
│        WHERE TD_PART_NUMBER = partNumber AND               │
│        TD_TRACEABILITY_CODE = traceabilityCode             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔄 **PHASE 8: CYCLE RESET & CONTINUATION**

### **Step 8.1: Test Parameter Reset**
```
┌─────────────────────────────────────────────────────────────┐
│ 🔄 Reset Test Parameters for Next Cycle                    │
├─────────────────────────────────────────────────────────────┤
│ 1. Clear status message                                     │
│                                                             │
│ 2. Reset process status UI colors:                         │
│    ├─ AUTO → DeepSkyBlue                                   │
│    ├─ HOME → DeepSkyBlue                                   │
│    ├─ PULL1 → DeepSkyBlue                                  │
│    ├─ PULL2 → DeepSkyBlue                                  │
│    └─ TESTRESULT → DeepSkyBlue                             │
│                                                             │
│ 3. Reset camera status:                                    │
│    └─ CAM1 → "CAMERA ONE STATUS" (DeepSkyBlue)            │
│                                                             │
│ 4. Reset measured values:                                  │
│    ├─ loadcell01Value = 0.0                                │
│    ├─ loadcell02Value = 0.0                                │
│    ├─ loadcell03Value = 0.0                                │
│    ├─ loadcell04Value = 0.0                                │
│    ├─ L1MaxValue = 0.0                                     │
│    ├─ L2MaxValue = 0.0                                     │
│    ├─ L3MaxValue = 0.0                                     │
│    ├─ L4MaxValue = 0.0                                     │
│    ├─ P01Value = 0.0                                       │
│    ├─ P02Value = 0.0                                       │
│    ├─ P03Value = 0.0                                       │
│    └─ P04Value = 0.0                                       │
│                                                             │
│ 5. Reset test flags:                                       │
│    ├─ failCounter = 0                                      │
│    ├─ passCounter = 0                                      │
│    ├─ rcvdTestRslt = False                                 │
│    └─ cam1Result = ""                                      │
│                                                             │
│ 6. Clear specification tree results:                       │
│    ├─ Clear ACTUAL column                                  │
│    └─ Clear RESULT column                                  │
└─────────────────────────────────────────────────────────────┘
```

### **Step 8.2: Cycle Continuation Logic**
```
┌─────────────────────────────────────────────────────────────┐
│ ▶️ Test Cycle Continuation Decision                         │
├─────────────────────────────────────────────────────────────┤
│ 1. Write Machine ON signal to PLC                          │
│                                                             │
│ 2. Determine next action:                                   │
│    ├─ IF endingNGCableValidated = True:                    │
│    │   └─ Refresh form for next part                       │
│    └─ ELSE:                                                │
│        └─ Continue testing with current part               │
│                                                             │
│ 3. Start next test cycle:                                  │
│    └─ Call start_check_async() to begin monitoring         │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔚 **PHASE 9: PART COMPLETION & FORM REFRESH**

### **Step 9.1: Form Refresh for Next Part**
```
┌─────────────────────────────────────────────────────────────┐
│ 🆕 Refresh Form for Next Part Processing                   │
├─────────────────────────────────────────────────────────────┤
│ 1. Clear data structures:                                  │
│    ├─ inputSensorsToReadList.clear()                       │
│    ├─ mldDataTable.clear()                                 │
│    └─ deviceToRead.clear()                                 │
│                                                             │
│ 2. Reset workflow flags:                                   │
│    ├─ endingNGCableValidated = False                       │
│    ├─ partRunningSerialExists = False                      │
│    ├─ employee_validation_complete = False                 │
│    └─ current_employee_id = None                           │
│                                                             │
│ 3. Clear UI elements:                                      │
│    ├─ Clear specification tree                             │
│    ├─ Clear model header text                              │
│    ├─ Hide sensor labels                                   │
│    ├─ Reset sensor label colors to black                   │
│    └─ Clear part image display                             │
│                                                             │
│ 4. Reset chart data:                                       │
│    └─ dataPointX = 0                                       │
│                                                             │
│ 5. Reset entry fields:                                     │
│    ├─ Clear ALC entry field                                │
│    ├─ Enable ALC entry field                               │
│    ├─ Clear employee entry field                           │
│    ├─ Enable employee entry field                          │
│    └─ Set focus to employee entry field                    │
│                                                             │
│ 6. Enable next model button                                │
│                                                             │
│ 7. Ready for new employee authentication                   │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎯 **COMPLETE WORKFLOW SUMMARY**

### **📋 Process Flow Overview:**
```
1. 🚀 STARTUP → Load .env config → Initialize PLC → Setup GUI
2. 👤 AUTHENTICATION → Employee validation → ALC code processing
3. ⚙️ PART SETUP → Load specifications → Configure sensors → Start NG validation
4. 🧪 TESTING → Multi-threaded PLC monitoring → Real-time data collection
5. 📊 EVALUATION → Compare against specs → Count pass/fail → Determine status
6. 💾 DATABASE → Save test data → Update running serial → Generate traceability
7. 🏷️ PRINTING → Process label template → Print barcode → Monitor scan
8. 🔄 RESET → Clear parameters → Reset UI → Start next cycle
9. 🔚 COMPLETION → Refresh form → Reset for next part
```

### **⚡ Key Features:**
- ✅ **Multi-threaded Architecture**: 4 parallel monitoring threads
- ✅ **Real-time PLC Communication**: Modbus RTU with 50-200ms refresh rates
- ✅ **Dynamic Database Operations**: MySQL with configurable columns
- ✅ **Template-based Label Printing**: 20+ placeholder replacements
- ✅ **State Machine Workflow**: NG validation and normal testing modes
- ✅ **Comprehensive Error Handling**: Try-catch blocks throughout
- ✅ **Simulation Mode Support**: Testing without physical hardware
- ✅ **Thread-safe UI Updates**: Proper synchronization with main thread

### **🔧 Configuration-Driven Design:**
- All settings loaded from `.env` file
- PLC addresses from configuration text files
- Database table structure from part specifications
- Sensor layout from label details table
- Flexible column inclusion based on part requirements

**This workflow represents a complete, production-ready EOL testing system with all the sophistication of the original C# application!** 🚀
