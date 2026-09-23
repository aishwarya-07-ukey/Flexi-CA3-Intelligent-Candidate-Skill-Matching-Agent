import math
import os
from datetime import datetime

import gradio as gr
from dotenv import load_dotenv

from agent import CandidateMatchingAgent
from resume_parser import extract_resume_text
from auth import authenticate


# =========================================================
# ENVIRONMENT
# =========================================================

load_dotenv()

agent = None

MAX_HISTORY = 8


# =========================================================
# AGENT
# =========================================================

def get_agent():
    global agent

    if agent is None:
        agent = CandidateMatchingAgent()

    return agent


# =========================================================
# LOGIN / LOGOUT
# =========================================================

def login(username, password):
    if authenticate(username, password):
        return (
            gr.update(visible=False),
            gr.update(visible=True),
            "Login successful."
        )

    return (
        gr.update(visible=True),
        gr.update(visible=False),
        "Invalid username or password."
    )


def logout():
    return (
        gr.update(visible=True),
        gr.update(visible=False),
        ""
    )


# =========================================================
# PRESENTATION HELPERS
# =========================================================

def render_score_gauge(score):
    """Beautiful circular match score."""

    try:
        score = float(score)
    except Exception:
        score = 0

    radius = 58
    circumference = 2 * math.pi * radius

    pct = max(0, min(100, score))
    offset = circumference * (1 - pct / 100)

    if pct >= 75:
        color = "#22C55E"
        verdict = "Strong match"
    elif pct >= 50:
        color = "#F59E0B"
        verdict = "Partial match"
    else:
        color = "#EF4444"
        verdict = "Weak match"

    return f"""
    <div class="gauge-container">

        <svg
            width="180"
            height="180"
            viewBox="0 0 150 150"
            class="score-gauge"
        >

            <circle
                cx="75"
                cy="75"
                r="{radius}"
                fill="none"
                stroke="#27344D"
                stroke-width="12"
            />

            <circle
                cx="75"
                cy="75"
                r="{radius}"
                fill="none"
                stroke="{color}"
                stroke-width="12"
                stroke-linecap="round"
                stroke-dasharray="{circumference:.2f}"
                stroke-dashoffset="{offset:.2f}"
                transform="rotate(-90 75 75)"
            />

            <text
                x="75"
                y="70"
                text-anchor="middle"
                font-family="Inter, sans-serif"
                font-size="27"
                font-weight="800"
                fill="{color}"
            >
                {pct:.0f}%
            </text>

            <text
                x="75"
                y="92"
                text-anchor="middle"
                font-family="Inter, sans-serif"
                font-size="11"
                fill="#94A3B8"
            >
                MATCH
            </text>

        </svg>

        <div
            class="gauge-verdict"
            style="color:{color};"
        >
            {verdict}
        </div>

    </div>
    """


def render_skill_chips(skills, kind):
    """Render matched or missing skills as pills."""

    if not skills:
        if kind == "matched":
            text = "No matched skills found"
        else:
            text = "No major skill gaps detected"

        return f"""
        <div class="empty-state">
            {text}
        </div>
        """

    if kind == "matched":
        icon = "✓"
        css_class = "matched-chip"
    else:
        icon = "+"
        css_class = "missing-chip"

    chips = ""

    for skill in skills:
        skill = str(skill).strip()

        if not skill:
            continue

        chips += f"""
        <span class="skill-chip {css_class}">
            <span class="chip-icon">{icon}</span>
            {skill}
        </span>
        """

    return f"""
    <div class="skill-chip-container">
        {chips}
    </div>
    """


def render_summary(resume_text, job_description):
    """Compact resume/job preview."""

    def preview(text, limit=450):
        if not text:
            return "No information available."

        text = " ".join(str(text).split())

        if len(text) > limit:
            return text[:limit] + "..."

        return text

    return f"""
    <div class="summary-grid">

        <div class="summary-card">

            <div class="summary-icon">
                📄
            </div>

            <div>
                <div class="summary-title">
                    Resume
                </div>

                <div class="summary-body">
                    {preview(resume_text)}
                </div>
            </div>

        </div>


        <div class="summary-card">

            <div class="summary-icon">
                💼
            </div>

            <div>
                <div class="summary-title">
                    Target Role
                </div>

                <div class="summary-body">
                    {preview(job_description)}
                </div>
            </div>

        </div>

    </div>
    """


