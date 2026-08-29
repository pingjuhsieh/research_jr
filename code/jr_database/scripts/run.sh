#!/usr/bin/env bash
# Build JR database deliverables under output/jr_database/ (pairs + map).
set -euo pipefail
cd "$(dirname "$0")/../../.."

APPLY=()
NO_MAP=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --apply-unmatched) APPLY=(--apply-unmatched); shift ;;
    --no-map) NO_MAP=1; shift ;;
    *) echo "Unknown arg: $1" >&2; exit 2 ;;
  esac
done

echo "==> Build cross-group JR database…"
if [[ "$NO_MAP" -eq 1 ]]; then
  uv run python -B code/jr_database/build_cross_group.py "${APPLY[@]:-}" --no-map
else
  uv run python -B code/jr_database/build_cross_group.py "${APPLY[@]:-}"
fi

echo ""
echo "Outputs in output/jr_database/:"
echo "  cross_group.xlsx · merge_cross_assertions.csv · RA_workpack.xlsx"
[[ "$NO_MAP" -eq 0 ]] && echo "  jr_map.html"
echo "(see output/jr_database/README.md)"
