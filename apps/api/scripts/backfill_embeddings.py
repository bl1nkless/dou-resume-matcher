import argparse

from resume_hunt.db.session import SessionLocal
from resume_hunt.ml_gateway.embeddings import backfill_embeddings


def main() -> None:
    parser = argparse.ArgumentParser(description="Backfill document chunk embeddings.")
    parser.add_argument("--model", dest="model_name", default=None)
    parser.add_argument(
        "--document-type",
        default="all",
        choices=["all", "resume", "vacancy", "company_profile"],
    )
    parser.add_argument(
        "--backend",
        default=None,
        choices=["auto", "sentence_transformers", "deterministic"],
    )
    args = parser.parse_args()

    with SessionLocal() as session:
        result = backfill_embeddings(
            session,
            model_name=args.model_name,
            document_type=args.document_type,
            backend=args.backend,
        )
    print(
        "backfilled embeddings "
        f"backend={result['backend']} model={result['embedding_model']} "
        f"created={result['created']} skipped={result['skipped']}"
    )


if __name__ == "__main__":
    main()
