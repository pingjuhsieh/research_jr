#!/usr/bin/env bash
# Build map only (needs existing cross_group + assertions in output/jr_database/).
set -euo pipefail
cd "$(dirname "$0")/../../.."

echo "==> Sync map inputs from jr_database…"
uv run python -B code/visualization/sync_from_jr_database.py

echo ""
echo "==> Build map…"
uv run python -B code/visualization/build_cross_group_map.py "$@"

echo ""
echo "Outputs:"
echo "  output/jr_database/cross_group_map.xlsx"
echo "  output/jr_database/jr_records.json"
echo "  output/jr_database/cross_group_jr_map.html"
