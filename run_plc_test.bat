@echo off
echo ========================================
echo Real PLC Integration Test
echo ========================================
echo.
echo This script will test the real PLC integration
echo Make sure your PLC is connected to COM5
echo.
pause
echo.
echo Running PLC connection test...
python test_real_plc_integration.py
echo.
echo ========================================
echo Test completed!
echo ========================================
pause



