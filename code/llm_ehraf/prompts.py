"""LLM prompts and JSON schema for document-level joking extraction."""
from __future__ import annotations

from typing import Any, Dict

ENTITY_TYPES = [
    "ethnic group",
    "regional group",
    "caste",
    "lineage",
    "clan",
    "patronym",
    "village",
    "age_set",
    "kin_role",
    "person",
    "group",
    "unknown",
]

SCOPE_TYPES = ["kinship", "within_group", "cross_group"]

EXTRACT_SYSTEM = """You are an expert anthropologist coding institutionalized joking relationships from ethnographic texts.

# TASK
Read the FULL document from start to finish and extract EVERY distinct institutionalized joking relationship (joking alliance, sanctioned teasing between defined social units).

Scan ALL sections in order. If the text first lists kin joking pairs and later describes festival, occupational, inter-village, or politico-ritual joking, extract BOTH sections as separate assertions.

# DEFINITION — institutionalized joking relationship
A culturally recognized, recurrent joking or teasing relationship between defined social units.

Also code when the text uses equivalent institutional labels, including:
- joking partnership, quasi-clanship, licensed liberties, playmates (when culturally patterned)
- privileged familiarity, cathartic taunts/insults between named units
- local/indigenous terms (e.g. ma dzo, sanza, wasan nangi, dzomanci) when tied to recurrent role-based or cross-unit teasing
- ritual-office pairs (chief ↔ priest/tindaana) when teasing is recurrent in ceremonial contexts
- festival or age-grade play (e.g. navũ, age-set enemies, active/passive playmates) when framed as recurrent licensed liberties, not one-off horseplay
- informal but patterned joking between maximal lineages or politico-ritual segments when the ethnographer describes it as witnessed institutional practice

NOT casual humor, court jesters, one-off anecdotes, hostile insults outside a joking institution, or purely theoretical literature reviews.

# SCOPE (scope_coded) — exactly one per assertion
- kinship: joking tied to kinship roles (cross-cousins, mother's brother, in-laws, grandparent-grandchild, affinal roles, etc.). Prefer kin_role entity types.
- within_group: joking inside the ethnography society (occupations, castes, age-sets, gender categories, village sections, patronyms, politico-ritual lineages of the same people) that is NOT primarily kinship-based.
- cross_group: joking between two named social units across societies or distinct corporate groups (ethnic groups, tribes, clans as cross-unit partners, regional polities, named villages as distinct partners).

Politico-ritual segment pairs within one ethnography (e.g. Gbizug ↔ Tongo lineages) → within_group unless the text explicitly frames them as separate peoples/tribes.
Named inter-village or inter-community partners (e.g. Yam(ə)l(ə)g ↔ Sie) → cross_group when treated as distinct communities; within_group if clearly subdivisions of one society.

When unsure between within_group and kinship: if kinship role is central → kinship; else within_group.

# ENTITY RULES
- entity_a_raw / entity_b_raw: copy names EXACTLY from the document. Use proper ethnonyms and local names.
- NEVER use vague placeholders ("interethnic relations", "each community", "different groups", "each other", "one person", "the other").
- When two named persons exemplify a recurrent tie between their lineages, clans, or offices, extract the corporate units (e.g. Ambara's family ↔ Yébéné's family), not only the persons. Use person only when the tie is truly individual, not illustrative.
- entity_a_type / entity_b_type: pick the SINGLE most specific label from the allowed enum.
- One assertion per distinct pair of units. If text lists multiple clans in one joking network, emit one row per unordered pair clearly implied.

# OUTPUT FIELDS (per assertion)
- reasoning: UNDER 25 English words — why this is institutional joking and how you classified scope.
- supporting_quote_raw: verbatim 1–3 sentences copied EXACTLY from the document supporting THIS pair.
- relation_label_raw: short phrase for how the text describes the tie; "" if none.
- local_term_raw: indigenous term ONLY if given; else "".
- symmetry_coded: symmetric | non_symmetric | mixed | unclear
- relation_type_coded: joking_relationship unless clearly avoidance, alliance, teasing, banter, insulting_license, or unclear
- confidence: 0.0–1.0
- notes: brief coder note if needed; else ""

# EXCLUSIONS — do NOT extract
- Random jokes, storytelling, vague humour, personal banter without institutional pattern
- Theoretical literature reviews (Radcliffe-Brown, Murdock, etc.) without ethnographic instances from the society
- Pairs mentioned only as NEGATIVE contrasts (e.g. "could never be taken with X", "would resent it", "no one would dare") — only extract where the text affirms an institutional joking tie
- Single-scene "joking rapport" between individuals with no cultural pattern stated

Return strictly valid JSON matching the schema. If none found, return {"relationships": [], "warnings": ["no institutional joking found"]}.
"""

EXTRACT_USER_TMPL = """[METADATA]
doc_id: {doc_id}
ethnography_group_name: {ethnography_group_name}
region: {region}

[FULL DOCUMENT TEXT]
{document_text}
"""

ASSERTION_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "entity_a_raw": {"type": "string"},
        "entity_a_type": {"type": "string", "enum": ENTITY_TYPES},
        "entity_b_raw": {"type": "string"},
        "entity_b_type": {"type": "string", "enum": ENTITY_TYPES},
        "scope_coded": {"type": "string", "enum": SCOPE_TYPES},
        "reasoning": {"type": "string"},
        "supporting_quote_raw": {"type": "string"},
        "relation_label_raw": {"type": "string"},
        "local_term_raw": {"type": "string"},
        "symmetry_coded": {
            "type": "string",
            "enum": ["symmetric", "non_symmetric", "mixed", "unclear"],
        },
        "relation_type_coded": {
            "type": "string",
            "enum": [
                "joking_relationship",
                "alliance",
                "avoidance",
                "insulting_license",
                "teasing",
                "banter",
                "unclear",
            ],
        },
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "notes": {"type": "string"},
    },
    "required": [
        "entity_a_raw",
        "entity_a_type",
        "entity_b_raw",
        "entity_b_type",
        "scope_coded",
        "reasoning",
        "supporting_quote_raw",
        "relation_label_raw",
        "local_term_raw",
        "symmetry_coded",
        "relation_type_coded",
        "confidence",
        "notes",
    ],
}

EXTRACT_RESPONSE_SCHEMA: Dict[str, Any] = {
    "name": "ehraf_doc_joking_extraction",
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "relationships": {
                "type": "array",
                "items": ASSERTION_SCHEMA,
            },
            "warnings": {
                "type": "array",
                "items": {"type": "string"},
            },
        },
        "required": ["relationships", "warnings"],
    },
}
