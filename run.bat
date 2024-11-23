@echo off
if not exist "main.py" (
    echo Error: main.py not found in the current directory
    pause
    exit /b 1
)

if not exist "src" (
    echo Error: src directory not found
    pause
    exit /b 1
)

where python >nul 2>nul
if %errorlevel% neq 0 (
    echo Python is not installed or not in PATH
    pause
    exit /b 1
)

python main.py
if %errorlevel% neq 0 (
    echo An error occurred while running the script
    pause
    exit /b 1
)
pause
