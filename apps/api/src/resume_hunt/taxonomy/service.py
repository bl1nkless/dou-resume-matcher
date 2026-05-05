import json
import string
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from resume_hunt.db.models import SkillTaxonomy


def default_taxonomy_path() -> Path:
    for parent in Path(__file__).resolve().parents:
        candidate = parent / "ml" / "taxonomy" / "skill_taxonomy_seed.json"
        if candidate.exists():
            return candidate
    return Path.cwd() / "ml" / "taxonomy" / "skill_taxonomy_seed.json"


def load_taxonomy_seed(path: Path | None = None) -> list[dict[str, Any]]:
    seed_path = path or default_taxonomy_path()
    return json.loads(seed_path.read_text(encoding="utf-8"))


def seed_skill_taxonomy(session: Session, *, path: Path | None = None) -> dict[str, int]:
    rows = load_taxonomy_seed(path)
    created = 0
    updated = 0
    for row in rows:
        canonical_name = row["canonical_name"]
        existing = session.scalar(
            select(SkillTaxonomy).where(SkillTaxonomy.canonical_name == canonical_name)
        )
        aliases = _unique_aliases([canonical_name, *row.get("aliases", [])])
        if existing is None:
            session.add(
                SkillTaxonomy(
                    canonical_name=canonical_name,
                    category=row.get("category"),
                    aliases=aliases,
                    metadata_json={"seed_source": "m3_seed"},
                )
            )
            created += 1
            continue
        existing.category = row.get("category")
        existing.aliases = aliases
        existing.metadata_json = {**(existing.metadata_json or {}), "seed_source": "m3_seed"}
        updated += 1
    session.commit()
    return {"created": created, "updated": updated, "total": len(rows)}


def normalize_skill_name(session: Session, mention: str) -> str | None:
    normalized = normalize_alias(mention)
    for skill in session.scalars(select(SkillTaxonomy)):
        aliases = [skill.canonical_name, *(skill.aliases or [])]
        if normalized in {normalize_alias(alias) for alias in aliases}:
            return skill.canonical_name
    return None


def normalize_alias(value: str) -> str:
    table = str.maketrans({char: " " for char in string.punctuation if char not in {"+", "#"}})
    return " ".join(value.lower().translate(table).split())


def _unique_aliases(values: list[str]) -> list[str]:
    seen: set[str] = set()
    unique: list[str] = []
    for value in values:
        normalized = normalize_alias(value)
        if normalized in seen:
            continue
        seen.add(normalized)
        unique.append(value)
    return unique
