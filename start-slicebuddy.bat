@echo off
cd /d "%~dp0"

docker info >nul 2>&1
if errorlevel 1 (
  echo Docker Desktop is not running. Start Docker Desktop, then run this file again.
  pause
  exit /b 1
)

docker compose up --build --detach
if errorlevel 1 (
  echo SliceBuddy could not start.
  pause
  exit /b 1
)

echo SliceBuddy is running at http://127.0.0.1:3000
echo To stop it later, run: docker compose down
pause
