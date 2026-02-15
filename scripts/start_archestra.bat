@echo off
docker stop goofy_dijkstra 2>nul
docker rm goofy_dijkstra 2>nul
docker stop archestra-ngrok 2>nul
docker rm archestra-ngrok 2>nul

echo Starting Archestra with ngrok...
docker run -d --name archestra-ngrok ^
  -p 9000:9000 -p 3000:3000 ^
  -e ARCHESTRA_QUICKSTART=true ^
  -e ARCHESTRA_NGROK_AUTH_TOKEN=39h364UYdM78IIA6rNW4yiSa2RM_5KcFm6WE2CybwvNCTdt9W ^
  -v //var/run/docker.sock:/var/run/docker.sock ^
  -v archestra-postgres-data:/var/lib/postgresql/data ^
  -v archestra-app-data:/app/data ^
  archestra/platform

echo Container started. Logs follow:
timeout /t 5
docker logs archestra-ngrok
