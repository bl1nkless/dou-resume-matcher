from pathlib import Path
from uuid import UUID

from fastapi import UploadFile
from sqlalchemy.orm import Session

from resume_hunt.db.models import Document

DATA_DIR = Path(__file__).resolve().parents[5] / "data" / "uploads"


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
    document = Document(
        user_id=user_id,
        document_type=document_type,
        source_url=source_url,
        raw_text=normalized,
        language=detect_language(normalized),
        object_storage_uri=object_storage_uri,
    )
    session.add(document)
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
