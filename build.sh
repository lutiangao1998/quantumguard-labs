#!/usr/bin/env bash
# QuantumGuard Labs - Render.com Build Script
# This script installs Python deps, builds the React frontend,
# and prepares the app for production.

set -e

echo "==> Installing Python dependencies..."
pip install -r requirements.txt

echo "==> Installing Node.js / pnpm..."
npm install -g pnpm

echo "==> Installing frontend dependencies..."
cd frontend
pnpm install --frozen-lockfile

echo "==> Building React frontend..."
pnpm build

cd ..
echo "==> Build complete."