def render_history(history):
    """Render previous analyses."""

    if not history:
        return """
        <div class="empty-state">
            No analyses yet this session.
        </div>
        """

    rows = ""

    for item in reversed(history):

        score = item.get("score", 0)

        if score >= 75:
            color = "#22C55E"
        elif score >= 50:
            color = "#F59E0B"
        else:
            color = "#EF4444"

        rows += f"""
        <div class="history-row">

            <div class="history-file">
                {item.get("file", "Resume")}
            </div>

            <div
                class="history-score"
                style="color:{color};"
            >
                {float(score):.0f}%
            </div>

            <div class="history-meta">
                {item.get("matched", 0)} matched
                ·
                {item.get("missing", 0)} gaps
            </div>

            <div class="history-time">
                {item.get("time", "")}
            </div>

        </div>
        """

    return f"""
    <div class="history-list">
        {rows}
    </div>
    """


# =========================================================
# CANDIDATE ANALYSIS
# =========================================================

def analyze_candidate(
    resume_file,
    job_description,
    required_skills,
    history
):
    history = history or []

    # -----------------------------
    # Validation
    # -----------------------------

    if resume_file is None:
        return (
            render_score_gauge(0),
            render_skill_chips([], "matched"),
            render_skill_chips([], "missing"),
            "Please upload a resume first.",
            {},
            "",
            history,
            render_history(history)
        )

    if not job_description or not job_description.strip():
        return (
            render_score_gauge(0),
            render_skill_chips([], "matched"),
            render_skill_chips([], "missing"),
            "Please enter a job description first.",
            {},
            "",
            history,
            render_history(history)
        )

    try:

        # -----------------------------
        # Agent
        # -----------------------------

        ag = get_agent()

        # -----------------------------
        # Extract resume
        # -----------------------------

        resume_text = extract_resume_text(resume_file)

        if not resume_text or not resume_text.strip():

            return (
                render_score_gauge(0),
                render_skill_chips([], "matched"),
                render_skill_chips([], "missing"),
                "Could not extract text from the resume.",
                {},
                "",
                history,
                render_history(history)
            )

        # -----------------------------
        # Skills
        # -----------------------------

        skills = [
            skill.strip()
            for skill in (required_skills or "").split(",")
            if skill.strip()
        ]

        # -----------------------------
        # AI analysis
        # -----------------------------

        result = ag.analyze(
            resume_text,
            job_description,
            skills
        )

        score = result.get("score", 0)

        matched = result.get(
            "matched_skills",
            []
        )

        missing = result.get(
            "missing_skills",
            []
        )

        analysis = result.get(
            "ai_analysis",
            "No AI analysis was returned."
        )

        # -----------------------------
        # Chat context
        # -----------------------------

        context = {
            "resume": resume_text,
            "job_description": job_description,
            "required_skills": ", ".join(skills),
            "score": score,
            "matched_skills": ", ".join(matched)
            if matched else "None",
            "missing_skills": ", ".join(missing)
            if missing else "None",
        }

        # -----------------------------
        # History
        # -----------------------------

        history.append({
            "file": os.path.basename(resume_file),
            "score": score,
            "matched": len(matched),
            "missing": len(missing),
            "time": datetime.now().strftime("%H:%M:%S")
        })

        history = history[-MAX_HISTORY:]

        # -----------------------------
        # Final output
        # -----------------------------

        return (
            render_score_gauge(score),

            render_skill_chips(
                matched,
                "matched"
            ),

            render_skill_chips(
                missing,
                "missing"
            ),

            analysis,

            context,

            render_summary(
                resume_text,
                job_description
            ),

            history,

            render_history(history)
        )

    except Exception as e:

        return (
            render_score_gauge(0),
            render_skill_chips([], "matched"),
            render_skill_chips([], "missing"),
            f"""
            ### Analysis Error

            `{str(e)}`

            Please check your API configuration and try again.
            """,
            {},
            "",
            history,
            render_history(history)
        )


