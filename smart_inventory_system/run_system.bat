@echo off
title SmartLogix - Inventory and Transportation Management System
echo =========================================================================
echo   Starting SmartLogix Inventory and Logistics Management System...
echo =========================================================================
cd /d "%~dp0"

echo Opening browser at http://127.0.0.1:5000 ...
start http://127.0.0.1:5000

echo Launching Flask server on http://127.0.0.1:5000 ...
python app.py
if errorlevel 1 (
    echo Python default alias not found, trying local Python path...
    "%LOCALAPPDATA%\Python\bin\python.exe" app.py
)
pause
