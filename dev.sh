#!/bin/bash
# Development server with Tailwind CSS watch mode
# Run with: ./dev.sh

echo "🚀 Starting Mimo development environment..."
echo ""

# Start Tailwind CSS in watch mode (background)
echo "📦 Starting Tailwind CSS watch mode..."
pnpm dev:css &
TAILWIND_PID=$!

# Wait a bit for Tailwind to start
sleep 2

# Start FastAPI server
echo "🐍 Starting FastAPI server..."
uv run uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload

# Cleanup: kill Tailwind when FastAPI stops
trap "kill $TAILWIND_PID 2>/dev/null" EXIT