# =========================================================
# AI CHAT
# =========================================================

def chat_with_ai(
    message,
    history,
    context
):

    history = history or []

    if not message or not message.strip():
        return history, ""

    if not context:

        history.append({
            "role": "assistant",
            "content": (
                "Please analyze a candidate first. "
                "Then I can answer questions about "
                "the candidate, skill gaps, and target role."
            )
        })

        return history, ""

    try:

        ag = get_agent()

        system_prompt = """
You are TALENTMATCH AI, an intelligent candidate
skill-matching and recruitment assistant.

Your job is to help users understand:

- candidate-job matching
- resume strengths
- matched skills
- missing skills
- learning priorities
- interview preparation
- technical skill requirements
- candidate development

IMPORTANT RULES:

1. Do not invent candidate information.

2. Use only information contained in the
   provided candidate context.

3. Clearly say when information is not available.

4. Do not claim a candidate has experience
   unless the resume supports it.

5. Keep answers professional, practical,
   and easy to understand.

6. When discussing skill gaps, distinguish
   between:
   - explicitly missing skills
   - skills that cannot be verified from the resume

7. Give actionable recommendations when asked.
"""

        candidate_context = f"""

CURRENT CANDIDATE CONTEXT

RESUME:
{context.get("resume", "")}

TARGET JOB:
{context.get("job_description", "")}

REQUIRED SKILLS:
{context.get("required_skills", "")}

MATCH SCORE:
{context.get("score", 0)}%

MATCHED SKILLS:
{context.get("matched_skills", "None")}

SKILL GAPS:
{context.get("missing_skills", "None")}
"""

        messages = [
            {
                "role": "system",
                "content": system_prompt + candidate_context
            }
        ]

        # Convert Gradio message history into OpenAI-style messages
        for item in history:

            if not isinstance(item, dict):
                continue

            role = item.get("role")
            content = item.get("content")

            if role in ["user", "assistant"] and content:

                messages.append({
                    "role": role,
                    "content": str(content)
                })

        messages.append({
            "role": "user",
            "content": message.strip()
        })

        response = ag.client.chat.completions.create(
            model="openrouter/free",
            messages=messages
        )

        answer = response.choices[0].message.content

        new_history = list(history)

        new_history.append({
            "role": "user",
            "content": message.strip()
        })

        new_history.append({
            "role": "assistant",
            "content": answer
        })

        return new_history, ""

    except Exception as e:

        history.append({
            "role": "assistant",
            "content": (
                "Sorry, I couldn't process that request.\n\n"
                f"Error: {str(e)}"
            )
        })

        return history, ""


def clear_chat():
    return []


# =========================================================
# THEME
# =========================================================

theme = gr.themes.Base(
    primary_hue=gr.themes.colors.indigo,
    secondary_hue=gr.themes.colors.violet,
    neutral_hue=gr.themes.colors.slate,

    font=[
        gr.themes.GoogleFont("Inter"),
        "system-ui",
        "sans-serif"
    ],

    font_mono=[
        gr.themes.GoogleFont("IBM Plex Mono"),
        "monospace"
    ]
).set(

    body_background_fill="#080D1A",

    background_fill_primary="#0F172A",

    background_fill_secondary="#080D1A",

    border_color_primary="#27344D",

    button_primary_background_fill="#6366F1",

    button_primary_background_fill_hover="#7C3AED",

    button_primary_text_color="#FFFFFF",

    block_title_text_color="#F8FAFC",

    block_label_text_color="#CBD5E1",

    body_text_color="#F8FAFC",

    input_background_fill="#0B1222",

    input_border_color="#27344D",

    block_border_width="1px",

    block_radius="14px"
)


# =========================================================
# CUSTOM CSS
# =========================================================

