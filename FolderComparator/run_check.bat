@echo off
REM Batch file to run check_report.py with parameters
REM Usage: run_check.bat "C:\path\to\folder"

REM Change to script directory
cd /d "%~dp0"

REM Check if parameter was provided
if "%1"=="" (
    echo Error: Missing folder path parameter
    echo Usage: run_check.bat "C:\path\to\folder"
    pause
    exit /b 1
)

REM Run the Python script with -c parameter
python check_report.py -c %1