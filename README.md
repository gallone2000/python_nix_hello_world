# Hello World FastAPI + Nix (no pip/venv)

This repository is a **simple FastAPI application** written in Python.

Instead of the more common approach:

- installing dependencies with `pip` into a virtual environment (`.venv`), and
- building/running from an official Python image like `python:3.14`

…this project uses **Nix** (via a `flake.nix`) to provide **Python and all Python dependencies** from **nixpkgs**.

## Why Nix here?

Using Nix gives you:

- **Reproducibility**: the dependency set is pinned by `flake.lock`, so the same inputs produce the same environment.
- **Fewer surprises across machines**: teammates on different laptops/OSes (and CI) get the same Python + libs, without “works on my machine” drift.
- **No venv management**: no `pip install`, no `uv sync`, no `.venv` to keep in sync.

---

## What’s inside

### API endpoints

- `GET /` → `{"message": "Hello World"}`
- `GET /hello/{name}` → `{"message": "Hello {name}"}`
- `GET /health` → `{"status": "ok"}`

### Entry point

The application lives in `main.py` and exposes `app`, so Uvicorn runs it as:

- `main:app`

---

## Requirements

- **Nix** with flakes enabled
- Optional: **Docker** (for container builds/runs)
- Optional: **make** (to use the provided Makefile commands)

---

## Run locally (development)

Enter the Nix development shell:

```bash
nix develop
```

Sanity check:

```bash
python -c "import fastapi, uvicorn; print('ok')"
```

Run the server:

```bash
python -m uvicorn main:app --reload
```

Open:

- http://127.0.0.1:8000/
- http://127.0.0.1:8000/hello/Alice
- http://127.0.0.1:8000/health

---

## How dependencies work

Dependencies are **not** installed via `pip`.

They are declared in `flake.nix` using nixpkgs Python packages, for example:

- `pkgs.python314Packages.fastapi`
- `pkgs.python314Packages.uvicorn`

Nix builds a Python environment (often called `pyEnv`) with:

```nix
python.withPackages (ps: with ps; [
  fastapi
  uvicorn
])
```

The exact nixpkgs revision is pinned by `flake.lock`.

---

## Docker (distroless runtime)

This project can be containerized without relying on `python:3.14` images.

A typical pattern is:

1. Build the Nix Python environment in a `nixos/nix` builder stage
2. Copy the minimal required `/nix/store` closure + app sources
3. Run on a small runtime image (e.g. distroless)

---

## Makefile commands

A Makefile is included to simplify building and running the container.

### Common workflow

Build the image:

```bash
make build
```

Start the service:

```bash
make start
```

Follow logs:

```bash
make logs
```

Check health:

```bash
make health
```

Stop the service:

```bash
make stop
```

Remove containers:

```bash
make down
```

See status:

```bash
make status
```

Show all targets:

```bash
make help
```

### Variables

You can override variables like this:

```bash
make start PORT=9000 HOST=0.0.0.0
```

Key vars:

- `IMAGE` (default: app name)
- `CONTAINER` (default: app name)
- `PORT` (default: 8000)
- `HOST` (default: 127.0.0.1)

### Docker Compose autodetect

If `compose.yml` or `docker-compose.yml` exists, `make start/stop/logs/...` will use `docker compose`.
Otherwise it falls back to `docker run`.

### Debug shell

Because distroless images do not include a shell, the Makefile provides:

```bash
make shell
```

This opens a `nixos/nix` container with your repo mounted at `/app` for debugging.

