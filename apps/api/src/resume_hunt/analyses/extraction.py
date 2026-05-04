import re
from dataclasses import dataclass


@dataclass(frozen=True)
class SkillMatch:
    canonical_name: str
    raw_mention: str
    evidence_text: str
    confidence: float


SKILL_ALIASES: dict[str, tuple[str, ...]] = {
    "Python": ("python",),
    "JavaScript": ("javascript", "js"),
    "TypeScript": ("typescript", "ts"),
    "React": ("react", "react.js", "reactjs"),
    "Next.js": ("next.js", "nextjs", "next js"),
    "FastAPI": ("fastapi", "fast api"),
    "Django": ("django", "django rest framework", "drf"),
    "Flask": ("flask",),
    "REST API": ("rest api", "restful", "api development", "rest endpoints"),
    "PostgreSQL": ("postgresql", "postgres", "psql"),
    "SQL": ("sql", "relational database", "database models"),
    "SQLAlchemy": ("sqlalchemy", "sql alchemy"),
    "Docker": ("docker", "docker compose"),
    "Git": ("git", "github", "gitlab"),
    "Pytest": ("pytest", "unit tests", "automated tests"),
    "AWS": ("aws", "amazon web services"),
    "Linux": ("linux",),
    "HTML": ("html",),
    "CSS": ("css", "tailwind"),
    "Celery": ("celery",),
    "Redis": ("redis",),
    "Kubernetes": ("kubernetes", "k8s"),
    "CI/CD": ("ci/cd", "github actions", "gitlab ci"),
    "English": ("english", "англійська", "английский"),
}

TRANSFERABLE_SKILLS: dict[str, set[str]] = {
    "Django": {"FastAPI", "Flask", "REST API", "Python"},
    "FastAPI": {"Django", "Flask", "REST API", "Python"},
    "Flask": {"FastAPI", "Django", "REST API", "Python"},
    "PostgreSQL": {"SQL"},
    "SQL": {"PostgreSQL", "SQLAlchemy"},
    "Pytest": {"REST API", "Python"},
    "Docker": {"Linux"},
    "Next.js": {"React", "TypeScript", "JavaScript"},
    "React": {"Next.js", "TypeScript", "JavaScript"},
}

SENIORITY_ORDER = {
    "trainee": 0,
    "junior": 1,
    "junior+": 2,
    "middle": 3,
    "senior": 4,
    "lead": 5,
}


def split_sentences(text: str) -> list[str]:
    chunks = re.split(r"(?<=[.!?])\s+|\n+|(?:\s+-\s+)", text)
    return [chunk.strip(" \t-*•") for chunk in chunks if len(chunk.strip()) > 2]


def extract_skills(text: str) -> list[SkillMatch]:
    lowered = text.lower()
    sentences = split_sentences(text)
    found: dict[str, SkillMatch] = {}
    for canonical, aliases in SKILL_ALIASES.items():
        for alias in aliases:
            pattern = rf"(?<![a-z0-9+#]){re.escape(alias)}(?![a-z0-9+#])"
            match = re.search(pattern, lowered)
            if not match:
                continue
            evidence = next(
                (sentence for sentence in sentences if alias in sentence.lower()),
                text[max(match.start() - 120, 0) : match.end() + 120].strip(),
            )
            found[canonical] = SkillMatch(
                canonical_name=canonical,
                raw_mention=match.group(0),
                evidence_text=evidence[:500],
                confidence=0.9 if alias == canonical.lower() else 0.82,
            )
            break
    return sorted(found.values(), key=lambda item: item.canonical_name.lower())


def detect_seniority(text: str) -> str | None:
    lowered = text.lower()
    if re.search(r"\b(lead|team lead|tech lead)\b", lowered):
        return "lead"
    if re.search(r"\b(senior|5\+?\s*years|5\+?\s*рок|5\+?\s*лет)\b", lowered):
        return "senior"
    if re.search(r"\b(middle|mid-level|3\+?\s*years|3\+?\s*рок|3\+?\s*лет)\b", lowered):
        return "middle"
    if re.search(r"\b(junior\+|strong junior)\b", lowered):
        return "junior+"
    if re.search(r"\b(junior|1\+?\s*year|1\+?\s*рік|1\+?\s*год|1\+?\s*рок)\b", lowered):
        return "junior"
    if re.search(r"\b(trainee|intern|стажер|стажерка)\b", lowered):
        return "trainee"
    return None


def detect_work_format(text: str) -> str:
    lowered = text.lower()
    if re.search(r"\b(remote|віддалено|удаленно)\b", lowered):
        return "remote"
    if re.search(r"\b(hybrid|гібрид|гибрид)\b", lowered):
        return "hybrid"
    if re.search(r"\b(office|офіс|офис)\b", lowered):
        return "office"
    return "unknown"


