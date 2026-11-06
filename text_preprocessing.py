"""Small, dependency-free text cleanup helpers for resume analysis."""

from __future__ import annotations

import re


def preprocess_text(text: str) -> str:
    """Normalize text while preserving characters used in technical skills.

    The function intentionally does not remove stop words; TF-IDF handles those
    during matching, while keyword and skill extraction need the full text.
    """
    if not isinstance(text, str):
        raise TypeError("Text to preprocess must be a string.")

    cleaned = text.lower()
    cleaned = re.sub(r"https?://\S+|www\.\S+", " ", cleaned)
    cleaned = re.sub(r"\b[\w.+-]+@[\w.-]+\.[a-z]{2,}\b", " ", cleaned)
    cleaned = re.sub(r"[^a-z0-9+#./-]+", " ", cleaned)
    return re.sub(r"\s+", " ", cleaned).strip()
