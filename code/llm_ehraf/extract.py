"""LLM extraction: full cleaned markdown → joking relationships in SQLite."""
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jsonschema import validate as jsonschema_validate
from tqdm import tqdm

_V2_ROOT = Path(__file__).resolve().parent
_CODE_ROOT = _V2_ROOT.parent
_PIPELINE_ROOT = _CODE_ROOT.parent
for _p in (_CODE_ROOT, _PIPELINE_ROOT):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from pipeline_config import (  # noqa: E402
    append_jsonl,
    create_chat_completion,
    effective_max_output_tokens,
    get_openai_client,
    llm_error_signature,
    message_content_from_response,
    parse_llm_json_content,
    reasoning_effort_for_model,
    same_llm_error_twice,
)
from llm_ehraf.config import (  # noqa: E402
    EXTRACT_MAX_TOKENS,
    LLM_TEMPERATURE,
    MAX_DOC_CHARS,
    MAX_LLM_RETRIES,
    MODEL_EXTRACT,
    ensure_dirs,
)
from llm_ehraf.db import connect_db
from llm_ehraf.prompts import EXTRACT_RESPONSE_SCHEMA, EXTRACT_SYSTEM, EXTRACT_USER_TMPL
from llm_ehraf.markdown import truncate_for_llm


def _call_extract(client, *, doc_id: str, ethno: str, region: str, document_text: str) -> dict[str, Any]:
    messages = [
        {"role": "system", "content": EXTRACT_SYSTEM},
        {
            "role": "user",
            "content": EXTRACT_USER_TMPL.format(
                doc_id=doc_id,
                ethnography_group_name=ethno,
                region=region,
                document_text=document_text,
            ),
        },
    ]
    schema = EXTRACT_RESPONSE_SCHEMA
    max_tokens = effective_max_output_tokens(MODEL_EXTRACT, EXTRACT_MAX_TOKENS, stage="extract")
    reasoning = reasoning_effort_for_model(MODEL_EXTRACT, "extract")

    prev_err: str | None = None
    for attempt in range(1, MAX_LLM_RETRIES + 1):
        try:
            resp = create_chat_completion(
                client,
                model=MODEL_EXTRACT,
                messages=messages,
                response_format={"type": "json_schema", "json_schema": schema},
                max_output_tokens=max_tokens,
                reasoning_effort=reasoning,
                temperature=LLM_TEMPERATURE,
            )
            content, finish_reason, refusal = message_content_from_response(resp)
            if refusal:
                raise ValueError(f"model refusal: {refusal}")
            if finish_reason == "length":
                raise ValueError("finish_reason=length — raise EXTRACT_MAX_TOKENS_V2")
            data = parse_llm_json_content(content)
            jsonschema_validate(instance=data, schema=schema["schema"])
            return data
        except Exception as exc:
            if same_llm_error_twice(prev_err, exc):
                raise
            prev_err = llm_error_signature(exc)
            if attempt == MAX_LLM_RETRIES:
                raise
            time.sleep(min(2 ** attempt, 30))
    raise RuntimeError("unreachable")


