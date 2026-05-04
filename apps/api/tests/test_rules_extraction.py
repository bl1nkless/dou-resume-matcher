from resume_hunt.analyses.extraction import parse_resume, parse_vacancy
from resume_hunt.documents.service import build_document_parse


def test_parse_resume_extracts_normalized_skills_and_positioning() -> None:
    parsed = parse_resume(
        "Junior Python Backend Developer. Built FastAPI REST API with PostgreSQL and pytest.",
        target_role="Junior Python Backend Developer",
    )

    skill_names = {skill["canonical_name"] for skill in parsed["skills"]}

    assert {"Python", "FastAPI", "REST API", "PostgreSQL", "Pytest"} <= skill_names
    assert parsed["estimated_seniority"] == "junior"
    assert "Junior Python Backend Developer" in parsed["positioning"]


def test_parse_vacancy_extracts_requirements_and_work_format() -> None:
    parsed = parse_vacancy(
        "\n".join(
            [
                "Junior Python Developer",
                "Requirements:",
                "Python, Django or FastAPI, REST API, PostgreSQL, Git, English Intermediate.",
                "Remote work.",
            ]
        ),
        "Junior Python Developer",
    )

    assert parsed["seniority"] == "junior"
    assert parsed["work_format"] == "remote"
    assert {"Python", "Django", "FastAPI", "REST API", "PostgreSQL", "Git", "English"} <= set(
        parsed["required_skills"]
    )
    assert any(item["priority"] == "required" for item in parsed["raw_requirements"])


def test_document_parse_builds_chunks_and_skill_records() -> None:
    parsed = build_document_parse(
        "resume",
        "Python backend developer. Built REST API with PostgreSQL. Used Docker and Git.",
    )

    assert parsed["language"] == "en"
    assert parsed["sections"]
    assert parsed["sections"][0]["chunk_type"] == "resume_chunk"
    assert {"Python", "REST API", "PostgreSQL", "Docker", "Git"} <= {
        skill["canonical_name"] for skill in parsed["skills"]
    }
