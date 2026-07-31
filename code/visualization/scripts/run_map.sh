#!/usr/bin/env bash
# Sync consolidated JR database → map inputs, then build interactive map.
# Requires: output/result/cross_group.csv
#           output/jr_database/merge_cross_assertions.csv
set -euo pipefail
cd "$(dirname "$0")/../../.."

echo "==> Sync map inputs from jr_database…"
uv run python -B code/visualization/sync_from_jr_database.py

echo ""
echo "==> Build map…"
uv run python -B code/visualization/build_cross_group_map.py "$@"

echo ""
echo "Outputs:"
echo "  output/visualization/between_group_joking.xlsx"
echo "  output/visualization/jr_records.json"
echo "  output/visualization/cross_group_jr_map.html"