def run_extract(
    *,
    db_path: Path,
    force: bool = False,
    doc_id: str | None = None,
    region: str | None = None,
    group: str | None = None,
    limit: int | None = None,
    dry_run: bool = False,
) -> None:
    paths = ensure_dirs()
    con = connect_db(db_path)
    client = None if dry_run else get_openai_client()

    query = """
        SELECT doc_id, filename, region, ethnography_group_name, md_clean_path
        FROM document
        WHERE md_clean_path IS NOT NULL
    """
    params: list[Any] = []
    if doc_id:
        query += " AND doc_id = ?"
        params.append(doc_id)
    if region:
        query += " AND region = ?"
        params.append(region)
    if group:
        query += " AND ethnography_group_name = ? COLLATE NOCASE"
        params.append(group)
    query += " ORDER BY doc_id"

    rows = con.execute(query, params).fetchall()
    if not rows:
        print("No converted documents found. Run convert first.")
        con.close()
        return

    extracted_docs = {
        r["doc_id"]
        for r in con.execute(
            "SELECT doc_id FROM document WHERE extracted_at IS NOT NULL"
        )
    }

    if limit is not None:
        rows = rows[:limit]

    print(f"Model: {MODEL_EXTRACT}")
    print(f"Documents to consider: {len(rows)}")

    processed = 0
    total_relationships = 0
    for row in tqdm(rows, desc="Extract JR"):
        did = row["doc_id"]
        if did in extracted_docs and not force:
            continue

        md_path = Path(row["md_clean_path"])
        if not md_path.is_file():
            print(f"Missing markdown for {did}: {md_path}")
            continue

        text = md_path.read_text(encoding="utf-8")
        llm_text, truncated = truncate_for_llm(text, MAX_DOC_CHARS)

        if dry_run:
            print(f"[dry-run] {did}: {len(text)} chars ({'truncated' if truncated else 'full'})")
            processed += 1
            continue

        assert client is not None
        try:
            data = _call_extract(
                client,
                doc_id=did,
                ethno=row["ethnography_group_name"],
                region=row["region"],
                document_text=llm_text,
            )
        except Exception as exc:
            append_jsonl(
                paths.logs / "llm_errors.jsonl",
                {
                    "doc_id": did,
                    "region": row["region"],
                    "stage": "extract",
                    "error": str(exc),
                },
            )
            print(f"ERROR {did}: {exc}")
            continue

        now = datetime.now(timezone.utc).isoformat()
        warnings = data.get("warnings") or []
        relationships = data.get("relationships") or []

        con.execute("DELETE FROM joking_relationship WHERE doc_id = ?", (did,))
        for rel in relationships:
            con.execute(
                """
                INSERT INTO joking_relationship (
                  doc_id, region, ethnography_group_name,
                  entity_a_raw, entity_a_type, entity_b_raw, entity_b_type,
                  scope_coded, reasoning, supporting_quote_raw,
                  relation_label_raw, local_term_raw,
                  symmetry_coded, relation_type_coded, confidence, notes,
                  extracted_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    did,
                    row["region"],
                    row["ethnography_group_name"],
                    rel["entity_a_raw"],
                    rel["entity_a_type"],
                    rel["entity_b_raw"],
                    rel["entity_b_type"],
                    rel["scope_coded"],
                    rel.get("reasoning", ""),
                    rel.get("supporting_quote_raw", ""),
                    rel.get("relation_label_raw", ""),
                    rel.get("local_term_raw", ""),
                    rel.get("symmetry_coded", "unclear"),
                    rel.get("relation_type_coded", "joking_relationship"),
                    float(rel.get("confidence", 0.0)),
                    rel.get("notes", ""),
                    now,
                ),
            )

        con.execute(
            """
            UPDATE document
            SET extracted_at = ?, extract_model = ?, extract_warnings = ?, truncated = ?
            WHERE doc_id = ?
            """,
            (now, MODEL_EXTRACT, json.dumps(warnings, ensure_ascii=False), int(truncated), did),
        )
        con.commit()
        processed += 1
        total_relationships += len(relationships)

    con.close()
    print(f"Extracted from {processed} documents ({total_relationships} relationship rows)")


def main() -> None:
    paths = ensure_dirs()
    parser = argparse.ArgumentParser(description="LLM extract joking relationships (full doc)")
    parser.add_argument("--db", type=Path, default=paths.jr_sqlite)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--doc-id", type=str, default=None)
    parser.add_argument("--region", type=str, default=None)
    parser.add_argument("--group", type=str, default=None, help="Ethnography group, e.g. Hausa")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    run_extract(
        db_path=args.db,
        force=args.force,
        doc_id=args.doc_id,
        region=args.region,
        group=args.group,
        limit=args.limit,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
