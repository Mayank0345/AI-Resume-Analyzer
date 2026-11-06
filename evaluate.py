"""Calculate and explain the final resume-to-job match score."""

from __future__ import annotations

from collections.abc import Mapping

import numpy as np


def calculate_match_score(
    text_similarity: float,
    skill_coverage: float,
    has_required_skills: bool,
) -> float:
    """Return a score from zero to 100 using the project's documented weights."""
    if not np.isfinite(text_similarity) or not np.isfinite(skill_coverage):
        raise ValueError("Similarity and skill coverage must be finite numbers.")

    text_similarity = float(np.clip(text_similarity, 0, 100))
    skill_coverage = float(np.clip(skill_coverage, 0, 100))
    if has_required_skills:
        score = 0.7 * text_similarity + 0.3 * skill_coverage
    else:
        score = text_similarity
    return float(np.clip(score, 0, 100))


def evaluate_match(match_result: Mapping[str, object]) -> dict[str, object]:
    """Add an overall score and plain-language band to matcher results."""
    required_skills = match_result["required_skills"]
    score = calculate_match_score(
        float(match_result["text_similarity"]),
        float(match_result["skill_coverage"]),
        bool(required_skills),
    )
    if score >= 75:
        rating = "Strong"
    elif score >= 50:
        rating = "Moderate"
    else:
        rating = "Low"

    return {
        **match_result,
        "match_score": score,
        "rating": rating,
    }
