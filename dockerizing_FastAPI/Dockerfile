# syntax=docker/dockerfile:1

# ---------- Stage 1: builder ----------
# Installs dependencies into an isolated virtual environment. Build tools and
# pip caches live ONLY in this stage and are thrown away — they never reach the
# final image.
FROM python:3.12-slim AS builder

# Create the venv we'll later copy into the runtime stage.
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


# ---------- Stage 2: runtime ----------
# A clean, slim image that contains only the venv and the app code.
FROM python:3.12-slim

# Don't write .pyc files; flush logs straight to the container output.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

# Run as a non-root user for security.
RUN useradd --create-home appuser

# Copy the ready-made virtual environment from the builder stage.
COPY --from=builder /opt/venv /opt/venv

WORKDIR /app
COPY app ./app

USER appuser
EXPOSE 8000

# 0.0.0.0 so the server is reachable from outside the container.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
