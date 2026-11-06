"""Extract configured skills and job-specific keywords from text."""

from __future__ import annotations

import re

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

from text_preprocessing import preprocess_text

SKILL_TERMS = (
    "agile",
    "aws",
    "azure",
    "c",
    "c#",
    "c++",
    "communication",
    "css",
    "data analysis",
    "deep learning",
    "docker",
    "excel",
    "fastapi",
    "flask",
    "git",
    "google cloud",
    "html",
    "java",
    "javascript",
    "kubernetes",
    "leadership",
    "machine learning",
    "matplotlib",
    "natural language processing",
    "nlp",
    "numpy",
    "pandas",
    "power bi",
    "project management",
    "python",
    "pytorch",
    "react",
    "rest api",
    "scikit-learn",
    "sql",
    "statistics",
    "tableau",
    "tensorflow",
)

EDUCATION_TERMS = (
    "bachelor",
    "bachelors",
    "b.sc",
    "b.s.",
    "master",
    "masters",
    "m.sc",
    "m.s.",
    "mba",
    "ph.d",
    "phd",
    "associate degree",
    "doctorate",
)

QUALIFICATION_TERMS = (
    "aws certified",
    "certified scrum master",
    "cissp",
    "pmp",
    "professional certification",
    "professional engineer",
    "certification",
)

GENERIC_KEYWORDS = {
    "ability",
    "candidate",
    "experience",
    "experienced",
    "job",
    "looking",
    "preferred",
    "qualification",
    "qualifications",
    "requirement",
    "requirements",
    "responsibility",
    "responsibilities",
    "role",
    "team",
    "work",
    "working",
}


def _contains_term(text: str, term: str) -> bool:
    """Match complete phrases without mistaking C++ or C# for the C language."""
    expression = re.escape(term.lower())
    if term == "c":
        return re.search(r"(?<![a-z0-9])c(?![a-z0-9+#])", text) is not None
    return re.search(rf"(?<![a-z0-9]){expression}(?![a-z0-9])", text) is not None


def extract_skills(text: str) -> list[str]:
    """Return recognized skills in the order they appear in the vocabulary."""
    normalized_text = preprocess_text(text)
    return [
        skill
        for skill in SKILL_TERMS
        if _contains_term(normalized_text, skill)
    ]


def extract_education(text: str) -> list[str]:
    """Return recognized degree and education terms."""
    normalized_text = preprocess_text(text)
    return [
        term
        for term in EDUCATION_TERMS
        if _contains_term(normalized_text, term)
    ]


def extract_qualifications(text: str) -> list[str]:
    """Return recognized certification and professional qualification terms."""
    normalized_text = preprocess_text(text)
    return [
        term
        for term in QUALIFICATION_TERMS
        if _contains_term(normalized_text, term)
    ]


def extract_experience_years(text: str) -> float | None:
    """Return the largest explicit duration in years, if one is stated."""
    normalized_text = preprocess_text(text)
    durations = re.findall(
        r"(?<!\w)(\d+(?:\.\d+)?)\s*\+?\s*(?:years?|yrs?)(?!\w)",
        normalized_text,
    )
    if not durations:
        return None
    return max(float(duration) for duration in durations)


def extract_keywords(
    job_description: str,
    resume_text: str,
    limit: int = 10,
) -> list[str]:
    """Rank high-value job phrases that do not appear in the resume."""
    if limit < 1:
        raise ValueError("Keyword limit must be at least one.")

    job_text = preprocess_text(job_description)
    resume = preprocess_text(resume_text)
    if not job_text:
        return []

    vectorizer = TfidfVectorizer(
        stop_words="english",
        ngram_range=(1, 2),
        max_features=80,
        token_pattern=r"(?u)\b[a-zA-Z][a-zA-Z0-9+#.-]*\b",
    )
    try:
        job_vector = vectorizer.fit_transform([job_text])
    except ValueError as error:
        if "empty vocabulary" in str(error).lower():
            return []
        raise

    terms = vectorizer.get_feature_names_out()
    weights = job_vector.toarray()[0]
    ranked_indices = np.argsort(weights)[::-1]

    missing: list[str] = []
    for index in ranked_indices:
        term = terms[index]
        if term in GENERIC_KEYWORDS or len(term) < 3:
            continue
        if not _contains_term(resume, term):
            missing.append(term)
        if len(missing) >= limit:
            break
    return missing
