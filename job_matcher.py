"""Compare resume text with job requirements using TF-IDF and skill coverage."""

from __future__ import annotations

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from skill_extractor import extract_keywords, extract_skills
from text_preprocessing import preprocess_text


def match_resume_to_job(
    resume_text: str,
    job_description: str,
) -> dict[str, object]:
    """Return similarity, skill coverage, and missing job terms.

    The weighted overall score is calculated separately by ``evaluate.py``.
    """
    resume_text = preprocess_text(resume_text)
    job_description = preprocess_text(job_description)
    if not resume_text:
        raise ValueError("The resume does not contain any text to analyze.")
    if not job_description:
        raise ValueError("Enter or upload a job description to continue.")

    vectorizer = TfidfVectorizer(
        stop_words="english",
        ngram_range=(1, 2),
        token_pattern=r"(?u)\b[a-zA-Z][a-zA-Z0-9+#.-]*\b",
    )
    analyzer = vectorizer.build_analyzer()
    if analyzer(resume_text) and analyzer(job_description):
        document_vectors = vectorizer.fit_transform([resume_text, job_description])
        similarity = float(
            cosine_similarity(document_vectors[0:1], document_vectors[1:2])[0, 0]
        )
    else:
        similarity = 0.0

    resume_skills = extract_skills(resume_text)
    required_skills = extract_skills(job_description)
    matched_skills = [
        skill for skill in required_skills if skill in resume_skills
    ]
    missing_skills = [
        skill for skill in required_skills if skill not in resume_skills
    ]
    skill_coverage = (
        len(matched_skills) / len(required_skills) * 100
        if required_skills
        else 0.0
    )

    return {
        "text_similarity": similarity * 100,
        "skill_coverage": skill_coverage,
        "resume_skills": resume_skills,
        "required_skills": required_skills,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "skill_table": pd.DataFrame(
            {
                "Skill": required_skills,
                "Found in resume": [
                    skill in resume_skills for skill in required_skills
                ],
            }
        ),
        "missing_keywords": extract_keywords(job_description, resume_text),
    }
