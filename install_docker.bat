@echo off
echo Installing Docker Python module for BeamMP Server Configurator...
echo.

REM Try different pip commands with --user flag to avoid permission issues
echo Attempting to install docker module...

REM Try python -m pip with --user first
python -m pip install --user docker==6.1.3
if %errorlevel% equ 0 (
    echo.
    echo Successfully installed Docker module!
    echo You can now use the server management features.
    pause
    exit /b 0
)

REM Try pip directly with --user
pip install --user docker==6.1.3
if %errorlevel% equ 0 (
    echo.
    echo Successfully installed Docker module!
    echo You can now use the server management features.
    pause
    exit /b 0
)

REM Try pip3 with --user
pip3 install --user docker==6.1.3
if %errorlevel% equ 0 (
    echo.
    echo Successfully installed Docker module!
    echo You can now use the server management features.
    pause
    exit /b 0
)

echo.
echo Failed to install Docker module automatically.
echo.
echo Please try one of the following manual methods:
echo.
echo 1. Open Command Prompt as Administrator and run:
echo    python -m pip install docker==6.1.3
echo.
echo 2. Or install for current user only:
echo    python -m pip install --user docker==6.1.3
echo.
echo 3. Or if you have pip installed separately:
echo    pip install --user docker==6.1.3
echo.
echo Note: The configurator will still work without Docker module,
echo but server management features will be disabled.
echo.
pause 