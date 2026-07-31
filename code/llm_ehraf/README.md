# llm_ehraf — joking relationships from eHRAF via LLM

Convert eHRAF PDFs with markitdown, extract institutionalized joking
relationships with a full-document LLM, export CSV.

## Commands

```bash
uv run python -B code/llm_ehraf/run.py convert
uv run python -B code/llm_ehraf/run.py extract --force
uv run python -B code/llm_ehraf/run.py export
# or: uv run python -B code/llm_ehraf/run.py all --force
```

## Outputs (`output/llm_ehraf/`)

| File | Contents |
|------|----------|
| `export/llm_ehraf_joking_relationships.csv` | All scopes (kinship / within_group / cross_group) |
| `export/llm_ehraf_cross_group.csv` | Aggregated cross-group |
| `export/llm_ehraf_within_kin.csv` | Aggregated within + kinship |
| `ehraf_jr_doc.sqlite` | Extraction DB |
| `markdown_raw/`, `markdown_clean/` | Converted documents |

Downstream consolidation: `code/jr_database/` → `output/result/`.
