"""Streamlit interface for the AI Resume Analyzer."""

from __future__ import annotations

import streamlit as st
from PyPDF2.errors import PdfReadError

from evaluate import evaluate_match
from job_matcher import match_resume_to_job
from resume_parser import extract_text_from_pdf
from skill_extractor import (
    extract_education,
    extract_experience_years,
    extract_qualifications,
)


def _build_suggestions(results: dict[str, object]) -> list[str]:
    """Create resume suggestions from detected gaps without inventing claims."""
    suggestions: list[str] = []
    missing_skills = results["missing_skills"]
    missing_keywords = results["missing_keywords"]
    if missing_skills:
        suggestions.append(
            "If you have these skills, make them easier to find: "
            + ", ".join(missing_skills)
            + "."
        )
    if missing_keywords:
        suggestions.append(
            "Use relevant job-specific terms where they accurately describe your "
            "experience: "
            + ", ".join(missing_keywords[:5])
            + "."
        )
    if not results["education"]:
        suggestions.append(
            "If relevant, add your degree, field of study, and institution in a "
            "clearly labeled education section."
        )
    if results["experience_years"] is None:
        suggestions.append(
            "Make your work history easy to scan with role titles, dates, and "
            "specific accomplishments."
        )
    if not suggestions:
        suggestions.append(
            "Your detected skills align well. Keep the resume focused on the role."
        )
    suggestions.append(
        "Highlight relevant projects and quantify their outcomes, such as time "
        "saved, users reached, or model performance improved."
    )
    return suggestions

st.set_page_config(
    page_title="AI Resume Analyzer",
    page_icon="📄",
    layout="wide",
)