CUSTOM_CSS = """

@import url(
'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap'
);


/* =====================================================
   ROOT
   ===================================================== */

:root {

    --bg: #080D1A;

    --panel: #0F172A;

    --card: #141D31;

    --card2: #182238;

    --border: #27344D;

    --text: #F8FAFC;

    --muted: #94A3B8;

    --accent: #6366F1;

    --accent2: #8B5CF6;

    --success: #22C55E;

    --warning: #F59E0B;

    --danger: #EF4444;
}


/* =====================================================
   PAGE
   ===================================================== */

body {

    background: var(--bg) !important;

}


.gradio-container {

    max-width: 1450px !important;

    margin: auto !important;

    background:

        radial-gradient(
            circle at 10% 0%,
            rgba(99, 102, 241, 0.13),
            transparent 28%
        ),

        radial-gradient(
            circle at 90% 8%,
            rgba(139, 92, 246, 0.10),
            transparent 26%
        ),

        var(--bg) !important;

    color: var(--text) !important;

    font-family:
        'Inter',
        system-ui,
        sans-serif !important;

}


/* =====================================================
   LOGIN
   ===================================================== */

#login-card {

    max-width: 560px;

    margin: 7vh auto !important;

    padding: 36px !important;

    background:
        rgba(15, 23, 42, 0.96) !important;

    border:
        1px solid var(--border) !important;

    border-radius:
        24px !important;

    box-shadow:
        0 25px 80px rgba(0,0,0,0.35);

}


#brand {

    text-align: center;

    margin-bottom: 30px;

}


.brand-title {

    font-size: 32px;

    font-weight: 800;

    letter-spacing: -1.2px;

    color: var(--text);

}


.brand-title span {

    color: #818CF8;

}


.brand-subtitle {

    color: var(--muted);

    font-size: 14px;

    margin-top: 8px;

}


/* =====================================================
   DASHBOARD
   ===================================================== */

#dashboard {

    background:
        rgba(15, 23, 42, 0.92) !important;

    border:
        1px solid var(--border) !important;

    border-radius:
        24px !important;

    padding:
        30px !important;

    box-shadow:
        0 20px 70px rgba(0,0,0,0.25);

}


/* =====================================================
   HEADINGS
   ===================================================== */

.section-title {

    font-size: 21px;

    font-weight: 700;

    color: var(--text);

    margin-bottom: 5px;

}


.section-subtitle {

    color: var(--muted);

    font-size: 13px;

}


/* =====================================================
   INPUTS
   ===================================================== */

label {

    color: var(--text) !important;

    font-weight: 600 !important;

}


input,
textarea {

    background:
        #0B1222 !important;

    color:
        var(--text) !important;

    border:
        1px solid var(--border) !important;

    border-radius:
        12px !important;

}


textarea:focus,
input:focus {

    border-color:
        var(--accent) !important;

    box-shadow:
        0 0 0 2px
        rgba(99,102,241,0.13) !important;

}


/* =====================================================
   BUTTONS
   ===================================================== */

.primary-btn {

    background:
        linear-gradient(
            135deg,
            var(--accent),
            var(--accent2)
        ) !important;

    color:
        white !important;

    border:
        none !important;

    font-weight:
        700 !important;

    border-radius:
        12px !important;

    transition:
        all 0.2s ease !important;

}


.primary-btn:hover {

    transform:
        translateY(-1px);

    box-shadow:
        0 10px 30px
        rgba(99,102,241,0.28);

}


.secondary-btn {

    background:
        #1E293B !important;

    color:
        var(--text) !important;

    border:
        1px solid var(--border) !important;

    border-radius:
        10px !important;

}


/* =====================================================
   RESULT CARDS
   ===================================================== */

.result-card {

    background:
        var(--card) !important;

    border:
        1px solid var(--border) !important;

    border-radius:
        16px !important;

}


/* =====================================================
   SCORE GAUGE
   ===================================================== */

.gauge-container {

    display:
        flex;

    flex-direction:
        column;

    align-items:
        center;

    justify-content:
        center;

    min-height:
        235px;

    padding:
        5px;

}


.score-gauge {

    filter:
        drop-shadow(
            0 8px 18px
            rgba(99,102,241,0.10)
        );

}


.gauge-verdict {

    font-size:
        15px;

    font-weight:
        700;

    margin-top:
        -2px;

}


/* =====================================================
   SKILL CHIPS
   ===================================================== */

.skill-chip-container {

    display:
        flex;

    flex-wrap:
        wrap;

    gap:
        8px;

    padding:
        5px 0;

}


.skill-chip {

    display:
        inline-flex;

    align-items:
        center;

    gap:
        6px;

    font-size:
        13px;

    font-weight:
        600;

    padding:
        7px 12px;

    border-radius:
        999px;

}


.matched-chip {

    background:
        rgba(34,197,94,0.12);

    color:
        #86EFAC;

    border:
        1px solid
        rgba(34,197,94,0.25);

}


.missing-chip {

    background:
        rgba(245,158,11,0.11);

    color:
        #FCD34D;

    border:
        1px solid
        rgba(245,158,11,0.25);

}


.chip-icon {

    font-weight:
        800;

}


/* =====================================================
   EMPTY STATE
   ===================================================== */

.empty-state {

    color:
        var(--muted);

    font-size:
        13px;

    font-style:
        italic;

    padding:
        10px 0;

}


/* =====================================================
   AI ANALYSIS
   ===================================================== */

#analysis {

    background:
        var(--card) !important;

    border:
        1px solid var(--border) !important;

    border-radius:
        16px !important;

    padding:
        24px !important;

    line-height:
        1.7 !important;

    color:
        #E2E8F0 !important;

}


#analysis h1,
#analysis h2,
#analysis h3 {

    color:
        #A5B4FC !important;

}


/* =====================================================
   SUMMARY
   ===================================================== */

.summary-grid {

    display:
        grid;

    grid-template-columns:
        1fr 1fr;

    gap:
        14px;

}


.summary-card {

    display:
        flex;

    gap:
        13px;

    background:
        #10192B;

    border:
        1px solid var(--border);

    border-radius:
        14px;

    padding:
        16px;

}


.summary-icon {

    width:
        36px;

    height:
        36px;

    display:
        flex;

    align-items:
        center;

    justify-content:
        center;

    background:
        rgba(99,102,241,0.12);

    border-radius:
        10px;

    flex-shrink:
        0;

}


.summary-title {

    font-size:
        14px;

    font-weight:
        700;

    color:
        #A5B4FC;

    margin-bottom:
        5px;

}


.summary-body {

    font-size:
        13px;

    color:
        var(--muted);

    line-height:
        1.55;

}


/* =====================================================
   HISTORY
   ===================================================== */

.history-list {

    display:
        flex;

    flex-direction:
        column;

    gap:
        7px;

}


.history-row {

    display:
        grid;

    grid-template-columns:
        1.6fr
        0.6fr
        1fr
        0.7fr;

    align-items:
        center;

    gap:
        8px;

    padding:
        10px 12px;

    background:
        #10192B;

    border:
        1px solid var(--border);

    border-radius:
        10px;

    font-size:
        12px;

}


.history-file {

    color:
        var(--text);

    font-weight:
        600;

    overflow:
        hidden;

    text-overflow:
        ellipsis;

    white-space:
        nowrap;

}


.history-score {

    font-weight:
        800;

}


.history-meta {

    color:
        var(--muted);

}


.history-time {

    color:
        #64748B;

    text-align:
        right;

}


/* =====================================================
   CHAT
   ===================================================== */

#chatbox {

    background:
        var(--card) !important;

    border:
        1px solid var(--border) !important;

    border-radius:
        16px !important;

    overflow:
        hidden;

}


#chatbox .message {

    border-radius:
        14px !important;

}


.chat-title {

    font-size:
        21px;

    font-weight:
        750;

    color:
        var(--text);

}


.chat-subtitle {

    color:
        var(--muted);

    font-size:
        13px;

    margin-top:
        4px;

}


/* =====================================================
   LOGIN MESSAGE
   ===================================================== */

.login-message {

    text-align:
        center;

    color:
        var(--muted);

}


/* =====================================================
   FOOTER
   ===================================================== */

.footer {

    text-align:
        center;

    color:
        #64748B;

    font-size:
        12px;

    margin-top:
        28px;

    padding-top:
        15px;

}


/* =====================================================
   RESPONSIVE
   ===================================================== */

@media (max-width: 900px) {

    .summary-grid {

        grid-template-columns:
            1fr;

    }

}


@media (max-width: 768px) {

    .gradio-container {

        padding:
            10px !important;

    }


    #dashboard,
    #login-card {

        padding:
            18px !important;

        border-radius:
            16px !important;

    }


    .brand-title {

        font-size:
            26px;

    }


    .history-row {

        grid-template-columns:
            1fr 0.5fr;

    }


    .history-meta,
    .history-time {

        display:
            none;

    }

}

"""