def detect_domain(text: str) -> str | None:
    lowered = text.lower()
    domains = {
        "fintech": ("fintech", "finance", "banking", "payments", "crypto"),
        "ecommerce": ("e-commerce", "ecommerce", "marketplace", "retail"),
        "edtech": ("edtech", "education", "learning"),
        "healthtech": ("healthtech", "healthcare", "medical"),
        "gamedev": ("gamedev", "game development", "ігри", "игры"),
        "saas": ("saas", "b2b product", "subscription"),
    }
    for domain, markers in domains.items():
        if any(marker in lowered for marker in markers):
            return domain
    return None


def infer_role(text: str) -> str | None:
    for line in text.splitlines():
        cleaned = line.strip(" -*•")
        if re.search(r"\b(developer|engineer|розробник|разработчик)\b", cleaned, re.IGNORECASE):
            return cleaned[:120]
    return None


def extract_section(text: str, headers: tuple[str, ...]) -> str:
    pattern = "|".join(re.escape(header) for header in headers)
    match = re.search(rf"(?im)^({pattern})\s*:?\s*$", text)
    if not match:
        return ""
    rest = text[match.end() :]
    next_header = re.search(r"(?im)^[a-zа-яіїєґ /+-]{3,32}\s*:?\s*$", rest)
    return rest[: next_header.start()] if next_header else rest


def parse_resume(text: str, target_role: str | None = None) -> dict:
    skills = extract_skills(text)
    seniority = detect_seniority(text)
    role = target_role or infer_role(text)
    skill_names = [skill.canonical_name for skill in skills]
    strong_signals = [skill.evidence_text for skill in skills[:5]]
    weak_signals: list[str] = []
    if "Docker" not in skill_names:
        weak_signals.append("Docker or deployment experience is not explicit")
    if "English" not in skill_names:
        weak_signals.append("English level is not explicit")
    if seniority in {None, "trainee", "junior"}:
        weak_signals.append("Commercial experience depth may need clearer evidence")

    return {
        "target_role": role,
        "estimated_seniority": seniority,
        "skills": [skill.__dict__ for skill in skills],
        "strong_signals": strong_signals,
        "weak_signals": weak_signals,
        "positioning": build_positioning(role, seniority, skill_names),
    }


def build_positioning(role: str | None, seniority: str | None, skills: list[str]) -> str | None:
    if not role and not skills:
        return None
    top_skills = ", ".join(skills[:4])
    seniority_part = f"{seniority} " if seniority else ""
    role_part = role or "software candidate"
    return f"{seniority_part}{role_part} with evidence in {top_skills}".strip()


def parse_vacancy(text: str, title: str) -> dict:
    skills = extract_skills(text)
    required_text = extract_section(
        text,
        (
            "requirements",
            "must have",
            "обов'язково",
            "вимоги",
            "требования",
            "необхідні навички",
        ),
    )
    preferred_text = extract_section(
        text,
        ("nice to have", "would be a plus", "буде плюсом", "плюсом", "бажано"),
    )
    responsibilities_text = extract_section(
        text,
        ("responsibilities", "what you will do", "обов'язки", "задачі", "обязанности"),
    )
    required_skill_names = {skill.canonical_name for skill in extract_skills(required_text)} if required_text else set()
    preferred_skill_names = (
        {skill.canonical_name for skill in extract_skills(preferred_text)} if preferred_text else set()
    )
    all_skill_names = [skill.canonical_name for skill in skills]
    if not required_skill_names:
        required_skill_names = set(all_skill_names[: max(1, min(6, len(all_skill_names)))])
    preferred_skill_names = preferred_skill_names - required_skill_names

    raw_requirements = [
        {
            "text": skill_name,
            "requirement_type": "technical_skill" if skill_name != "English" else "language_requirement",
            "priority": "required",
            "normalized_skill": skill_name,
        }
        for skill_name in sorted(required_skill_names)
    ]
    raw_requirements.extend(
        {
            "text": skill_name,
            "requirement_type": "technical_skill" if skill_name != "English" else "language_requirement",
            "priority": "preferred",
            "normalized_skill": skill_name,
        }
        for skill_name in sorted(preferred_skill_names)
    )

    return {
        "title": title,
        "required_skills": sorted(required_skill_names),
        "preferred_skills": sorted(preferred_skill_names),
        "responsibilities": split_sentences(responsibilities_text)[:8],
        "seniority": detect_seniority(text),
        "domain": detect_domain(text),
        "work_format": detect_work_format(text),
        "language_requirements": [
            requirement["text"]
            for requirement in raw_requirements
            if requirement["requirement_type"] == "language_requirement"
        ],
        "raw_requirements": raw_requirements,
        "skills": [skill.__dict__ for skill in skills],
    }


def seniority_distance(candidate: str | None, vacancy: str | None) -> int:
    if candidate is None or vacancy is None:
        return 0
    return SENIORITY_ORDER.get(vacancy, 0) - SENIORITY_ORDER.get(candidate, 0)
