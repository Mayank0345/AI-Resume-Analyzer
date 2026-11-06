"""Tests for the independent resume-analysis modules."""

import unittest
from io import BytesIO

from PyPDF2 import PdfWriter

from evaluate import calculate_match_score, evaluate_match
from job_matcher import match_resume_to_job
from resume_parser import extract_text_from_pdf
from skill_extractor import (
    extract_education,
    extract_experience_years,
    extract_keywords,
    extract_qualifications,
    extract_skills,
)
from text_preprocessing import preprocess_text

SAMPLE_RESUME = (
    "Python developer with pandas, 3 years of experience, "
    "a Bachelor degree, and AWS Certified status."
)
SAMPLE_JOB = "Python and SQL experience required; machine learning is preferred."


class TextPreprocessingTests(unittest.TestCase):
    def test_normalizes_text_and_preserves_technical_terms(self):
        result = preprocess_text(
            "C++ developer. Contact: user@example.com https://example.com"
        )
        self.assertIn("c++", result)
        self.assertNotIn("user@example.com", result)
        self.assertNotIn("https", result)


class SkillExtractorTests(unittest.TestCase):
    def test_extracts_skills_and_details_from_sample_resume(self):
        self.assertIn("python", extract_skills(SAMPLE_RESUME))
        self.assertIn("pandas", extract_skills(SAMPLE_RESUME))
        self.assertIn("bachelor", extract_education(SAMPLE_RESUME))
        self.assertEqual(extract_experience_years(SAMPLE_RESUME), 3.0)
        self.assertIn("aws certified", extract_qualifications(SAMPLE_RESUME))

    def test_cplusplus_is_not_mistaken_for_c(self):
        self.assertEqual(extract_skills("C++ developer"), ["c++"])

    def test_extracts_missing_keywords_from_sample_job(self):
        keywords = extract_keywords(SAMPLE_JOB, SAMPLE_RESUME)
        self.assertTrue(keywords)
        self.assertIn("sql", keywords)


class ResumeParserTests(unittest.TestCase):
    def test_rejects_empty_pdf_upload(self):
        with self.assertRaisesRegex(ValueError, "empty"):
            extract_text_from_pdf(b"")

    def test_rejects_pdf_without_extractable_text(self):
        writer = PdfWriter()
        writer.add_blank_page(width=72, height=72)
        pdf = BytesIO()
        writer.write(pdf)
        with self.assertRaisesRegex(ValueError, "OCR"):
            extract_text_from_pdf(pdf.getvalue())


class JobMatcherAndEvaluationTests(unittest.TestCase):
    def test_compares_sample_resume_and_job_description(self):
        matched = match_resume_to_job(SAMPLE_RESUME, SAMPLE_JOB)
        self.assertIn("python", matched["matched_skills"])
        self.assertIn("sql", matched["missing_skills"])
        self.assertGreaterEqual(matched["text_similarity"], 0)
        self.assertLessEqual(matched["text_similarity"], 100)
        evaluated = evaluate_match(matched)
        self.assertTrue(0 <= evaluated["match_score"] <= 100)
        self.assertIn(evaluated["rating"], {"Low", "Moderate", "Strong"})

    def test_score_uses_similarity_alone_without_detected_skills(self):
        self.assertEqual(calculate_match_score(82, 0, False), 82)

    def test_rejects_empty_match_inputs(self):
        with self.assertRaisesRegex(ValueError, "resume"):
            match_resume_to_job("", "Python developer")
        with self.assertRaisesRegex(ValueError, "job description"):
            match_resume_to_job("Python developer", " ")


if __name__ == "__main__":
    unittest.main()
