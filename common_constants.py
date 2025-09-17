"""
Common constants and configuration for EOL Tester application
"""

class Constants:
    """Database connection strings and other constants"""

    # Database connection string for MySQL
    dbConnectionString = "Server=localhost;Database=EOL;Uid=root;Pwd=12345;"

    # Printer name for barcode printing
    printerName = "Your_Printer_Name"  # Replace with actual printer name

    # File paths for configuration files
    inputSensorsFile = "txt_files/InputSensors.txt"
    processStatusFile = "txt_files/ProcessStatus.txt"
    employeeCodesFile = "txt_files/EmployeeCodes.txt"
    plcOnRegisterFile = "txt_files/PLC_on_register.txt"
    alertOnRegisterFile = "txt_files/AlertOnPLCCoilAddress.txt"  # New file for alert coil
    machineOnRegisterFile = "txt_files/MachineOnPLCCoilAddress.txt"  # New file for machine on coil

    # Timing constants (in milliseconds)
    alcInput_TimeInterval = 3000  # 3 seconds for ALC code input
    printedLabelScanDataInput_TimeInterval = 4000  # 4 seconds for barcode scanner data
    printedLabelScanDataInput_WaitTime = 6000  # 6 seconds wait for receiving printed label scan data
    alertOn_TimeInterval = 5000  # 5 seconds wait until the alert stops

    # Process status labels
    processStatusLabels = ["AUTO", "HOME", "PULL1_OK", "PULL1_NG", "PULL2_OK", "PULL2_NG", "TESTRESULT_OK", "TESTRESULT_NG", "CAM1_OK", "CAM1_NG", "CAM1_ONOFF"]


