#!/bin/sh
set -eu

cd "$(dirname "$0")"

if ! docker info >/dev/null 2>&1; then
  printf '%s\n' "Docker Desktop is not running. Start Docker Desktop, then run this file again."
  printf '%s' "Press Enter to close..."
  read answer
  exit 1
fi

docker compose up --build --detach

printf '%s\n' "SliceBuddy is running at http://127.0.0.1:3000"
printf '%s\n' "To stop it later, run: docker compose down"
