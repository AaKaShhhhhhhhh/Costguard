@echo off
echo Starting Costguard Services...
cd /d "%~dp0.."
docker-compose up -d --build --remove-orphans
echo.
echo Checking status...
docker-compose ps
echo.
echo Costguard should be ready at:
echo Dashboard: http://localhost:8501
echo Backend:   http://localhost:8000
echo.
pause
