# ── Stage 1: Build React frontend ─────────────────────────────────────────────
FROM node:22-alpine AS frontend-builder

WORKDIR /app/frontend

# Install pnpm
RUN npm install -g pnpm

# Copy package files
COPY frontend/package.json frontend/pnpm-lock.yaml ./

# Install dependencies
RUN pnpm install --frozen-lockfile

# Copy source
COPY frontend/ ./

# Build
RUN pnpm build

# ── Stage 2: Python backend ────────────────────────────────────────────────────
FROM python:3.11-slim

WORKDIR /app

# System dependencies for reportlab (PDF generation)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libfreetype6 \
    && rm -rf /var/lib/apt/lists/*

# Copy Python requirements
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source
COPY quantumguard/ ./quantumguard/
COPY api/ ./api/

# Copy built frontend from stage 1
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Expose port
EXPOSE 8000

# Start FastAPI
CMD ["python", "-m", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
