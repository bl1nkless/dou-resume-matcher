from urllib.parse import urlparse
from uuid import UUID

import httpx
from bs4 import BeautifulSoup
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from resume_hunt.analyses.extraction import parse_vacancy
from resume_hunt.db.models import Company, Job
from resume_hunt.documents.service import create_text_document, normalize_text


def infer_title(text: str, explicit_title: str | None = None) -> str:
    if explicit_title:
        return explicit_title.strip()
    for line in text.splitlines():
        clean = line.strip()
        if 4 <= len(clean) <= 120:
            return clean
    return "Untitled DOU vacancy"


def infer_company(explicit_company: str | None = None) -> str:
    return explicit_company.strip() if explicit_company else "Unknown company"


def create_job_from_text(
    session: Session,
    *,
    user_id: UUID,
    text: str,
    title: str | None = None,
    company_name: str | None = None,
    source_url: str | None = None,
    source: str = "manual_text",
) -> Job:
    normalized = normalize_text(text)
    document = create_text_document(
        session,
        user_id=user_id,
        document_type="vacancy",
        text=normalized,
        source_url=source_url,
    )
    company = Company(name=infer_company(company_name), source_url=source_url)
    session.add(company)
    session.flush()

    job_title = infer_title(normalized, title)
    extracted = parse_vacancy(normalized, job_title)
    job = Job(
        company_id=company.id,
        source=source,
        source_url=source_url,
        title=job_title,
        seniority=extracted["seniority"],
        domain=extracted["domain"],
        work_format=extracted["work_format"],
        language_requirements={"items": extracted["language_requirements"]},
        raw_document_id=document.id,
        extracted_json={
            "source": "m1_ingestion",
            "extraction_status": "m2_rules_baseline",
            "company": company.name,
            "raw_text_preview": normalized[:600],
            **extracted,
        },
    )
    session.add(job)
    session.commit()
    session.refresh(job)
    return job


async def fetch_vacancy_url(url: str) -> tuple[str, str, str | None]:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="URL must be HTTP(S)")

    async with httpx.AsyncClient(
        headers={"User-Agent": "resume-hunt-mvp/0.1 (+local user-submitted URL)"},
        timeout=15,
        follow_redirects=True,
    ) as client:
        try:
            response = await client.get(url)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Could not fetch vacancy URL. Paste vacancy text instead.",
            ) from exc

    soup = BeautifulSoup(response.text, "html.parser")
    title = soup.find("h1")
    title_text = title.get_text(" ", strip=True) if title else (soup.title.string if soup.title else None)
    content_node = soup.find(class_="vacancy-section") or soup.find("main") or soup.body
    content = content_node.get_text("\n", strip=True) if content_node else soup.get_text("\n", strip=True)
    if len(content) < 40:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Fetched page did not contain enough text. Paste vacancy text instead.",
        )
    return content, title_text or "DOU vacancy", response.url.human_repr()
