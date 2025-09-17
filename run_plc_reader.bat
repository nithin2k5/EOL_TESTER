@echo off
echo ===================================
echo PLC Coil Reader - COM4 Connection
echo ===================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python and add it to your PATH
    pause
    exit /b 1
)

REM Check if required packages are installed
python -c "import pymodbus, serial" >nul 2>&1
if errorlevel 1 (
    echo Installing required packages...
    pip install pymodbus pyserial
    if errorlevel 1 (
        echo ERROR: Failed to install required packages
        pause
        exit /b 1
    )
)

echo Starting PLC Coil Reader...
echo.
python plc_coil_reader.py

echo.
echo PLC Reader session ended.
pause


