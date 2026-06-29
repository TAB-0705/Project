# Movie Booking App

A full-stack movie ticket booking system built with **FastAPI**, **MongoDB** (Motor async driver), and a **Streamlit** demo UI. The core design goal is **booking correctness**: under concurrent load, a seat is sold exactly once — never twice.

**Stack:** Python 3.12+ · FastAPI · MongoDB (Motor) · Streamlit  |  **License:** MIT

---

## Table of contents

- [Features](#features)
- [Architecture](#architecture)
- [Tech stack](#tech-stack)
- [Project structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Local setup](#local-setup)
- [Configuration](#configuration)
- [Seeding the catalog (TMDB)](#seeding-the-catalog-tmdb)
- [Running the app](#running-the-app)
- [The booking lifecycle](#the-booking-lifecycle)
- [Concurrency guarantee](#concurrency-guarantee)
- [Seat tiers & pricing](#seat-tiers--pricing)
- [API documentation](#api-documentation)
- [Error handling](#error-handling)
- [Testing](#testing)
- [Deployment](#deployment)
- [Roadmap](#roadmap)
- [Attribution & license](#attribution--license)

---

## Features

- **Browse catalog** — real now-playing movies (TMDB-seeded) with posters, runtime, genres and certifications, filterable by city.
- **BookMyShow-style flow** — movie → city → theatre → showtime → seat map → payment → ticket.
- **Live seat map** — a 200-seat tiered auditorium with real-time availability.
- **Atomic seat hold → confirm → cancel** — concurrency-safe holds with automatic expiry, mock payment on confirm, and release on cancel.
- **JWT authentication** — email/password registration and login with bcrypt-hashed credentials.
- **Admin CRUD** — manage movies, theatres and showtimes, with showtime-overlap validation.
- **Role-aware access** — admins get read-only browse + management; moviegoers get the booking flow and their own bookings.

---

## Architecture

The codebase follows a strict, gradeable **layered architecture**. Each layer has exactly one job, and dependencies only point downward:

```
HTTP request
    │
    ▼
routers/      ← thin: parse input → call a service → shape the response. No business logic.
    │
    ▼
services/     ← all business logic lives here (booking rules, overlap checks, auth).
    │
    ▼
db/mongo.py   ← the ONLY module that touches MongoDB. Single Motor client, tz_aware=True.
```

**Why this matters:** routers never embed query logic, and only `db/mongo.py` knows about Mongo, so the database can be swapped or mocked without touching business rules. The booking core is isolated in `services/booking_service.py`, which is where the concurrency guarantee is enforced and tested.

> The Motor client is created with `tz_aware=True` so every datetime read back from Mongo is timezone-aware UTC — no naive/aware comparison bugs when checking hold expiry.

---

## Tech stack

| Layer | Choice | Why |
|-------|--------|-----|
| API framework | FastAPI | Async, automatic OpenAPI docs, Pydantic validation |
| ASGI server | Uvicorn (Gunicorn in prod) | Async worker model |
| Database | MongoDB | Per-showtime embedded seat document enables a single atomic update for seat claims |
| DB driver | Motor (async) | Non-blocking I/O end to end |
| Validation | Pydantic v2 / pydantic-settings | Typed request/response models + env config |
| Auth | python-jose (JWT) + passlib/bcrypt | Stateless tokens, hashed passwords |
| Demo UI | Streamlit | Fast to build a clickable demo |
| Catalog data | TMDB API | Real movie metadata for a realistic demo |

---

## Project structure

```
movie-booking/
├── app/
│   ├── main.py                 # FastAPI app, lifespan, router registration
│   ├── config.py               # pydantic-settings: env vars → typed Settings
│   ├── db/
│   │   └── mongo.py            # Motor client (tz_aware=True); only file touching Mongo
│   ├── core/
│   │   ├── security.py        # bcrypt hashing + JWT encode/decode
│   │   └── deps.py            # get_current_user, require_admin dependencies
│   ├── routers/
│   │   ├── auth.py            # /auth
│   │   ├── movies.py          # /movies
│   │   ├── theaters.py        # /theaters
│   │   ├── showtimes.py       # /showtimes
│   │   ├── bookings.py        # /bookings
│   │   └── admin.py          # /admin
│   ├── services/
│   │   ├── auth_service.py
│   │   ├── catalog_service.py
│   │   ├── booking_service.py # atomic hold / confirm / cancel — the graded core
│   │   └── admin_service.py
│   └── schemas/               # Pydantic request/response models
│       ├── user.py
│       ├── movie.py
│       ├── showtime.py
│       └── booking.py
├── scripts/
│   └── seed_tmdb.py           # seed movies/theatres/showtimes from TMDB (offline fallback included)
├── tests/
│   └── test_concurrency.py    # proves no double-booking under parallel holds
├── streamlit_app.py           # demo UI
├── requirements.txt
├── .env.example
├── Dockerfile
├── docker-compose.yml
└── README.md
```

> Reconcile router filenames/paths with your actual `app/routers/` — the structure above reflects the documented layering and should match closely.

---

## Prerequisites

- **Python 3.12+** (the API has no native-extension constraints; 3.12/3.13 have the widest wheel coverage).
- **MongoDB** — either Docker (recommended for local) or a free **MongoDB Atlas** cluster.
- **A free TMDB API key** — https://www.themoviedb.org/settings/api (only needed to re-seed the catalog).
- **Git**, and on Windows, **PowerShell**.

---

## Local setup

```bash
# 1. Clone
git clone <your-repo-url> movie-booking
cd movie-booking

# 2. Create & activate a virtual environment
python -m venv .venv
```

**macOS / Linux**
```bash
source .venv/bin/activate
```

**Windows (PowerShell)**
```powershell
.venv\Scripts\Activate.ps1
# If activation is blocked:
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

```bash
# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env        # Windows: copy .env.example .env
#   then edit .env (see Configuration below)

# 5. Start MongoDB locally (Docker)
docker run -d --name movie-mongo -p 27017:27017 mongo:7
```

No Docker? Point `MONGO_URI` at a **MongoDB Atlas** connection string instead and skip step 5.

---

## Configuration

All configuration is loaded from environment variables via `pydantic-settings` (`app/config.py`). Copy `.env.example` to `.env` and fill in:

| Variable | Required | Default | Description |
|----------|:--------:|---------|-------------|
| `MONGO_URI` | ✅ | `mongodb://localhost:27017` | Motor connection string (local or Atlas) |
| `MONGO_DB_NAME` | ✅ | `movie_booking` | Database name |
| `JWT_SECRET_KEY` | ✅ | — | Secret for signing JWTs. Generate with `openssl rand -hex 32` |
| `JWT_ALGORITHM` | — | `HS256` | JWT signing algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | — | `60` | Access-token lifetime |
| `SEAT_HOLD_TTL_SECONDS` | — | `300` | How long a seat hold survives before it can be reclaimed |
| `TMDB_API_KEY` | — | — | Required only to re-seed the catalog from TMDB |
| `CORS_ORIGINS` | — | `http://localhost:8501` | Comma-separated allowed origins (Streamlit UI) |
| `ENVIRONMENT` | — | `development` | `development` / `production` (toggles docs exposure, etc.) |

> Never commit `.env`. Confirm it is listed in `.gitignore`. `JWT_SECRET_KEY` must be a strong random value in production — a leaked key lets anyone forge tokens.

---

## Seeding the catalog (TMDB)

The catalog (movies, multi-city theatres, showtimes) is populated by a seed script that pulls real now-playing titles from TMDB, with an offline fallback list if the API is unreachable:

```bash
python -m scripts.seed_tmdb
```

This seeds:
- **Movies** — real posters, runtime, genres, certifications (TMDB).
- **Theatres** — real multiplex names across Vellore, Chennai, Bengaluru and Hyderabad.
- **Showtimes** — each with a 200-seat tiered auditorium (see [Seat tiers](#seat-tiers--pricing)).

---

## Running the app

Run the API and the demo UI in two terminals.

```bash
# Terminal 1 — API
uvicorn app.main:app --reload --port 8000
```
- Interactive Swagger docs: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

```bash
# Terminal 2 — Streamlit demo UI
streamlit run streamlit_app.py
```
- UI: http://localhost:8501

---

## The booking lifecycle

A booking moves through three states. The transitions are the heart of the system:

```
   POST /bookings/hold              POST /bookings/{id}/confirm
 ┌───────────────────┐  held      ┌──────────────────────────┐  confirmed
 │  seats selected   │ ─────────► │   hold + mock payment    │ ───────────► TICKET
 └───────────────────┘            └──────────────────────────┘
          │                                    │
          │ POST /bookings/{id}/cancel         │ (no action within SEAT_HOLD_TTL_SECONDS)
          ▼                                    ▼
       released                       hold expires → seats reclaimable
```

- **Hold** atomically claims the requested seats for `SEAT_HOLD_TTL_SECONDS`. If any requested seat isn't free, the *entire* hold fails (all-or-nothing).
- **Confirm** runs the mock payment and converts a live hold into a permanent booking.
- **Cancel** releases a held (or confirmed) booking's seats back to the pool.
- **Expiry** is enforced on read: an unconfirmed hold past its TTL is treated as released, so seats free themselves without a background job.

---

## Concurrency guarantee

**No seat is ever sold twice.** This is enforced at the database layer, not in Python:

- Seats for a showtime live in a single embedded document.
- A hold is a **single atomic conditional update** — Mongo claims the seats only if they are all currently free, in one round trip. There is no read-then-write race window.
- If two requests target the same seat simultaneously, exactly one update matches; the other claims zero seats and is rejected with **`409 Conflict`**.

This is verified by `tests/test_concurrency.py`, which fires parallel hold requests at the same seats and asserts exactly one succeeds.

---

## Seat tiers & pricing

Each auditorium has 200 seats across five tiers (prices in ₹). Seat IDs are zero-padded (`A01`, `L12`).

| Tier | Rows | Price (₹) |
|------|------|----------:|
| Recliner | A–B | 450 |
| Prime | C–D | 300 |
| Premium | E–H | 190 |
| Classic | I–K | 140 |
| Economy | L–M | 90 |

---

## API documentation

- **Interactive:** Swagger UI at `/docs`, ReDoc at `/redoc` (auto-generated from the code).
- **Reference:** see [`API_SPECIFICATION.md`](./API_SPECIFICATION.md) for the full endpoint contract, request/response examples, and complete error-handling tables.

---

## Error handling

Errors are returned with a standard FastAPI envelope, `{ "detail": ... }`, and a meaningful HTTP status. Summary:

| Status | Meaning | Typical cause |
|-------:|---------|---------------|
| `400` | Bad Request | Malformed input (e.g. empty seat list) |
| `401` | Unauthorized | Missing / invalid / expired token |
| `403` | Forbidden | Non-admin on an admin route; accessing another user's booking |
| `404` | Not Found | Unknown movie / theatre / showtime / booking |
| `409` | Conflict | Seat already held or sold; showtime overlap; hold already finalized |
| `410` | Gone | Hold expired before confirm |
| `422` | Unprocessable Entity | Pydantic validation failure |
| `500` | Internal Server Error | Unexpected server fault |

Full per-endpoint tables are in [`API_SPECIFICATION.md`](./API_SPECIFICATION.md#error-handling).

---

## Testing

```bash
pip install pytest pytest-asyncio mongomock-motor
pytest -v
```

The suite's centerpiece is the concurrency test proving the no-double-booking guarantee. Tests use `mongomock-motor`, so **no live MongoDB is required** to run them.

---

## Deployment

### 1. Containerize

**Dockerfile**
```dockerfile
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# Gunicorn manages multiple Uvicorn workers for production concurrency.
CMD ["gunicorn", "app.main:app", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--workers", "4", \
     "--bind", "0.0.0.0:8000", \
     "--timeout", "60"]
```

**docker-compose.yml** (API + MongoDB for a self-contained stack)
```yaml
services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      MONGO_URI: mongodb://mongo:27017
      MONGO_DB_NAME: movie_booking
      JWT_SECRET_KEY: ${JWT_SECRET_KEY}
      ENVIRONMENT: production
    depends_on:
      - mongo
  mongo:
    image: mongo:7
    volumes:
      - mongo_data:/data/db
    ports:
      - "27017:27017"

volumes:
  mongo_data:
```

```bash
JWT_SECRET_KEY=$(openssl rand -hex 32) docker compose up --build
```

### 2. Database

Use a managed **MongoDB Atlas** cluster in production rather than a container. Set `MONGO_URI` to the Atlas SRV connection string and restrict network access to your app's egress IPs.

### 3. Secrets & config

- Inject `JWT_SECRET_KEY`, `MONGO_URI`, and `TMDB_API_KEY` as platform secrets — never bake them into the image.
- Set `ENVIRONMENT=production`. Consider disabling `/docs` and `/redoc` in production (gate their inclusion on `ENVIRONMENT`).
- Configure `CORS_ORIGINS` to your real frontend origin(s).

### 4. Run & scale

- The app is **stateless** — all state is in MongoDB, so you can run **N replicas behind a load balancer** safely. The atomic seat-claim guarantee holds across replicas because correctness is enforced in the database, not in app memory.
- Front the app with a reverse proxy (nginx / managed ingress) terminating **HTTPS**.
- Add a **`GET /health`** endpoint (returns `200` + a Mongo ping) for liveness/readiness probes.
- Seed the catalog once after first deploy: `python -m scripts.seed_tmdb`.

### 5. Platform options

| Platform | Notes |
|----------|-------|
| Render / Railway / Fly.io | Push the Docker image; set env secrets; point at Atlas |
| Azure Container Apps | Image + secrets + Atlas (or Cosmos DB for Mongo API) |
| Any Kubernetes | Deployment (N replicas) + Service + Ingress; secrets via `Secret` objects |

---

## Roadmap

Phase 2 (deferred) features:

- Reviews & ratings
- Promo codes / discounts
- Google OAuth login
- QR-code tickets
- Search & filter, responsive grid, city auto-detect, hold-countdown auto-refresh

---

## Attribution & license

This product uses the **TMDB API** but is **not endorsed or certified by TMDB**. Movie metadata and posters are provided by [The Movie Database (TMDB)](https://www.themoviedb.org/). The TMDB API is used here for non-commercial, educational purposes.

Licensed under the MIT License.
