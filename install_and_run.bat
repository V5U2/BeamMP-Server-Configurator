@echo off
echo BeamMP Server Configurator - Installation and Setup
echo ===================================================

echo.
echo Checking Python installation...
python --version
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.7+ from https://python.org
    pause
    exit /b 1
)

echo.
echo Installing required packages...
echo If you get permission errors, try running this as Administrator
python -m pip install Flask toml

if %errorlevel% neq 0 (
    echo.
    echo Trying alternative installation method...
    pip install Flask toml
)

if %errorlevel% neq 0 (
    echo.
    echo ERROR: Failed to install required packages
    echo Please try running this script as Administrator
    pause
    exit /b 1
)

echo.
echo Installation completed successfully!
echo.
echo Starting BeamMP Server Configurator...
echo The web interface will be available at: http://localhost:5000
echo Press Ctrl+C to stop the server
echo.

python app.py

pause 