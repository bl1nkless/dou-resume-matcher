# M2 Rules Baseline

M2 turns the foundation into a single-vacancy analysis workflow.

## Included

- deterministic resume and vacancy skill extraction
- candidate seniority and positioning heuristics
- vacancy seniority, work format, domain, and requirement parsing
- document chunks and extracted skill records during ingestion
- evidence maps, gap reports, score components, verdicts, and baseline recommendations
- lightweight feedback events for later weak-label validation

## Boundaries

The rules baseline is intentionally interpretable and easy to debug. Neural structured extraction,
embeddings, pgvector retrieval, and LLM-written recommendations should augment this baseline rather
than replace its audit trail.
