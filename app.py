import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import json
import re

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Candidate Assessment",
    page_icon="📋",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── Google Sheet config ─────────────────────────────────────────────────────────
# IMPORTANT: Replace this with your actual Google Sheet ID
# (the long string in the sheet URL between /d/ and /edit)
GOOGLE_SHEET_ID = "1S4WTfsI5-jf3OJPHrt33mGtUdvSSad2P608Yg24hZJw"
SHEET_NAME = "Sheet1"   # change if your tab has a different name

# ── Questions ──────────────────────────────────────────────────────────────────
QUESTIONS = [
    {
        "q": "What comes next? 2, 4, 6, 8, ?",
        "options": ["A. 9", "B. 10", "C. 11", "D. 12"],
        "correct": "B. 10",
        "situation": False,
    },
    {
        "q": "Solve for x: 5x − 10 = 20",
        "options": ["A. 4", "B. 5", "C. 6", "D. 7"],
        "correct": "C. 6",
        "situation": False,
    },
    {
        "q": "25% of 200 =",
        "options": ["A. 25", "B. 40", "C. 50", "D. 75"],
        "correct": "C. 50",
        "situation": False,
    },
    {
        "q": "How to copy text?",
        "options": ["A. Ctrl + C", "B. Ctrl + B", "C. Ctrl + V", "D. Ctrl + S"],
        "correct": "A. Ctrl + C",
        "situation": False,
    },
    {
        "q": "How to paste text?",
        "options": ["A. Ctrl + C", "B. Ctrl + B", "C. Ctrl + V", "D. Ctrl + S"],
        "correct": "C. Ctrl + V",
        "situation": False,
    },
    {
        "q": "What should you do if you face a problem or task that you don't know how to handle?",
        "options": [
            "A. Ask your Team Leader for guidance.",
            "B. Ask your Manager directly about the issue.",
            "C. Ask the HR Admin if they know how to solve it.",
            "D. Keep trying different solutions until you fix it yourself.",
        ],
        "correct": "A. Ask your Team Leader for guidance.",
        "situation": False,
    },
    {
        "q": "How do you usually plan and organize your workday to stay productive?",
        "options": [
            "A. Write a simple plan on a note and complete tasks whenever possible.",
            "B. Create main points and mark them when they are completed.",
            "C. Divide the day into time blocks and assign tasks to each period.",
            "D. Create a to-do list and organize tasks based on priority.",
        ],
        "correct": "D. Create a to-do list and organize tasks based on priority.",
        "situation": False,
    },
    {
        "q": "What would you do if you realized you made a mistake at work?",
        "options": [
            "A. Ignore it and hope nobody notices.",
            "B. Fix the mistake immediately and inform your Team Leader.",
            "C. Blame the system or another employee.",
            "D. Wait until someone reports the problem.",
        ],
        "correct": "B. Fix the mistake immediately and inform your Team Leader.",
        "situation": False,
    },
    {
        "q": 'You call a doctor\'s office to follow up on a prescription that needs the doctor\'s signature. The nurse answers but sounds busy and says "Call later."',
        "options": [
            "A. Insist she checks immediately.",
            "B. Hang up and stop following up.",
            "C. Explain the request again and ask for a convenient time to follow up.",
            "D. Threaten to report them.",
        ],
        "correct": "C. Explain the request again and ask for a convenient time to follow up.",
        "situation": True,
    },
    {
        "q": "You call to confirm the prescription fax but the nurse says they never received it.",
        "options": [
            "A. Argue it is their fault.",
            "B. Confirm the fax number and resend the document.",
            "C. Tell them to check better.",
            "D. End the call.",
        ],
        "correct": "B. Confirm the fax number and resend the document.",
        "situation": True,
    },
    {
        "q": "The nurse refuses to transfer the call because she is busy.",
        "options": [
            "A. Ask politely if there is a better time to call or another staff member who can assist.",
            "B. Demand to speak to the doctor immediately.",
            "C. Hang up and mark the office as non-cooperative.",
            "D. Call repeatedly.",
        ],
        "correct": "A. Ask politely if there is a better time to call or another staff member who can assist.",
        "situation": True,
    },
    {
        "q": "The doctor is not in the office today to sign the prescription.",
        "options": [
            "A. Ask when the doctor will return and schedule a follow-up call.",
            "B. Tell them it must be signed today.",
            "C. Cancel the order.",
            "D. Ask them to sign it themselves.",
        ],
        "correct": "A. Ask when the doctor will return and schedule a follow-up call.",
        "situation": True,
    },
]

