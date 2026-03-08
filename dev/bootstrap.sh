#!/bin/bash
set -e

# Installiert Test-Dependencies in einem lokalen venv
# Das venv ist getrennt vom HA-System-Python im Container
PYTHON="/usr/local/bin/python3.13"

if [ ! -f "$PYTHON" ]; then
  # Fallback: python3 im PATH
  PYTHON="python3"
fi

if [ ! -d "dev/.venv" ]; then
  echo "Creating virtual environment in dev/.venv ..."
  $PYTHON -m venv dev/.venv
fi

echo "Activating venv and installing requirements..."
. dev/.venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

echo ""
echo "✅ Dev environment ready!"
echo "   ▶  HA UI (auto-started): http://localhost:8123"
echo "   ▶  Run tests:  source dev/.venv/bin/activate && pytest"
echo "   ▶  HA logs:    tail -f /var/log/ha.log"
