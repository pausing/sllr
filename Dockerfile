# Multi-stage Dockerfile for SLLR
# Stage 1: Install Node.js 22.14 (Nixpacks default 22.10 breaks Vite 8)
FROM python:3.12-slim as node-install

WORKDIR /tmp
COPY scripts/install-node.sh .
RUN bash install-node.sh

# Stage 2: Build frontend
FROM node-install as frontend-build

WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 3: Python backend + frontend dist
FROM python:3.12-slim

WORKDIR /app

# Copy Node.js from node-install stage (optional, only if needed for runtime)
# COPY --from=node-install /usr/local/node /usr/local/node

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY backend/ ./backend/
COPY src/ ./src/
COPY data/ ./data/
COPY scripts/ ./scripts/
COPY docs/ ./docs/

# Copy built frontend
COPY --from=frontend-build /app/frontend/dist ./frontend/dist

# Environment variables
ENV SLLR_DATA_DIR=/data
ENV STATIC_DIR=frontend/dist
ENV PYTHONUNBUFFERED=1
ENV PORT=8000
ENV PYTHONPATH=/app:/app/src

# Volume for persistent data
VOLUME /data

EXPOSE 8000

# Run FastAPI with Uvicorn
CMD ["sh", "-c", "PYTHONPATH=/app:/app/src uvicorn backend.app.main:app --host 0.0.0.0 --port 8000"]
