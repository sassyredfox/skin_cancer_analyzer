@echo off
setlocal
set "ROOT=%~dp0"

echo ========================================
echo Skin Cancer Project - Presentation Mode
echo ========================================
echo.

echo [1/3] Starting frontend container...
cd /d "%ROOT%"
docker compose up -d frontend

echo.
echo [2/3] Stopping backend container (using local backend instead)...
docker stop skin-cancer-backend >nul 2>&1

echo.
echo [3/3] Starting local backend with trained model...
start "Skin Cancer Backend" cmd /k "set UNCERTAINTY_THRESHOLD=0.35 && set LESION_FOCUS_MIN_RATIO=1.05 && set STRONG_CONFIDENCE_OVERRIDE=0.95 && cd /d \"%ROOT%backend\" && python main.py"

echo.
echo Open these URLs in browser:
echo Frontend: http://localhost:3000
echo Backend health: http://localhost:8000/health
echo.
echo Upload any image in the frontend to run model inference.
echo Keep the backend terminal window open during demo.
echo.
endlocal
