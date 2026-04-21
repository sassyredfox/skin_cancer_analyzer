@echo off
REM Windows batch script to run the project with Docker

echo.
echo ====================================
echo   Skin Cancer Detection Project
echo   Docker Setup Script (Windows)
echo ====================================
echo.

REM Check if Docker is installed
docker --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not installed or not in PATH
    echo Please install Docker Desktop from: https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)

echo [OK] Docker detected
echo.

REM Build and start containers
echo [*] Building and starting Docker containers...
docker-compose up -d

if errorlevel 1 (
    echo [ERROR] Failed to start Docker containers
    pause
    exit /b 1
)

echo.
echo ====================================
echo   Services Started Successfully!
echo ====================================
echo.
echo Frontend: http://localhost:3000
echo Backend:  http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo.
echo To view logs:
echo   docker-compose logs -f
echo.
echo To stop services:
echo   docker-compose down
echo.
pause