# =========================================================
# GRADIO APPLICATION
# =========================================================

with gr.Blocks(
    title="TalentMatch AI"
) as demo:

    # -----------------------------------------------------
    # STATES
    # -----------------------------------------------------

    analysis_context = gr.State({})

    history_state = gr.State([])


    # =====================================================
    # LOGIN SCREEN
    # =====================================================

    with gr.Column(
        elem_id="login-card",
        visible=True
    ) as login_screen:

        gr.HTML(
            """
            <div id="brand">

                <div class="brand-title">
                    TALENT<span>MATCH AI</span>
                </div>

                <div class="brand-subtitle">
                    Intelligent Candidate Skill Matching Agent
                </div>

            </div>
            """
        )

        gr.Markdown(
            """
            ## Welcome back

            Sign in to analyze candidate resumes using
            semantic matching and AI-powered insights.
            """,
            elem_classes=["section-title"]
        )

        username = gr.Textbox(
            label="Username",
            placeholder="Enter username"
        )

        password = gr.Textbox(
            label="Password",
            placeholder="Enter password",
            type="password"
        )

        login_button = gr.Button(
            "Sign In",
            variant="primary",
            elem_classes=["primary-btn"]
        )

        login_message = gr.Markdown(
            "",
            elem_classes=["login-message"]
        )

        gr.Markdown(
            """
            **Demo credentials**

            Username: `admin`

            Password: `admin123`
            """
        )


    # =====================================================
    # MAIN DASHBOARD
    # =====================================================

    with gr.Column(
        elem_id="dashboard",
        visible=False
    ) as dashboard:

        # -------------------------------------------------
        # HEADER
        # -------------------------------------------------

        with gr.Row():

            with gr.Column(scale=5):

                gr.HTML(
                    """
                    <div>

                        <div class="brand-title">
                            TALENT<span>MATCH AI</span>
                        </div>

                        <div class="brand-subtitle">
                            Intelligent Candidate Skill Matching Agent
                        </div>

                    </div>
                    """
                )

            with gr.Column(scale=1):

                logout_button = gr.Button(
                    "Logout",
                    elem_classes=["secondary-btn"]
                )


        # -------------------------------------------------
        # INTRO
        # -------------------------------------------------

        gr.Markdown(
            """
            ## Candidate Analysis

            Upload a resume and provide the target job requirements.

            TalentMatch AI combines semantic matching,
            skill-gap detection, and LLM-powered recruitment insights.
            """,
            elem_classes=["section-title"]
        )


        # =================================================
        # INPUT + RESULT
        # =================================================

        with gr.Row():

            # ---------------------------------------------
            # INPUT
            # ---------------------------------------------

            with gr.Column(
                scale=5,
                elem_classes=["result-card"]
            ):

                gr.Markdown(
                    "Candidate & Role",
                    elem_classes=["section-title"]
                )

                resume_file = gr.File(
                    label="Candidate Resume",
                    file_types=[
                        ".pdf",
                        ".docx",
                        ".txt"
                    ],
                    type="filepath"
                )

                job_description = gr.Textbox(
                    label="Job Description",
                    placeholder=(
                        "Paste the target job description here..."
                    ),
                    lines=9
                )

                required_skills = gr.Textbox(
                    label="Required Skills",
                    placeholder=(
                        "Python, SQL, Machine Learning, Git, Java"
                    ),
                    lines=3
                )

                analyze_button = gr.Button(
                    "Analyze Candidate",
                    variant="primary",
                    elem_classes=["primary-btn"]
                )


            # ---------------------------------------------
            # RESULTS
            # ---------------------------------------------

            with gr.Column(
                scale=6,
                elem_classes=["result-card"]
            ):

                gr.Markdown(
                    "Matching Overview",
                    elem_classes=["section-title"]
                )

                match_score = gr.HTML(
                    render_score_gauge(0)
                )

                with gr.Row():

                    with gr.Column():

                        gr.Markdown(
                            "Matched Skills",
                            elem_classes=["section-title"]
                        )

                        matched_skills = gr.HTML(
                            render_skill_chips(
                                [],
                                "matched"
                            )
                        )


                    with gr.Column():

                        gr.Markdown(
                            "Skill Gaps",
                            elem_classes=["section-title"]
                        )

                        missing_skills = gr.HTML(
                            render_skill_chips(
                                [],
                                "missing"
                            )
                        )


        # =================================================
        # AI INSIGHTS
        # =================================================

        gr.Markdown(
            "AI Candidate Insights",
            elem_classes=["section-title"]
        )

        ai_analysis = gr.Markdown(
            """
            Run an analysis to generate
            AI-powered candidate insights.
            """,
            elem_id="analysis"
        )


        # =================================================
        # SUMMARY + HISTORY
        # =================================================

        with gr.Row():

            with gr.Column(
                scale=6,
                elem_classes=["result-card"]
            ):

                gr.Markdown(
                    "Resume & Job Summary",
                    elem_classes=["section-title"]
                )

                summary_panel = gr.HTML(
                    """
                    <div class="empty-state">
                        Run an analysis to see a summary.
                    </div>
                    """
                )


            with gr.Column(
                scale=5,
                elem_classes=["result-card"]
            ):

                gr.Markdown(
                    "Analysis History",
                    elem_classes=["section-title"]
                )

                history_panel = gr.HTML(
                    """
                    <div class="empty-state">
                        No analyses yet this session.
                    </div>
                    """
                )


        # =================================================
        # AI CHATBOX
        # =================================================

        gr.Markdown(
            """
            <div class="chat-title">
                🤖 TalentMatch AI Assistant
            </div>

            <div class="chat-subtitle">
                Ask questions about the candidate, skill gaps,
                interview preparation, or technical requirements.
            </div>
            """
        )

        chatbot = gr.Chatbot(
            label="AI Assistant",
            height=420,
            elem_id="chatbox"
        )

        with gr.Row():

            chat_input = gr.Textbox(
                placeholder=(
                    "Ask TalentMatch AI..."
                ),
                show_label=False,
                scale=6
            )

            send_button = gr.Button(
                "Send",
                variant="primary",
                elem_classes=["primary-btn"],
                scale=1
            )

            clear_button = gr.Button(
                "Clear",
                elem_classes=["secondary-btn"],
                scale=1
            )


        # =================================================
        # FOOTER
        # =================================================

        gr.Markdown(
            """
            <div class="footer">

                TALENTMATCH AI • Intelligent Candidate Skill Matching Agent

                <br>

                Powered by Semantic Matching + OpenRouter LLM

            </div>
            """
        )


    # =====================================================
    # EVENTS
    # =====================================================

    # LOGIN

    login_button.click(
        fn=login,

        inputs=[
            username,
            password
        ],

        outputs=[
            login_screen,
            dashboard,
            login_message
        ]
    )


    # LOGOUT

    logout_button.click(
        fn=logout,

        outputs=[
            login_screen,
            dashboard,
            login_message
        ]
    )


    # ANALYSIS

    analyze_button.click(
        fn=analyze_candidate,

        inputs=[
            resume_file,
            job_description,
            required_skills,
            history_state
        ],

        outputs=[
            match_score,
            matched_skills,
            missing_skills,
            ai_analysis,
            analysis_context,
            summary_panel,
            history_state,
            history_panel
        ]
    )


    # CHAT - SEND

    send_button.click(
        fn=chat_with_ai,

        inputs=[
            chat_input,
            chatbot,
            analysis_context
        ],

        outputs=[
            chatbot,
            chat_input
        ]
    )


    # CHAT - ENTER

    chat_input.submit(
        fn=chat_with_ai,

        inputs=[
            chat_input,
            chatbot,
            analysis_context
        ],

        outputs=[
            chatbot,
            chat_input
        ]
    )


    # CLEAR CHAT

    clear_button.click(
        fn=clear_chat,

        inputs=None,

        outputs=chatbot
    )


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))

    demo.launch(
        server_name="0.0.0.0",
        server_port=port,
        theme=theme,
        css=CUSTOM_CSS
    )