TOTAL_QUESTIONS = len(QUESTIONS)

# ── Styling ────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  /* ── Google font ── */
  @import url('https://fonts.googleapis.com/css2?family=Sora:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

  html, body, [class*="css"] {
    font-family: 'Sora', sans-serif !important;
  }

  /* ── Dark background ── */
  .stApp {
    background: #0a0f1e;
    background-image:
      radial-gradient(ellipse 80% 50% at 20% 10%, rgba(99,179,237,0.07) 0%, transparent 60%),
      radial-gradient(ellipse 60% 40% at 80% 90%, rgba(79,209,199,0.05) 0%, transparent 60%);
  }

  /* ── Hide streamlit chrome ── */
  #MainMenu, footer, header { visibility: hidden; }
  .block-container { padding-top: 2rem; padding-bottom: 2rem; max-width: 680px; }

  /* ── Typography ── */
  h1 { font-size: 2rem !important; font-weight: 700 !important; letter-spacing: -0.02em !important;
       background: linear-gradient(135deg, #e2e8f0 0%, #63b3ed 60%, #4fd1c7 100%);
       -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }
  h2 { color: #e2e8f0 !important; font-weight: 600 !important; font-size: 1.1rem !important; }
  p, label, div { color: #cbd5e0; }

  /* ── Input fields ── */
  .stTextInput > div > div > input,
  .stTextInput > div > div > input:focus {
    background: #1a2236 !important;
    border: 1px solid rgba(99,179,237,0.2) !important;
    border-radius: 10px !important;
    color: #e2e8f0 !important;
    font-family: 'Sora', sans-serif !important;
    padding: 12px 16px !important;
  }
  .stTextInput > div > div > input:focus {
    border-color: #63b3ed !important;
    box-shadow: 0 0 0 3px rgba(99,179,237,0.15) !important;
  }
  .stTextInput label { color: #718096 !important; font-size: 11px !important;
                       text-transform: uppercase; letter-spacing: 0.08em; font-weight: 500; }

  /* ── Radio buttons ── */
  .stRadio > label { color: #718096 !important; font-size: 11px !important;
                     text-transform: uppercase; letter-spacing: 0.08em; font-weight: 500; }
  .stRadio > div { gap: 8px !important; }
  .stRadio > div > label {
    background: #111827 !important;
    border: 1px solid rgba(99,179,237,0.15) !important;
    border-radius: 10px !important;
    padding: 12px 16px !important;
    color: #cbd5e0 !important;
    font-size: 14px !important;
    transition: all 0.2s !important;
    cursor: pointer !important;
    width: 100% !important;
  }
  .stRadio > div > label:hover {
    border-color: rgba(99,179,237,0.4) !important;
    background: rgba(99,179,237,0.06) !important;
  }
  /* selected radio */
  .stRadio > div [data-testid="stMarkdownContainer"] { color: #e2e8f0 !important; }

  /* ── Buttons ── */
  .stButton > button {
    background: linear-gradient(135deg, #63b3ed, #4fd1c7) !important;
    color: #0a0f1e !important;
    font-family: 'Sora', sans-serif !important;
    font-weight: 700 !important;
    font-size: 15px !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 14px 28px !important;
    width: 100% !important;
    transition: all 0.2s !important;
    letter-spacing: 0.01em !important;
  }
  .stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 8px 24px rgba(99,179,237,0.35) !important;
  }

  /* ── Cards / containers ── */
  .card {
    background: #111827;
    border: 1px solid rgba(99,179,237,0.12);
    border-radius: 14px;
    padding: 28px 32px;
    margin-bottom: 20px;
    box-shadow: 0 24px 80px rgba(0,0,0,0.35);
  }
  .badge {
    display: inline-block;
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: #63b3ed;
    border: 1px solid rgba(99,179,237,0.3);
    padding: 4px 14px;
    border-radius: 20px;
    margin-bottom: 12px;
  }
  .situation-badge {
    display: inline-block;
    background: rgba(99,179,237,0.1);
    color: #63b3ed;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    padding: 3px 12px;
    border-radius: 20px;
    margin-bottom: 10px;
    font-family: 'JetBrains Mono', monospace;
  }
  .q-number {
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    color: #63b3ed;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin-bottom: 6px;
  }
  .q-text {
    font-size: 16px;
    font-weight: 600;
    color: #e2e8f0;
    line-height: 1.6;
    margin-bottom: 4px;
  }
  .progress-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    color: #718096;
    display: flex;
    justify-content: space-between;
    margin-bottom: 6px;
  }
  .muted { color: #718096 !important; font-size: 14px !important; }

  /* ── Success screen ── */
  .success-box {
    background: #111827;
    border: 1px solid rgba(99,179,237,0.2);
    border-radius: 14px;
    padding: 48px 32px;
    text-align: center;
    box-shadow: 0 24px 80px rgba(0,0,0,0.35);
  }
  .success-icon {
    font-size: 48px;
    margin-bottom: 20px;
  }
  .success-title {
    font-size: 22px;
    font-weight: 700;
    background: linear-gradient(135deg, #e2e8f0, #63b3ed);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 14px;
  }
  .success-msg {
    color: #718096;
    font-size: 15px;
    line-height: 1.7;
    max-width: 420px;
    margin: 0 auto;
  }

  /* ── Divider ── */
  hr { border-color: rgba(99,179,237,0.1) !important; }

  /* ── Error text ── */
  .err { color: #fc8181 !important; font-size: 13px !important; margin-top: 4px; }
</style>
""", unsafe_allow_html=True)


# ── Session state init ─────────────────────────────────────────────────────────
def init_state():
    defaults = {
        "phase": "info",          # info | assessment | submitting | done
        "candidate": {},
        "current_q": 0,
        "answers": {},            # {0: "B. 10", 1: "C. 6", ...}
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()


# ── Google Sheets helper ───────────────────────────────────────────────────────
def get_gsheet_client():
    """Build gspread client using service account credentials from st.secrets."""
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    # Read from Streamlit secrets (set up in .streamlit/secrets.toml)
    creds_dict = dict(st.secrets["gcp_service_account"])
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    return gspread.authorize(creds)


def ensure_header(worksheet):
    """Add header row if the sheet is empty."""
    try:
        first = worksheet.cell(1, 1).value
        if not first:
            raise ValueError("empty")
    except Exception:
        headers = (
            ["Timestamp", "Name", "Phone", "Email", "Score"]
            + [f"Q{i+1}" for i in range(TOTAL_QUESTIONS)]
        )
        worksheet.append_row(headers)


def submit_to_sheet(candidate, answers, score):
    """Append one result row to Google Sheets."""
    try:
        client = get_gsheet_client()
        sheet = client.open_by_key(GOOGLE_SHEET_ID)
        worksheet = sheet.worksheet(SHEET_NAME)
        ensure_header(worksheet)

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # Extract just the letter (A/B/C/D) for cleaner storage
        answer_letters = []
        for i in range(TOTAL_QUESTIONS):
            ans = answers.get(i, "No Answer")
            # grab just the letter prefix (e.g. "B" from "B. 10")
            letter = ans[0] if ans and ans != "No Answer" else "—"
            answer_letters.append(letter)

        row = (
            [timestamp, candidate["name"], candidate["phone"], candidate["email"], f"{score}/{TOTAL_QUESTIONS}"]
            + answer_letters
        )
        worksheet.append_row(row)
        return True, None
    except Exception as e:
        return False, str(e)


def calculate_score(answers):
    score = 0
    for i, q in enumerate(QUESTIONS):
        user_ans = answers.get(i, "")
        if user_ans == q["correct"]:
            score += 1
    return score


# ── Validate email / phone ─────────────────────────────────────────────────────
def valid_email(email):
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email))

def valid_phone(phone):
    return bool(re.match(r"^[\d\s\+\-\(\)]{7,20}$", phone))


# ════════════════════════════════════════════════════════════════════════════════
# PAGE: CANDIDATE INFO
# ════════════════════════════════════════════════════════════════════════════════
def page_info():
    # Header
    st.markdown('<div class="badge">Candidate Portal</div>', unsafe_allow_html=True)
    st.markdown("# Skills Assessment")
    st.markdown('<p class="muted">Please fill in your details to begin the assessment.</p>', unsafe_allow_html=True)
    st.markdown("<hr>", unsafe_allow_html=True)

    st.markdown('<div class="card">', unsafe_allow_html=True)

    name  = st.text_input("Full Name", placeholder="e.g. Sarah Johnson",
                          value=st.session_state.candidate.get("name", ""))
    phone = st.text_input("Phone Number", placeholder="e.g. +1 555 000 0000",
                          value=st.session_state.candidate.get("phone", ""))
    email = st.text_input("Email Address", placeholder="e.g. sarah@example.com",
                          value=st.session_state.candidate.get("email", ""))

    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("Begin Assessment →"):
        errors = []
        if not name.strip():
            errors.append("Full name is required.")
        if not phone.strip() or not valid_phone(phone.strip()):
            errors.append("A valid phone number is required.")
        if not email.strip() or not valid_email(email.strip()):
            errors.append("A valid email address is required.")

        if errors:
            for e in errors:
                st.markdown(f'<p class="err">⚠ {e}</p>', unsafe_allow_html=True)
        else:
            st.session_state.candidate = {
                "name": name.strip(),
                "phone": phone.strip(),
                "email": email.strip(),
            }
            st.session_state.phase = "assessment"
            st.session_state.current_q = 0
            st.rerun()


# ════════════════════════════════════════════════════════════════════════════════
# PAGE: ASSESSMENT (one question at a time)
# ════════════════════════════════════════════════════════════════════════════════
def page_assessment():
    idx = st.session_state.current_q
    q   = QUESTIONS[idx]

    # ── Header ──
    st.markdown('<div class="badge">Assessment</div>', unsafe_allow_html=True)
    st.markdown("# Skills Assessment")

    # ── Progress ──
    progress_pct = int((idx / TOTAL_QUESTIONS) * 100)
    st.markdown(
        f'<div class="progress-label"><span>Question {idx+1} of {TOTAL_QUESTIONS}</span>'
        f'<span>{progress_pct}%</span></div>',
        unsafe_allow_html=True,
    )
    st.progress(idx / TOTAL_QUESTIONS)
    st.markdown("<hr>", unsafe_allow_html=True)

    # ── Question card ──
    st.markdown('<div class="card">', unsafe_allow_html=True)

    if q["situation"]:
        st.markdown('<div class="situation-badge">📋 Situation</div>', unsafe_allow_html=True)

    st.markdown(f'<div class="q-number">Question {idx + 1}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="q-text">{q["q"]}</div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    # Pre-select if already answered
    current_val = st.session_state.answers.get(idx, None)
    try:
        default_idx = q["options"].index(current_val) if current_val in q["options"] else 0
    except Exception:
        default_idx = 0

    chosen = st.radio(
        "Select your answer:",
        q["options"],
        index=default_idx,
        key=f"q_{idx}",
        label_visibility="collapsed",
    )

    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    # ── Navigation ──
    col1, col2 = st.columns([1, 3])
    with col1:
        if idx > 0:
            if st.button("← Back"):
                st.session_state.answers[idx] = chosen
                st.session_state.current_q -= 1
                st.rerun()
    with col2:
        is_last = (idx == TOTAL_QUESTIONS - 1)
        btn_label = "Submit Assessment ✓" if is_last else "Next Question →"
        if st.button(btn_label):
            st.session_state.answers[idx] = chosen

            if is_last:
                # Check all questions answered
                if len(st.session_state.answers) < TOTAL_QUESTIONS:
                    st.warning("Please answer all questions before submitting.")
                else:
                    st.session_state.phase = "submitting"
                    st.rerun()
            else:
                st.session_state.current_q += 1
                st.rerun()


# ════════════════════════════════════════════════════════════════════════════════
# PAGE: SUBMITTING (calculate score + push to Sheets)
# ════════════════════════════════════════════════════════════════════════════════
def page_submitting():
    with st.spinner("Submitting your assessment…"):
        score = calculate_score(st.session_state.answers)
        ok, err = submit_to_sheet(
            st.session_state.candidate,
            st.session_state.answers,
            score,
        )
    if ok:
        st.session_state.phase = "done"
        st.rerun()
    else:
        st.error(f"Submission failed: {err}\n\nPlease refresh and try again, or contact support.")


# ════════════════════════════════════════════════════════════════════════════════
# PAGE: SUCCESS
# ════════════════════════════════════════════════════════════════════════════════
def page_done():
    st.markdown("""
    <div class="success-box">
      <div class="success-icon">✅</div>
      <div class="success-title">Assessment Complete</div>
      <p class="success-msg">
        Thank you for completing the assessment.<br>
        Your responses have been submitted successfully.
      </p>
    </div>
    """, unsafe_allow_html=True)


# ── Router ─────────────────────────────────────────────────────────────────────
phase = st.session_state.phase

if phase == "info":
    page_info()
elif phase == "assessment":
    page_assessment()
elif phase == "submitting":
    page_submitting()
elif phase == "done":
    page_done()