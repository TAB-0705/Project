# Dockerizing the To-Do FastAPI App

A multi-stage `Dockerfile` containerizes the app. Place it (and `.dockerignore`)
at the project root, next to `requirements.txt` and the `app/` folder:

```
todo-api/
  Dockerfile
  .dockerignore
  requirements.txt
  app/
    main.py
    ...
```

## Build & run

```powershell
docker build -t todo-api .
docker run -p 8000:8000 todo-api
```

Open http://127.0.0.1:8000/docs

## Why multi-stage?

The build has two stages:

1. **builder** — installs the Python dependencies into a virtual environment at
   `/opt/venv`. Any build tools and pip caches stay in this stage.
2. **runtime** — a fresh slim image that copies *only* the finished `/opt/venv`
   and the `app/` code. The build machinery from stage 1 is discarded.

Result: a smaller final image with less attack surface, because the compiler
toolchain and caches never ship.

## Other choices, and why

- **`python:3.12-slim`** — slim base keeps the image small. The container's
  Python is independent of your host's 3.14, so the wheel issues you hit locally
  don't apply here.
- **Non-root `appuser`** — containers shouldn't run as root; if the app is
  compromised, the blast radius is smaller.
- **`--host 0.0.0.0`** — inside a container, binding to localhost would make the
  server unreachable from your machine. `0.0.0.0` exposes it on the published
  port.
- **`.dockerignore`** — stops `.venv`, `.git`, caches, etc. from bloating the
  build context and accidentally landing in the image.
- **`PYTHONUNBUFFERED=1`** — so logs appear immediately in `docker logs`.
