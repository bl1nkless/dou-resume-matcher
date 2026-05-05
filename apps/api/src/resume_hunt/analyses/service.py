from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from resume_hunt.analyses.extraction import TRANSFERABLE_SKILLS, seniority_distance
from resume_hunt.analyses.retrieval import build_retrieved_evidence
from resume_hunt.db.models import (
    AnalysisRun,
    CandidateProfile,
    Document,
    EvidenceMap,
    GapReport,
    Job,
    Recommendation,
    UserFeedbackEvent,
)

MODEL_VERSION = "m3-retrieval-baseline-0.1"


def create_analysis_run(
    session: Session,
    *,
    user_id: UUID,
    candidate_profile_id: UUID,
    job_id: UUID,
) -> AnalysisRun:
    profile = session.get(CandidateProfile, candidate_profile_id)
    if profile is None or profile.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate profile not found")

    job = session.get(Job, job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    if not _user_owns_job(session, job, user_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    analysis = AnalysisRun(
        user_id=user_id,
        candidate_profile_id=profile.id,
        job_id=job.id,
        status="running",
        model_version=MODEL_VERSION,
    )
    session.add(analysis)
    session.flush()

    evidence_rows, gap_rows, features, scores, verdict = _run_rules_baseline(
        session, analysis.id, profile, job
    )
    session.add_all(evidence_rows)
    session.add_all(gap_rows)
    session.add_all(_build_recommendations(analysis.id, profile, job, evidence_rows, gap_rows, verdict))

    analysis.status = "completed"
    analysis.completed_at = datetime.now(timezone.utc)
    analysis.feature_json = features
    analysis.score_json = scores
    analysis.verdict = verdict
    session.commit()
    session.refresh(analysis)
    return analysis


def get_analysis_report(session: Session, *, user_id: UUID, analysis_id: UUID) -> dict:
    analysis = session.get(AnalysisRun, analysis_id)
    if analysis is None or analysis.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis run not found")
    return {
        **analysis.__dict__,
        "evidence": list(
            session.scalars(select(EvidenceMap).where(EvidenceMap.analysis_run_id == analysis.id))
        ),
        "gaps": list(session.scalars(select(GapReport).where(GapReport.analysis_run_id == analysis.id))),
        "recommendations": list(
            session.scalars(select(Recommendation).where(Recommendation.analysis_run_id == analysis.id))
        ),
    }


def get_analysis(session: Session, *, user_id: UUID, analysis_id: UUID) -> AnalysisRun:
    analysis = session.get(AnalysisRun, analysis_id)
    if analysis is None or analysis.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis run not found")
    return analysis


def list_evidence(session: Session, *, user_id: UUID, analysis_id: UUID) -> list[EvidenceMap]:
    analysis = get_analysis(session, user_id=user_id, analysis_id=analysis_id)
    return list(session.scalars(select(EvidenceMap).where(EvidenceMap.analysis_run_id == analysis.id)))


def list_gaps(session: Session, *, user_id: UUID, analysis_id: UUID) -> list[GapReport]:
    analysis = get_analysis(session, user_id=user_id, analysis_id=analysis_id)
    return list(session.scalars(select(GapReport).where(GapReport.analysis_run_id == analysis.id)))


def list_recommendations(session: Session, *, user_id: UUID, analysis_id: UUID) -> list[Recommendation]:
    analysis = get_analysis(session, user_id=user_id, analysis_id=analysis_id)
    return list(session.scalars(select(Recommendation).where(Recommendation.analysis_run_id == analysis.id)))


def create_feedback_event(
    session: Session,
    *,
    user_id: UUID,
    analysis_id: UUID,
    event_type: str,
    event_value: dict,
) -> UserFeedbackEvent:
    analysis = get_analysis(session, user_id=user_id, analysis_id=analysis_id)
    feedback = UserFeedbackEvent(
        user_id=user_id,
        analysis_run_id=analysis.id,
        event_type=event_type,
        event_value={
            **event_value,
            "analysis_verdict": analysis.verdict,
            "analysis_model_version": analysis.model_version,
        },
    )
    session.add(feedback)
    session.commit()
    session.refresh(feedback)
    return feedback


def _user_owns_job(session: Session, job: Job, user_id: UUID) -> bool:
    if job.raw_document_id is None:
        return False
    document = session.get(Document, job.raw_document_id)
    return document is not None and document.user_id == user_id


def _run_rules_baseline(
    session: Session,
    analysis_id: UUID,
    profile: CandidateProfile,
    job: Job,
) -> tuple[list[EvidenceMap], list[GapReport], dict, dict, str]:
    candidate_skills = {
        item["canonical_name"]: item
        for item in profile.profile_json.get("skills", [])
        if "canonical_name" in item
    }
    requirements = job.extracted_json.get("raw_requirements", [])
    if not requirements:
        requirements = [
            {
                "text": skill_name,
                "requirement_type": "technical_skill",
                "priority": "required",
                "normalized_skill": skill_name,
            }
            for skill_name in job.extracted_json.get("required_skills", [])
        ]

    evidence_rows: list[EvidenceMap] = []
    gap_rows: list[GapReport] = []
    required_count = 0
    preferred_count = 0
    direct_required = 0
    direct_preferred = 0
    transferable_count = 0
    weak_count = 0
    missing_required = 0
    embedding_meta: dict[str, int | str] = {
        "backend": "rules_only",
        "embedding_model": "",
        "created": 0,
        "skipped": 0,
    }
    resume_document_id = profile.profile_json.get("resume_document_id")
    vacancy_document_id = str(job.raw_document_id) if job.raw_document_id else None

    for requirement in requirements:
        priority = requirement.get("priority", "required")
        skill_name = requirement.get("normalized_skill") or requirement.get("text")
        if priority == "required":
            required_count += 1
        else:
            preferred_count += 1

        retrieved_items: list[dict] = []
        retrieved_level: str | None = None
        retrieved_confidence: float | None = None
        if resume_document_id and vacancy_document_id:
            try:
                retrieved, embedding_meta = build_retrieved_evidence(
                    session,
                    resume_document_id=UUID(resume_document_id),
                    vacancy_document_id=UUID(vacancy_document_id),
                    requirement_text=requirement.get("text", skill_name),
                    normalized_skill=skill_name,
                    candidate_skills=candidate_skills,
                )
                retrieved_items = [
                    {
                        "chunk_id": str(item.chunk_id),
                        "chunk": item.chunk,
                        "similarity": item.similarity,
                        "evidence_type": item.evidence_type,
                        "skill_overlap": item.skill_overlap,
                        "reason": item.reason,
                    }
                    for item in retrieved
                    if item.evidence_type != "missing"
                ]
                if retrieved:
                    top = retrieved[0]
                    retrieved_level = top.evidence_type
                    retrieved_confidence = top.confidence
            except Exception:
                retrieved_items = []

        candidate_skill = candidate_skills.get(skill_name)
        transferable_skill = _find_transferable_skill(skill_name, candidate_skills)
        if retrieved_level == "direct" or candidate_skill:
            evidence_level = "direct"
            confidence = max(0.9 if candidate_skill else 0.0, retrieved_confidence or 0.0)
            if priority == "required":
                direct_required += 1
            else:
                direct_preferred += 1
            evidence_chunks = {
                "items": retrieved_items
                or [
                    {
                        "chunk": candidate_skill.get("evidence_text"),
                        "evidence_type": "direct",
                        "skill": skill_name,
                        "reason": f"CV explicitly mentions {skill_name}.",
                    }
                ]
            }
        elif retrieved_level == "transferable" or transferable_skill:
            evidence_level = "transferable"
            confidence = max(0.68 if transferable_skill else 0.0, retrieved_confidence or 0.0)
            transferable_count += 1
            evidence_chunks = {
                "items": retrieved_items
                or [
                    {
                        "chunk": transferable_skill.get("evidence_text"),
                        "evidence_type": "transferable",
                        "skill": transferable_skill.get("canonical_name"),
                        "reason": f"{transferable_skill.get('canonical_name')} partially transfers to {skill_name}.",
                    }
                ]
            }
            if transferable_skill:
                gap_rows.append(_gap_for_transferable(analysis_id, skill_name, transferable_skill, priority))
            else:
                gap_rows.append(_gap_for_weak_retrieval(analysis_id, skill_name, priority))
        elif retrieved_level == "weak":
            evidence_level = "weak"
            confidence = retrieved_confidence or 0.45
            weak_count += 1
            evidence_chunks = {"items": retrieved_items}
            gap_rows.append(_gap_for_weak_retrieval(analysis_id, skill_name, priority))
        else:
            evidence_level = "missing"
            confidence = 0.35
            evidence_chunks = {"items": retrieved_items}
            if priority == "required":
                missing_required += 1
            gap_rows.append(_gap_for_missing(analysis_id, skill_name, priority))

        evidence_rows.append(
            EvidenceMap(
                analysis_run_id=analysis_id,
                requirement_text=requirement.get("text", skill_name),
                requirement_type=requirement.get("requirement_type"),
                requirement_priority=priority,
                evidence_chunks=evidence_chunks,
                evidence_level=evidence_level,
                confidence=confidence,
            )
        )

    required_denominator = max(required_count, 1)
    preferred_denominator = max(preferred_count, 1)
    seniority_gap = seniority_distance(profile.estimated_seniority, job.seniority)
    skill_match = (direct_required + 0.5 * transferable_count + 0.25 * weak_count) / required_denominator
    preferred_match = direct_preferred / preferred_denominator if preferred_count else 0.0
    evidence_score = (direct_required + 0.65 * transferable_count + 0.35 * weak_count) / required_denominator
    seniority_score = max(0.0, 1.0 - max(seniority_gap, 0) * 0.28)
    gap_score = max(0.0, 1.0 - missing_required / required_denominator)
    interview_readiness = min(1.0, evidence_score * 0.85 + preferred_match * 0.15)
    semantic_match = min(1.0, skill_match * 0.78 + preferred_match * 0.22)
    domain_score = 0.65 if job.domain else 0.5

    overall = (
        0.22 * skill_match
        + 0.18 * semantic_match
        + 0.20 * evidence_score
        + 0.15 * seniority_score
        + 0.10 * domain_score
        + 0.10 * gap_score
        + 0.05 * interview_readiness
    )
    has_hard_seniority_gap = seniority_gap >= 3
    verdict = _verdict(overall, missing_required, has_hard_seniority_gap)
    features = {
        "skill_match_required_ratio": round(skill_match, 4),
        "skill_match_preferred_ratio": round(preferred_match, 4),
        "direct_evidence_ratio": round(direct_required / required_denominator, 4),
        "transferable_evidence_ratio": round(transferable_count / required_denominator, 4),
        "weak_evidence_ratio": round(weak_count / required_denominator, 4),
        "missing_required_skill_count": missing_required,
        "seniority_distance": seniority_gap,
        "domain_similarity_score": domain_score,
        "interview_readiness_score": round(interview_readiness, 4),
        "embedding_backend": embedding_meta["backend"],
        "embedding_model": embedding_meta["embedding_model"],
        "embeddings_created": embedding_meta["created"],
        "embeddings_skipped": embedding_meta["skipped"],
    }
    scores = {
        "overall_score": round(overall, 4),
        "skill_match_score": round(skill_match, 4),
        "semantic_match_score": round(semantic_match, 4),
        "experience_evidence_score": round(evidence_score, 4),
        "seniority_match_score": round(seniority_score, 4),
        "company_domain_score": domain_score,
        "gap_severity_score": round(gap_score, 4),
        "interview_readiness_score": round(interview_readiness, 4),
    }
    return evidence_rows, gap_rows, features, scores, verdict


def _find_transferable_skill(skill_name: str, candidate_skills: dict[str, dict]) -> dict | None:
    for related in TRANSFERABLE_SKILLS.get(skill_name, set()):
        if related in candidate_skills:
            return candidate_skills[related]
    return None


def _gap_for_transferable(
    analysis_id: UUID,
    skill_name: str,
    transferable_skill: dict,
    priority: str,
) -> GapReport:
    return GapReport(
        analysis_run_id=analysis_id,
        gap_text=skill_name,
        gap_type="soft_gap" if priority == "required" else "learning_gap",
        severity=0.45 if priority == "required" else 0.25,
        reason=f"No direct {skill_name} evidence, but {transferable_skill.get('canonical_name')} is relevant.",
        recommended_action=f"Position the transferable {transferable_skill.get('canonical_name')} evidence honestly.",
    )


def _gap_for_weak_retrieval(analysis_id: UUID, skill_name: str, priority: str) -> GapReport:
    return GapReport(
        analysis_run_id=analysis_id,
        gap_text=skill_name,
        gap_type="keyword_gap" if priority == "required" else "learning_gap",
        severity=0.4 if priority == "required" else 0.2,
        reason=f"Retrieved CV evidence is related to {skill_name}, but direct proof is weak.",
        recommended_action=f"Clarify honest evidence for {skill_name} if it exists; otherwise keep it as a gap.",
    )


def _gap_for_missing(analysis_id: UUID, skill_name: str, priority: str) -> GapReport:
    fake_risk_skills = {"AWS", "Kubernetes", "CI/CD"}
    if priority == "preferred":
        gap_type = "learning_gap"
        severity = 0.25
        action = f"Treat {skill_name} as a learning target before similar applications."
    elif skill_name in fake_risk_skills:
        gap_type = "fake_risk_gap"
        severity = 0.85
        action = f"Do not claim {skill_name} unless you have real project or production evidence."
    else:
        gap_type = "critical_gap"
        severity = 0.75
        action = f"Apply only if you can add honest evidence for {skill_name} or the role accepts learning."
    return GapReport(
        analysis_run_id=analysis_id,
        gap_text=skill_name,
        gap_type=gap_type,
        severity=severity,
        reason=f"{skill_name} is listed as a {priority} requirement and was not found in CV evidence.",
        recommended_action=action,
    )


def _verdict(score: float, missing_required: int, hard_seniority_gap: bool) -> str:
    if hard_seniority_gap or (score < 0.4 and missing_required > 0):
        return "skip"
    if score >= 0.82 and missing_required == 0:
        return "apply_now"
    if score >= 0.68 and missing_required <= 1:
        return "tailor_first"
    if score >= 0.55:
        return "realistic_stretch"
    if score >= 0.40:
        return "learning_target"
    return "skip"


def _build_recommendations(
    analysis_id: UUID,
    profile: CandidateProfile,
    job: Job,
    evidence_rows: list[EvidenceMap],
    gap_rows: list[GapReport],
    verdict: str,
) -> list[Recommendation]:
    direct = [
        row.requirement_text
        for row in evidence_rows
        if row.evidence_level == "direct" and row.requirement_priority == "required"
    ]
    transferable = [row.requirement_text for row in evidence_rows if row.evidence_level == "transferable"]
    forbidden = [gap.gap_text for gap in gap_rows if gap.gap_type == "fake_risk_gap"]
    return [
        Recommendation(
            analysis_run_id=analysis_id,
            recommendation_type="cv_actions",
            content_json={
                "verdict": verdict,
                "candidate_positioning": profile.positioning,
                "job_title": job.title,
                "direct_evidence_to_emphasize": direct[:6],
                "transferable_evidence_to_explain": transferable[:4],
                "forbidden_claims": forbidden,
                "actions": _cv_actions(direct, transferable, gap_rows),
            },
            llm_model=None,
            prompt_version="rules-baseline",
            guardrail_status="no_llm_no_unsupported_claims",
        ),
        Recommendation(
            analysis_run_id=analysis_id,
            recommendation_type="interview_battlecard",
            content_json={
                "focus_topics": direct[:5] + transferable[:3],
                "gap_topics": [gap.gap_text for gap in gap_rows[:5]],
                "prep_plan": _prep_plan(direct, transferable, gap_rows),
            },
            llm_model=None,
            prompt_version="rules-baseline",
            guardrail_status="no_llm_no_unsupported_claims",
        ),
    ]


def _cv_actions(direct: list[str], transferable: list[str], gaps: list[GapReport]) -> list[str]:
    actions = [f"Make {skill} visible in the CV summary or project bullets." for skill in direct[:3]]
    actions.extend(
        f"Describe transferable experience honestly for {skill}; do not present it as direct commercial use."
        for skill in transferable[:2]
    )
    actions.extend(gap.recommended_action for gap in gaps[:2] if gap.recommended_action)
    return actions[:7]


def _prep_plan(direct: list[str], transferable: list[str], gaps: list[GapReport]) -> list[str]:
    plan = [f"Prepare a concrete project story for {skill}." for skill in direct[:3]]
    plan.extend(f"Review differences between your experience and {skill}." for skill in transferable[:2])
    plan.extend(f"Practice a transparent answer about missing {gap.gap_text}." for gap in gaps[:2])
    return plan[:7]
