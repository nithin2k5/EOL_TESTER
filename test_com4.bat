@echo off
echo ===================================
echo Testing PLC Connection on COM4
echo ===================================
echo Configuration:
echo   COM Port: COM4
echo   Baudrate: 38400
echo   Station ID: 1
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

echo Starting COM4 PLC connection test...
echo.
python test_com4_plc.py

echo.
echo Test completed. Press any key to exit...
pause >nul


