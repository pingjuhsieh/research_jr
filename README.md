# ICMID PingJu — joking relationship research

Python **3.12+** ([uv](https://docs.astral.sh/uv/)). Stata / R for settlement & climate.

## Quick start

```bash
uv sync
cp .env.example .env   # OPENAI_API_KEY

# 1) LLM from eHRAF (if rebuilding extraction)
uv run python -B code/llm_ehraf/run.py all

# 2) JR database (pairs + map)
bash code/jr_database/scripts/run.sh
```

Deliverables: **`output/jr_database/`**
(map: `output/jr_database/jr_map.html`)

---

## Layout

```
ICMID PingJu/
├── code/
│   ├── llm_ehraf/       # PDF → LLM extraction (eHRAF)
│   ├── jr_database/     # Merge sources → database + map
│   ├── visualization/   # Map builder (outputs → jr_database/)
│   ├── settlement/
│   └── climate/
├── data/                # RAW inputs only (PDFs, GIS, original tables)
├── output/
│   ├── llm_ehraf/       # LLM intermediates
│   └── jr_database/     # All JR database products (tables + map)
├── literature/
└── PIPELINE.md
```

| Path | Role |
|------|------|
| `code/llm_ehraf/` | eHRAF PDFs → markdown → LLM → CSV |
| `code/jr_database/` | Keerthana + LLM + ICMID → `output/jr_database/` |
| `data/` | Original / downloadable inputs |
| `output/jr_database/` | Clean deliverables + interactive map |

See [PIPELINE.md](PIPELINE.md) and [code/jr_database/README.md](code/jr_database/README.md).
