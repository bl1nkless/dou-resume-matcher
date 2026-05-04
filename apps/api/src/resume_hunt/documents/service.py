from pathlib import Path
from uuid import UUID

from fastapi import UploadFile
from sqlalchemy.orm import Session

from resume_hunt.analyses.extraction import extract_skills, split_sentences
from resume_hunt.db.models import Document, DocumentChunk, ExtractedSkill


def _default_data_dir() -> Path:
    for parent in Path(__file__).resolve().parents:
        if (parent / "pyproject.toml").exists() and (parent / "alembic.ini").exists():
            return parent / "data" / "uploads"
    return Path.cwd() / "data" / "uploads"


DATA_DIR = _default_data_dir()


def normalize_text(text: str) -> str:
    return "\n".join(line.strip() for line in text.replace("\r\n", "\n").splitlines() if line.strip())


def detect_language(text: str) -> str:
    lowered = text.lower()
    cyrillic = sum(1 for char in lowered if "а" <= char <= "я" or char in "іїєґ")
    latin = sum(1 for char in lowered if "a" <= char <= "z")
    ukrainian_markers = sum(lowered.count(marker) for marker in ("ї", "є", "ґ", " та ", "від"))
    russian_markers = sum(lowered.count(marker) for marker in ("ы", "э", "ъ", " и ", "для"))

    if cyrillic and latin and min(cyrillic, latin) / max(cyrillic, latin) > 0.12:
        return "mixed"
    if ukrainian_markers > russian_markers and cyrillic:
        return "uk"
    if russian_markers > ukrainian_markers and cyrillic:
        return "ru"
    if latin:
        return "en"
    return "unknown"


def build_document_parse(document_type: str, text: str, source_url: str | None = None) -> dict:
    chunks = build_document_chunks(document_type, text)
    return {
        "document_type": document_type,
        "language": detect_language(text),
        "source_url": source_url,
        "sections": chunks,
        "skills": [skill.__dict__ for skill in extract_skills(text)],
        "parser_version": "rules-baseline-0.1",
    }


def build_document_chunks(document_type: str, text: str) -> list[dict]:
    sentences = split_sentences(text)
    if not sentences:
        return []

    chunk_type = "resume_chunk" if document_type == "resume" else "vacancy_chunk"
    chunks: list[dict] = []
    current: list[str] = []
    start_index = 0
    cursor = 0
    for sentence in sentences:
        if not current:
            start_index = text.find(sentence, cursor)
        current.append(sentence)
        cursor = max(cursor, text.find(sentence, cursor) + len(sentence))
        joined = " ".join(current)
        if len(joined) >= 260 or len(current) >= 3:
            chunks.append(_chunk_payload(chunk_type, joined, start_index, text))
            current = []
    if current:
        chunks.append(_chunk_payload(chunk_type, " ".join(current), start_index, text))
    return chunks


def _chunk_payload(chunk_type: str, chunk_text: str, start_index: int, full_text: str) -> dict:
    safe_start = max(start_index, 0)
    safe_end = min(safe_start + len(chunk_text), len(full_text))
    return {
        "section_type": chunk_type,
        "chunk_type": chunk_type,
        "text": chunk_text[:1000],
        "start_char": safe_start,
        "end_char": safe_end,
    }


def create_text_document(
    session: Session,
    *,
    user_id: UUID,
    document_type: str,
    text: str,
    source_url: str | None = None,
    object_storage_uri: str | None = None,
) -> Document:
    normalized = normalize_text(text)
    parsed = build_document_parse(document_type, normalized, source_url)
    document = Document(
        user_id=user_id,
        document_type=document_type,
        source_url=source_url,
        raw_text=normalized,
        parsed_json=parsed,
        language=parsed["language"],
        object_storage_uri=object_storage_uri,
    )
    session.add(document)
    session.flush()
    for chunk in parsed["sections"]:
        session.add(
            DocumentChunk(
                document_id=document.id,
                chunk_type=chunk["chunk_type"],
                text=chunk["text"],
                metadata_json={
                    "start_char": chunk["start_char"],
                    "end_char": chunk["end_char"],
                    "parser_version": parsed["parser_version"],
                },
            )
        )
    for skill in parsed["skills"]:
        session.add(
            ExtractedSkill(
                owner_type="document",
                owner_id=document.id,
                skill_id=None,
                raw_mention=skill["raw_mention"],
                evidence_text=skill["evidence_text"],
                confidence=skill["confidence"],
                extraction_method="rules-baseline",
            )
        )
    session.commit()
    session.refresh(document)
    return document


async def persist_uploaded_file(user_id: UUID, upload: UploadFile) -> tuple[str, str]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    safe_name = Path(upload.filename or "resume.txt").name
    target = DATA_DIR / str(user_id) / safe_name
    target.parent.mkdir(parents=True, exist_ok=True)
    content = await upload.read()
    target.write_bytes(content)

    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        text = content.decode("utf-8", errors="ignore")

    return f"local://uploads/{user_id}/{safe_name}", text
