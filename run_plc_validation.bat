@echo off
REM PLC Connection Stability Validation Test Runner
REM Tests the fixes for PLC power-off issue during Process Step 0

echo ========================================
echo PLC Connection Stability Validator
echo ========================================
echo.

REM Check if virtual environment exists
if exist "venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
) else (
    echo WARNING: Virtual environment not found
    echo Continuing with system Python...
)

echo.
echo Starting PLC validation tests...
echo Please ensure:
echo  1. PLC is powered ON
echo  2. PLC is connected to the configured COM port
echo  3. No other software is using the PLC connection
echo.
pause

REM Run validation script
python validate_plc_fix.py

echo.
echo ========================================
echo Validation Complete
echo ========================================
echo.
pause

