@echo off
set IMAGE_NAME=entropyx-ai
set IMAGE_TAG=latest
set OUTPUT_FILE=entropyx-ai-latest.tar

echo ========================================================
echo  Docker Image Build & Save Script for entropyx-ai
echo ========================================================

:: Check if Docker is installed
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker is not installed or not in PATH.
    echo Please install Docker Desktop and try again.
    pause
    exit /b 1
)

echo [1/3] Building Docker image %IMAGE_NAME%:%IMAGE_TAG%...
docker build -t %IMAGE_NAME%:%IMAGE_TAG% .
if %errorlevel% neq 0 (
    echo [ERROR] Docker build failed.
    pause
    exit /b 1
)

echo [2/3] Saving image to %OUTPUT_FILE%...
docker save -o %OUTPUT_FILE% %IMAGE_NAME%:%IMAGE_TAG%
if %errorlevel% neq 0 (
    echo [ERROR] Docker save failed.
    pause
    exit /b 1
)

echo [3/3] Done!
echo.
echo Success! The image has been saved to: %OUTPUT_FILE%
echo You can copy this file to your internal server and load it using:
echo    docker load -i %OUTPUT_FILE%
echo.
pause