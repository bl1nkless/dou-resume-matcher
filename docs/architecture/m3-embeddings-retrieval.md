# M3 Embeddings And Evidence Retrieval

M3 adds the first reusable semantic matching substrate on top of the M2 rules baseline.

## Included

- 100+ seed skills with aliases for taxonomy experiments
- deterministic 384-dimensional embedding fallback for local tests and CI
- optional sentence-transformers backend when the dependency and model are available
- idempotent embedding backfill for document chunks
- retrieval-backed evidence maps with chunk ids, similarity, skill overlap, confidence, and reasons

## Runtime Behavior

Analysis still completes if semantic retrieval fails. The service falls back to the M2 rules evidence,
stores the analysis result, and keeps recommendation generation grounded in structured evidence.

## Next

The next milestone should compare retrieval quality against labeled evidence examples and then add
LLM-written recommendations only from the evidence package and forbidden-claim list.
