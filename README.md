# ICMID PingJu — joking relationship research

Python **3.12+** ([uv](https://docs.astral.sh/uv/)). Stata / R for settlement & climate.

## Quick start

```bash
uv sync
cp .env.example .env   # OPENAI_API_KEY

# 1) LLM from eHRAF (if rebuilding extraction)
uv run python -B code/llm_ehraf/run.py all

# 2) Consolidated cross-group JR database
uv run python -B code/jr_database/build_cross_group.py

# 3) Optional map
bash code/visualization/scripts/run_map.sh
```

Final clean cross-group table: **`output/result/cross_group.xlsx`**

---

## Layout

```
ICMID PingJu/
├── code/
│   ├── llm_ehraf/       # PDF → LLM extraction (eHRAF)
│   ├── jr_database/     # Merge sources → master cross-group + homeland
│   ├── visualization/   # Interactive map
│   ├── settlement/
│   └── climate/
├── data/                # RAW inputs only (PDFs, GIS, original tables)
├── output/
│   ├── llm_ehraf/       # LLM intermediates
│   ├── jr_database/     # Merge intermediates + unmatched sheet
│   └── result/          # Final clean products
├── literature/
└── PIPELINE.md
```

| Path | Role |
|------|------|
| `code/llm_ehraf/` | eHRAF PDFs → markdown → LLM → CSV |
| `code/jr_database/` | Keerthana + LLM + ICMID manual → `output/result/` |
| `data/` | Original / downloadable inputs |
| `output/result/` | Clean deliverables |

See [PIPELINE.md](PIPELINE.md) and [code/jr_database/README.md](code/jr_database/README.md).
