@echo off
cd /d "%~dp0"
docker compose down
echo SliceBuddy has stopped.
pause
