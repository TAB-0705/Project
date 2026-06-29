# Movie Booking App — API Specification

**Version:** 1.0
**Base URL:** `http://localhost:8000` (local) · `https://<your-domain>` (production)
**Format:** All requests and responses are `application/json; charset=utf-8`.

> **Note on paths:** route strings and payload field names below follow the app's documented REST conventions. Reconcile them against your actual `app/routers/*.py` before publishing — the contract semantics (status codes, behaviour, errors) hold regardless of exact path spelling.

---

## Table of contents

- [Conventions](#conventions)
- [Authentication](#authentication)
- [Standard error format](#standard-error-format)
- [Endpoints](#endpoints)
  - [Auth](#auth)
  - [Catalog](#catalog)
  - [Bookings](#bookings)
  - [Admin](#admin)
  - [System](#system)
- [Error handling](#error-handling)
- [Data models](#data-models)

---

## Conventions

| Topic | Rule |
|-------|------|
| Timestamps | ISO 8601, UTC, timezone-aware (e.g. `2026-06-25T14:30:00Z`) |
| IDs | MongoDB ObjectId strings (24 hex chars) unless noted |
| Money | Integer rupees (₹), no decimals |
| Auth header | `Authorization: Bearer <access_token>` |
| Seat IDs | Zero-padded `<row><number>`, e.g. `A01`, `L12` |
| Booking status | `held` · `confirmed` · `cancelled` · `expired` |

---

## Authentication

The API uses **stateless JWT bearer tokens**.

1. Obtain a token via `POST /auth/login`.
2. Send it on every protected request: `Authorization: Bearer <access_token>`.
3. Tokens expire after `ACCESS_TOKEN_EXPIRE_MINUTES` (default 60). A request with a missing, malformed, or expired token returns **`401 Unauthorized`**.

Access levels:

| Level | How it's determined | Can access |
|-------|--------------------|------------|
| Public | No token | Catalog reads, register, login |
| User | Valid token, `role: user` | Booking flow + own bookings |
| Admin | Valid token, `role: admin` | Admin CRUD + read-only browse |

---

## Standard error format

All errors return an HTTP status in the `4xx`/`5xx` range and a JSON body:

```json
{ "detail": "Seat A05 is no longer available." }
```

Validation errors (`422`) use FastAPI's structured form:

```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "showtime_id"],
      "msg": "Field required"
    }
  ]
}
```

---

## Endpoints

### Auth

#### `POST /auth/register`
Create a new user account.

**Auth:** Public

**Request body**
```json
{ "email": "ada@example.com", "password": "s3cret-pass", "name": "Ada" }
```

**`201 Created`**
```json
{ "id": "665f...", "email": "ada@example.com", "name": "Ada", "role": "user" }
```

| Status | Condition |
|-------:|-----------|
| `201` | Account created |
| `409` | Email already registered |
| `422` | Invalid email or password too short |

---

#### `POST /auth/login`
Exchange credentials for an access token.

**Auth:** Public

**Request body**
```json
{ "email": "ada@example.com", "password": "s3cret-pass" }
```

**`200 OK`**
```json
{ "access_token": "eyJhbGci...", "token_type": "bearer", "expires_in": 3600 }
```

| Status | Condition |
|-------:|-----------|
| `200` | Authenticated |
| `401` | Invalid email or password |
| `422` | Missing fields |

---

#### `GET /auth/me`
Return the authenticated user's profile.

**Auth:** User / Admin

**`200 OK`**
```json
{ "id": "665f...", "email": "ada@example.com", "name": "Ada", "role": "user" }
```

| Status | Condition |
|-------:|-----------|
| `200` | OK |
| `401` | Missing / invalid / expired token |

---

### Catalog

#### `GET /movies`
List now-playing movies.

**Auth:** Public

**Query parameters**

| Param | Type | Required | Description |
|-------|------|:--------:|-------------|
| `city` | string | — | Filter to movies with showtimes in a city |
| `q` | string | — | Title search |

**`200 OK`**
```json
[
  {
    "id": "665f...",
    "title": "Interstellar",
    "runtime_minutes": 169,
    "genres": ["Sci-Fi", "Drama"],
    "certification": "UA",
    "poster_url": "https://image.tmdb.org/t/p/w500/..."
  }
]
```

| Status | Condition |
|-------:|-----------|
| `200` | OK (empty array if none match) |

---

#### `GET /movies/{movie_id}`
Get a single movie.

**Auth:** Public

| Status | Condition |
|-------:|-----------|
| `200` | OK |
| `404` | No movie with that id |

---

#### `GET /theaters`
List theatres, optionally filtered.

**Auth:** Public

**Query parameters**

| Param | Type | Required | Description |
|-------|------|:--------:|-------------|
| `city` | string | — | Filter by city (Vellore, Chennai, Bengaluru, Hyderabad) |
| `movie_id` | string | — | Only theatres screening this movie |

| Status | Condition |
|-------:|-----------|
| `200` | OK |

---

#### `GET /showtimes`
List showtimes for a movie/city/theatre.

**Auth:** Public

**Query parameters**

| Param | Type | Required | Description |
|-------|------|:--------:|-------------|
| `movie_id` | string | — | Filter by movie |
| `city` | string | — | Filter by city |
| `theater_id` | string | — | Filter by theatre |
| `date` | string (YYYY-MM-DD) | — | Filter by date |

**`200 OK`**
```json
[
  {
    "id": "665f...",
    "movie_id": "665f...",
    "theater_id": "665f...",
    "starts_at": "2026-06-26T18:30:00Z",
    "screen": "Audi 3",
    "seats_available": 142
  }
]
```

| Status | Condition |
|-------:|-----------|
| `200` | OK |

---

#### `GET /showtimes/{showtime_id}/seats`
Get the live seat map for a showtime.

**Auth:** Public

**`200 OK`**
```json
{
  "showtime_id": "665f...",
  "seats": [
    { "id": "A01", "tier": "Recliner", "price": 450, "status": "available" },
    { "id": "A02", "tier": "Recliner", "price": 450, "status": "sold" },
    { "id": "C05", "tier": "Prime",    "price": 300, "status": "held" }
  ]
}
```

`status` is one of `available`, `held`, `sold`.

| Status | Condition |
|-------:|-----------|
| `200` | OK |
| `404` | No showtime with that id |

---

### Bookings

#### `POST /bookings/hold`
Atomically hold one or more seats. **All-or-nothing.**

**Auth:** User

**Request body**
```json
{ "showtime_id": "665f...", "seats": ["A01", "A02"] }
```

**`201 Created`**
```json
{
  "booking_id": "665f...",
  "status": "held",
  "seats": ["A01", "A02"],
  "total_amount": 900,
  "hold_expires_at": "2026-06-25T14:35:00Z"
}
```

| Status | Condition |
|-------:|-----------|
| `201` | Hold placed |
| `400` | Empty seat list / unknown seat IDs for this showtime |
| `401` | Not authenticated |
| `404` | Showtime not found |
| `409` | One or more requested seats are already held or sold |

> On `409`, **no** seats are held — the request is rejected as a whole. Re-fetch the seat map and retry with available seats.

---

#### `POST /bookings/{booking_id}/confirm`
Run mock payment and convert a live hold into a confirmed booking.

**Auth:** User (must own the booking)

**`200 OK`**
```json
{
  "booking_id": "665f...",
  "status": "confirmed",
  "seats": ["A01", "A02"],
  "total_amount": 900,
  "confirmed_at": "2026-06-25T14:33:10Z"
}
```

| Status | Condition |
|-------:|-----------|
| `200` | Confirmed |
| `401` | Not authenticated |
| `403` | Booking belongs to another user |
| `404` | Booking not found |
| `409` | Booking already confirmed or cancelled |
| `410` | Hold expired before confirm — seats released |

---

#### `POST /bookings/{booking_id}/cancel`
Release a held or confirmed booking; seats return to the pool.

**Auth:** User (must own the booking)

**`200 OK`**
```json
{ "booking_id": "665f...", "status": "cancelled" }
```

| Status | Condition |
|-------:|-----------|
| `200` | Cancelled |
| `401` | Not authenticated |
| `403` | Booking belongs to another user |
| `404` | Booking not found |
| `409` | Booking already cancelled |

---

#### `GET /bookings/me`
List the authenticated user's bookings.

**Auth:** User

| Status | Condition |
|-------:|-----------|
| `200` | OK |
| `401` | Not authenticated |

---

#### `GET /bookings/{booking_id}`
Get a single booking (ticket view).

**Auth:** User (must own the booking) / Admin

| Status | Condition |
|-------:|-----------|
| `200` | OK |
| `401` | Not authenticated |
| `403` | Booking belongs to another user |
| `404` | Booking not found |

---

### Admin

All admin routes require a token with `role: admin`. A valid non-admin token returns **`403 Forbidden`**.

#### `POST /admin/movies` · `PUT /admin/movies/{id}` · `DELETE /admin/movies/{id}`
Create, update, delete a movie.

| Status | Condition |
|-------:|-----------|
| `201` / `200` | Created / updated |
| `204` | Deleted |
| `401` | Not authenticated |
| `403` | Not an admin |
| `404` | Movie not found (update/delete) |
| `422` | Invalid body |

---

#### `POST /admin/theaters` · `PUT /admin/theaters/{id}` · `DELETE /admin/theaters/{id}`
Manage theatres. Same status semantics as movies.

---

#### `POST /admin/showtimes` · `PUT /admin/showtimes/{id}` · `DELETE /admin/showtimes/{id}`
Manage showtimes. Creation/update validates that the new showtime does **not overlap** an existing one on the same screen.

| Status | Condition |
|-------:|-----------|
| `201` / `200` | Created / updated |
| `204` | Deleted |
| `401` | Not authenticated |
| `403` | Not an admin |
| `404` | Showtime / referenced movie / theatre not found |
| `409` | Showtime overlaps an existing one on the same screen |
| `422` | Invalid body (e.g. `starts_at` in the past) |

---

### System

#### `GET /health`
Liveness/readiness probe. Pings MongoDB.

**Auth:** Public

**`200 OK`**
```json
{ "status": "ok", "database": "connected" }
```

| Status | Condition |
|-------:|-----------|
| `200` | Service + DB healthy |
| `503` | Database unreachable |

---

## Error handling

### Global status codes

| Status | Name | When it occurs | `detail` example |
|-------:|------|----------------|------------------|
| `400` | Bad Request | Semantically invalid input that passes schema validation (empty seat list, unknown seat ID) | `"Seat list cannot be empty."` |
| `401` | Unauthorized | Missing, malformed, or expired token | `"Could not validate credentials."` |
| `403` | Forbidden | Authenticated but not permitted (non-admin on admin route; other user's booking) | `"Admin privileges required."` |
| `404` | Not Found | Referenced resource does not exist | `"Showtime not found."` |
| `409` | Conflict | State conflict — seat taken, double-booking prevented, overlap, already-finalized booking | `"Seats no longer available: A05."` |
| `410` | Gone | Hold expired before confirm | `"Hold expired. Please select seats again."` |
| `422` | Unprocessable Entity | Pydantic request validation failed | structured array (see above) |
| `500` | Internal Server Error | Unhandled exception | `"Internal server error."` |
| `503` | Service Unavailable | Dependency (MongoDB) down — `/health` | `"Database unreachable."` |

### Domain-specific conflicts (`409`)

| Scenario | Endpoint | Resolution |
|----------|----------|-----------|
| Seat already held/sold | `POST /bookings/hold` | Re-fetch seat map; pick free seats. No partial hold occurs. |
| Confirm an already-finalized booking | `POST /bookings/{id}/confirm` | Booking is terminal; start a new hold. |
| Cancel an already-cancelled booking | `POST /bookings/{id}/cancel` | No-op conflict; nothing to release. |
| Overlapping showtime on a screen | `POST/PUT /admin/showtimes` | Choose a non-overlapping slot or screen. |

### Hold expiry (`410`)

A hold lives for `SEAT_HOLD_TTL_SECONDS` (default 300s). Expiry is evaluated **on read** — confirming an expired hold returns `410` and the seats are already reclaimable by others. The client should return the user to seat selection.

---

## Data models

### User
```json
{ "id": "str", "email": "str", "name": "str", "role": "user | admin" }
```

### Movie
```json
{
  "id": "str", "title": "str", "runtime_minutes": "int",
  "genres": ["str"], "certification": "str", "poster_url": "str"
}
```

### Theater
```json
{ "id": "str", "name": "str", "city": "str", "screens": ["str"] }
```

### Showtime
```json
{
  "id": "str", "movie_id": "str", "theater_id": "str",
  "screen": "str", "starts_at": "datetime", "seats_available": "int"
}
```

### Seat
```json
{ "id": "str", "tier": "str", "price": "int", "status": "available | held | sold" }
```

### Booking
```json
{
  "booking_id": "str", "user_id": "str", "showtime_id": "str",
  "seats": ["str"], "total_amount": "int",
  "status": "held | confirmed | cancelled | expired",
  "hold_expires_at": "datetime | null", "confirmed_at": "datetime | null"
}
```