st.markdown(
    """
    <style>
    .stApp { background: #f4f7fb; color: #17283d; }
    [data-testid="stAppViewContainer"] { color: #17283d; }
    [data-testid="stHeader"] { background: rgba(244, 247, 251, .92); }
    [data-testid="stMarkdownContainer"] p,
    [data-testid="stMarkdownContainer"] li,
    [data-testid="stWidgetLabel"] p,
    [data-testid="stCaptionContainer"] {
        color: #45566d;
    }
    [data-testid="stFileUploaderDropzone"] {
        background: #ffffff;
        border: 1px dashed #b9c9d8;
    }
    [data-testid="stTextAreaRootElement"] textarea,
    [data-testid="stTextInputRootElement"] input {
        color: #17283d !important;
        background-color: #ffffff !important;
        -webkit-text-fill-color: #17283d !important;
    }
    [data-testid="stTextAreaRootElement"],
    [data-testid="stTextInputRootElement"] {
        background-color: #ffffff !important;
    }
    h1, h2, h3, h4, h5, h6, label {
        color: #1b2f48 !important;
    }
    .block-container { max-width: 1180px; padding-top: 2.2rem; padding-bottom: 3rem; }
    .hero {
        padding: 2.1rem 2.3rem;
        border-radius: 22px;
        color: white;
        background: linear-gradient(120deg, #142c4e, #236879);
        margin-bottom: 1.25rem;
        box-shadow: 0 12px 30px rgba(20, 44, 78, .14);
    }
    .hero h1 { margin: 0; color: white !important; font-size: 2.4rem; letter-spacing: -.03em; }
    .hero p { margin: .65rem 0 0; color: #e2eff7; font-size: 1.06rem; }
    .eyebrow {
        color: #9bd6d1;
        font-size: .76rem;
        font-weight: 700;
        letter-spacing: .12em;
        text-transform: uppercase;
        margin-bottom: .45rem;
    }
    .section-heading { margin: 1.4rem 0 .25rem; }
    div[data-testid="stMetric"] {
        background: white;
        border: 1px solid #e6ebf2;
        padding: 1rem 1.1rem;
        border-radius: 14px;
        box-shadow: 0 4px 14px rgba(20, 44, 78, .04);
    }
    div[data-testid="stTabs"] button { font-weight: 600; }
    div.stButton > button[kind="primary"] {
        background: #197f83;
        color: #ffffff;
        border: 1px solid #197f83;
        border-radius: 10px;
        min-height: 3rem;
        font-weight: 650;
    }
    div.stButton > button[kind="primary"] p {
        color: #ffffff !important;
    }
    div.stButton > button[kind="primary"]:hover {
        background: #14696d;
        border-color: #14696d;
        color: #ffffff;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero">
        <div class="eyebrow">Career toolkit · Resume intelligence</div>
        <h1>AI Resume Analyzer</h1>
        <p>See how your experience aligns with the role, surface skill gaps, and
        find practical ways to strengthen your application.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.caption("Private by design: files are processed in this session and not saved. "
           "Scores are estimates, not hiring decisions.")

st.markdown("### Start your analysis")
st.markdown("Add a resume and the job description you want to target.")
left_column, right_column = st.columns([0.85, 1.15], gap="large")
with left_column:
    st.markdown("#### 1 · Your resume")
    resume_file = st.file_uploader(
        "Upload a text-based PDF",
        type=["pdf"],
        help="Scanned image-only PDFs need OCR before their text can be analyzed.",
    )

with right_column:
    st.markdown("#### 2 · Target job")
    job_source = st.radio(
        "Choose how to add the job description",
        ("Paste text", "Upload .txt"),
        horizontal=True,
        label_visibility="collapsed",
        key="job_source",
    )
    if job_source == "Paste text":
        job_file = None
        job_description_input = st.text_area(
            "Job description",
            height=165,
            placeholder=(
                "Paste the role summary, responsibilities, required skills, "
                "and qualifications here."
            ),
            key="job_description_text",
        )
    else:
        job_file = st.file_uploader(
            "Upload a plain-text job description",
            type=["txt"],
            key="job_description_file",
        )
        job_description_input = ""

if st.button("Analyze my resume", type="primary", use_container_width=True):
    if resume_file is None:
        st.error("Upload a PDF resume to continue.")
    else:
        try:
            resume_text = extract_text_from_pdf(resume_file.getvalue())

            if job_file is not None:
                job_description = job_file.getvalue().decode("utf-8-sig").strip()
            else:
                job_description = job_description_input.strip()

            results = evaluate_match(
                match_resume_to_job(resume_text, job_description)
            )
            results["education"] = extract_education(resume_text)
            results["experience_years"] = extract_experience_years(resume_text)
            results["qualifications"] = extract_qualifications(resume_text)
            results["suggestions"] = _build_suggestions(results)
        except (ValueError, UnicodeDecodeError, PdfReadError) as error:
            st.error(str(error))
        else:
            st.session_state["analysis_results"] = results
            st.session_state["resume_filename"] = resume_file.name

results = st.session_state.get("analysis_results")
if results:
    st.divider()
    st.markdown("### Resume analysis results")
    st.caption(
        f"Analysis for **{st.session_state.get('resume_filename', 'uploaded resume')}**"
    )

    score_column, similarity_column, coverage_column = st.columns(3, gap="medium")
    score_column.metric("Job match score", f"{results['match_score']:.0f}%")
    similarity_column.metric("Content similarity", f"{results['text_similarity']:.0f}%")
    if results["required_skills"]:
        coverage_column.metric("Required skills matched", f"{results['skill_coverage']:.0f}%")
    else:
        coverage_column.metric("Required skills matched", "Not detected")

    score = results["match_score"]
    if results["rating"] == "Strong":
        st.success(f"**{results['rating']} match** · Your resume aligns well with this role.")
    elif results["rating"] == "Moderate":
        st.warning(f"**{results['rating']} match** · A few targeted updates may improve alignment.")
    else:
        st.info(f"**{results['rating']} match** · Review the role-specific gaps below.")
    st.progress(int(score), text="Overall match")

    overview_tab, skills_tab, resume_tab, suggestions_tab = st.tabs(
        ["Overview", "Skills & keywords", "Resume details", "Suggestions"]
    )
    with overview_tab:
        st.markdown("#### What is contributing to your score?")
        if results["required_skills"]:
            chart_data = results["skill_table"].copy()
            chart_data["Match"] = chart_data["Found in resume"].astype(int) * 100
            st.bar_chart(
                chart_data.set_index("Skill")[["Match"]],
                horizontal=True,
                height=max(180, 42 * len(chart_data)),
                color="#287d83",
            )
            st.caption("Each bar shows whether a required skill was detected in the resume.")
        else:
            st.info("No skills from the analyzer's built-in list were detected in the job description. The score is based on text similarity.")

        matched_count = len(results["matched_skills"])
        required_count = len(results["required_skills"])
        if required_count:
            st.write(
                f"**{matched_count} of {required_count}** recognized job skills "
                "were found in your resume."
            )

    with skills_tab:
        matched_column, missing_column = st.columns(2, gap="large")
        with matched_column:
            st.markdown("#### Skills identified")
            if results["matched_skills"]:
                st.success(" · ".join(results["matched_skills"]))
            elif results["resume_skills"]:
                st.info("Resume skills: " + ", ".join(results["resume_skills"]))
            else:
                st.info("No skills from the analyzer's built-in list were detected.")
        with missing_column:
            st.markdown("#### Missing skills")
            if results["missing_skills"]:
                st.warning(" · ".join(results["missing_skills"]))
            elif results["required_skills"]:
                st.success("All detected job skills appear in the resume.")
            else:
                st.info("No known required skills were detected in the job description.")

        st.markdown("#### Skills checklist")
        if results["required_skills"]:
            st.dataframe(
                results["skill_table"],
                hide_index=True,
                use_container_width=True,
            )
        else:
            st.caption("The checklist appears when recognizable skills are found in the job description.")
        st.markdown("#### Keywords to consider")
        if results["missing_keywords"]:
            st.write(", ".join(results["missing_keywords"]))
            st.caption("Use these terms only where they accurately describe your experience.")
        else:
            st.write("No additional high-priority keywords were identified.")

    with resume_tab:
        st.markdown("#### Information extracted from your resume")
        experience = results["experience_years"]
        detail_columns = st.columns(2)
        detail_columns[0].metric(
            "Experience mentioned",
            (
                f"At least {experience:g} years"
                if experience is not None
                else "Not detected"
            ),
        )
        detail_columns[1].metric(
            "Education",
            ", ".join(results["education"]) if results["education"] else "Not detected",
        )
        st.write(
            "**Skills:** "
            + (", ".join(results["resume_skills"]) if results["resume_skills"] else "None detected")
        )
        st.write(
            "**Qualifications / certifications:** "
            + (", ".join(results["qualifications"]) if results["qualifications"] else "None detected")
        )

    with suggestions_tab:
        st.markdown("#### Ways to strengthen your resume for this role")
        for index, suggestion in enumerate(results["suggestions"], start=1):
            st.markdown(f"**{index}.** {suggestion}")
        st.caption("Only include skills, experience, and achievements that are accurate.")

    with st.expander("How the score is calculated"):
        st.write(
            "The text-similarity component uses TF-IDF features and cosine similarity. "
            "When job skills are detected, the overall score combines 40% text "
            "similarity with 60% required-skill coverage. If no known job skills "
            "are detected, the text-similarity score is used on its own."
        )
        st.write(
            "Skill, education, experience, and qualification extraction uses "
            "transparent keyword and pattern matching. Review the results; this "
            "beginner-friendly tool does not understand context like a human reviewer."
        )
