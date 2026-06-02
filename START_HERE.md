# Start SliceBuddy Locally

SliceBuddy runs entirely on your computer. It does not require an OpenAI API
key, an account, or a paid service.

## Before You Start

Install and start [Docker Desktop](https://www.docker.com/products/docker-desktop/).

## macOS

Double-click:

```text
start-slicebuddy.command
```

## Windows

Double-click:

```text
start-slicebuddy.bat
```

## Any Operating System

Open a terminal in this folder and run:

```bash
docker compose up --build --detach
```

Then open:

```text
http://127.0.0.1:3000
```

## Stop SliceBuddy

Use the matching `stop-slicebuddy` file, or run:

```bash
docker compose down
```

## Troubleshooting

- Keep Docker Desktop running while using SliceBuddy.
- The first startup takes longer because Docker downloads and builds the local
  app images.
- Make sure ports `3000` and `8000` are not already used by another program.
- Uploaded STL and 3MF files are processed temporarily and removed after analysis.
