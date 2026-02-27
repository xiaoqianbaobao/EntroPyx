@echo off
echo ========================================================
echo  Docker Desktop Installer for Windows (Retry)
echo ========================================================

:: Check for Admin Privileges
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] This script must be run as Administrator!
    echo Please right-click on this file and select "Run as administrator".
    pause
    exit /b 1
)

echo [1/3] Installing Docker Desktop via Winget (Source: winget)...
:: Added --source winget to avoid msstore connection issues
winget install Docker.DockerDesktop --source winget --accept-package-agreements --accept-source-agreements
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Installation failed again. Network issues detected.
    echo.
    echo ========================================================
    echo  MANUAL INSTALLATION REQUIRED
    echo ========================================================
    echo Please open your browser and download the installer directly from:
    echo https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe
    echo.
    echo After downloading, run the installer and follow the prompts.
    echo.
    pause
    exit /b 1
)

echo [2/3] Installation completed.
echo.
echo [IMPORTANT] Docker Desktop requires a system restart.
set /p RESTART="Do you want to restart now? (Y/N): "
if /i "%RESTART%"=="Y" (
    shutdown /r /t 5
)

pause