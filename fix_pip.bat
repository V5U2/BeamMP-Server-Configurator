@echo off
echo Fixing pip installation for Python 3.9...
echo.

REM Check if running as administrator
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo This script needs to be run as Administrator.
    echo Right-click on this file and select "Run as administrator"
    echo.
    pause
    exit /b 1
)

echo Running as Administrator - proceeding with pip fix...
echo.

REM Try to fix pip using get-pip.py
echo Downloading get-pip.py...
curl -o get-pip.py https://bootstrap.pypa.io/get-pip.py
if %errorlevel% neq 0 (
    echo Failed to download get-pip.py
    echo Trying alternative method...
    goto :alternative_method
)

echo Installing pip using get-pip.py...
python get-pip.py --force-reinstall
if %errorlevel% equ 0 (
    echo Successfully reinstalled pip!
    goto :cleanup
)

:alternative_method
echo Trying alternative pip installation method...
echo.

REM Try using ensurepip with user installation
python -m ensurepip --user --upgrade
if %errorlevel% equ 0 (
    echo Successfully installed pip for user!
    goto :cleanup
)

REM Try installing pip using easy_install
echo Trying easy_install method...
python -m easy_install --upgrade pip
if %errorlevel% equ 0 (
    echo Successfully installed pip using easy_install!
    goto :cleanup
)

echo.
echo All automatic methods failed. Please try manual installation:
echo.
echo 1. Download get-pip.py manually from: https://bootstrap.pypa.io/get-pip.py
echo 2. Run: python get-pip.py --user
echo.
echo Or install Python from python.org which includes pip by default.
echo.
goto :cleanup

:cleanup
REM Clean up downloaded file
if exist get-pip.py del get-pip.py

echo.
echo Testing pip installation...
python -m pip --version
if %errorlevel% equ 0 (
    echo.
    echo Pip is now working! You can install the Docker module with:
    echo python -m pip install docker==6.1.3
) else (
    echo.
    echo Pip installation may still have issues.
    echo Try running: python -m pip install --user docker==6.1.3
)

echo.
pause 