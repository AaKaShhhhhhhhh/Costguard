@echo off
echo !!! Aggressive Cleanup Starting !!!
echo Stopping all running containers to free up ports...
FOR /f "tokens=*" %%i IN ('docker ps -q') DO docker stop %%i
echo Removing all containers...
FOR /f "tokens=*" %%i IN ('docker ps -aq') DO docker rm %%i
echo Cleanup done.

echo Removing volumes...
docker volume rm archestra-app-data archestra-postgres-data 2>nul
echo Volumes removed.

echo Starting Archestra...
docker run -d -p 9000:9000 -p 3000:3000 -e ARCHESTRA_QUICKSTART=true -e ARCHESTRA_NGROK_AUTH_TOKEN=39h364UYdM78IIA6rNW4yiSa2RM_5KcFm6WE2CybwvNCTdt9W -v //var/run/docker.sock:/var/run/docker.sock -v archestra-postgres-data:/var/lib/postgresql/data -v archestra-app-data:/app/data --name archestra-hackathon archestra/platform

echo.
echo Archestra is starting! 
echo Please wait 3-5 minutes for it to initialize.
echo Then check http://localhost:3000 for the NEW login credentials.
echo.
echo To see logs, run: docker logs -f archestra-hackathon
