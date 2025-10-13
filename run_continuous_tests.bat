@echo off
echo ========================================
echo    EOL Continuous Test Runner
echo ========================================
echo.

if "%1"=="simple" goto :simple
if "%1"=="advanced" goto :advanced
if "%1"=="auto" goto :auto
if "%1"=="help" goto :help

echo Usage: run_continuous_tests.bat [option]
echo.
echo Options:
echo   (no option)  - Run simple interactive menu
echo   simple       - Run simple continuous testing
echo   advanced     - Run advanced continuous testing with monitoring
echo   auto         - Run fully automated testing (bypasses manual validations)
echo   help         - Show this help message
echo.
echo Examples:
echo   run_continuous_tests.bat
echo   run_continuous_tests.bat simple
echo   run_continuous_tests.bat advanced
echo   run_continuous_tests.bat auto
echo.
goto :eof

:simple
echo Starting Simple Continuous Testing...
python simple_continuous_test.py
goto :eof

:advanced
echo Starting Advanced Continuous Testing...
python continuous_test_runner.py
goto :eof

:auto
echo Starting Fully Automated Testing...
python automated_test_runner.py
goto :eof

:help
echo ========================================
echo    EOL Continuous Test Runner - Help
echo ========================================
echo.
echo This batch file provides easy access to different
echo continuous testing modes for the EOL Tester.
echo.
echo MODES:
echo ------
echo Simple Mode (simple_continuous_test.py):
echo   - Interactive menu to choose test options
echo   - Run continuous testing or specific number of cycles
echo   - Simple and straightforward
echo.
echo Advanced Mode (continuous_test_runner.py):
echo   - Automated continuous testing with detailed monitoring
echo   - Real-time statistics and status updates
echo   - Comprehensive logging and error handling
echo   - Runs until manually stopped (Ctrl+C)
echo.
echo Automated Mode (automated_test_runner.py):
echo   - Fully automated testing that bypasses manual validations
echo   - Auto-loads first available model and part number
echo   - Auto-validates employee ID for testing
echo   - No manual intervention required
echo   - Perfect for continuous integration or automated testing
echo.
echo USAGE:
echo ------
echo 1. Double-click this batch file for interactive menu
echo 2. Use command line with options as shown above
echo 3. Press Ctrl+C in console to stop continuous testing
echo.
echo FILES CREATED:
echo -------------
echo - simple_continuous_test.py    (Simple runner)
echo - continuous_test_runner.py    (Advanced runner)
echo - automated_test_runner.py     (Fully automated runner)
echo - run_continuous_tests.bat     (This batch file)
echo.
pause
goto :eof
