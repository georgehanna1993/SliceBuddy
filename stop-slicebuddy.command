#!/bin/sh
set -eu

cd "$(dirname "$0")"
docker compose down
printf '%s\n' "SliceBuddy has stopped."
