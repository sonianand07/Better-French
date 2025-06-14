#!/usr/bin/env bash
# Simple helper to preview the static website locally.
# Usage: ./scripts/serve_ui.sh [PORT]
# Example: ./scripts/serve_ui.sh 8000

set -euo pipefail

PORT=${1:-8000}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SITE_DIR="${SCRIPT_DIR}/../Project-Better-French-Website"

cd "$SITE_DIR"

echo "Serving ${SITE_DIR} at http://localhost:${PORT}"
python3 -m http.server "${PORT}" 