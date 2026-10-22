#!/usr/bin/env bash
# Convenience launcher for AI Content Detector
set -e

# Detect virtual environment if present
if [ -d "venv" ]; then
  source venv/bin/activate
elif [ -d ".venv" ]; then
  source .venv/bin/activate
fi

echo "============================================================"
echo " Starting AI Content Detector"
echo " Access frontend at: http://localhost:8000"
echo " Health check at:    http://localhost:8000/health"
echo "============================================================"

# Launch the single uvicorn process
uvicorn app.main:app --host 0.0.0.0 --port 8000
