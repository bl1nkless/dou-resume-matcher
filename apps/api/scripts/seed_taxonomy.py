from resume_hunt.db.session import SessionLocal
from resume_hunt.taxonomy.service import seed_skill_taxonomy


def main() -> None:
    with SessionLocal() as session:
        result = seed_skill_taxonomy(session)
    print(
        "seeded taxonomy "
        f"created={result['created']} updated={result['updated']} total={result['total']}"
    )


if __name__ == "__main__":
    main()
