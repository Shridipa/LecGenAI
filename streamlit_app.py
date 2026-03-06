import streamlit as st
import os
import uuid
import time
import processor

# ─── Env Config ────────────────────────────────────────────────────────────────
os.environ["NUMBA_DISABLE_INT_CORES"] = "1"
os.environ["HF_HUB_DISABLE_SYMLINKS"] = "1"

# ─── Page Config (MUST be FIRST st.* call) ──────────────────────────────────────
st.set_page_config(
    page_title="LecGen AI · Smart Lecture Dashboard",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─── Caching (after set_page_config) ────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def process_lecture_cached(source_type, data):
    return processor.process_lecture(source_type, data)

# ─── Design System ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    /* ── Global ── */
    :root {
        --accent: #6366f1;
        --accent-end: #a855f7;
        --grad: linear-gradient(135deg, #6366f1 0%, #a855f7 100%);
        --surface: rgba(255,255,255,0.75);
        --border: rgba(200,200,230,0.35);
        --shadow: 0 8px 32px rgba(99,102,241,0.08);
        --radius-xl: 24px;
        --radius-lg: 18px;
        --radius-md: 12px;
    }

    html, body, .stApp {
        font-family: 'Inter', sans-serif !important;
        background: radial-gradient(ellipse at 70% 0%, #f0eeff 0%, #f7f8ff 50%, #eef6ff 100%) !important;
    }

    /* Hide default header */
    header[data-testid="stHeader"] { display: none; }
    .block-container { padding-top: 2.5rem; padding-bottom: 3rem; max-width: 900px; }

    /* ── Hero ── */
    .hero-wrap { text-align: center; padding: 1rem 0 2.5rem; }
    .hero-badge {
        display: inline-flex; align-items: center; gap: 8px;
        background: rgba(99,102,241,0.1); border: 1px solid rgba(99,102,241,0.2);
        border-radius: 100px; padding: 6px 18px;
        font-size: 0.82rem; font-weight: 600; color: var(--accent);
        margin-bottom: 1rem; animation: fadeIn 0.6s ease;
    }
    .hero-title {
        font-size: 3.2rem; font-weight: 800; line-height: 1.15;
        background: var(--grad); -webkit-background-clip: text;
        -webkit-text-fill-color: transparent; background-clip: text;
        margin: 0 auto 0.8rem; animation: slideDown 0.7s ease;
    }
    .hero-desc {
        font-size: 1.1rem; color: #64748b; max-width: 540px;
        margin: 0 auto 0; line-height: 1.7; animation: slideUp 0.7s ease;
    }

    /* ── Source Cards ── */
    .source-grid {
        display: grid; grid-template-columns: repeat(4, 1fr);
        gap: 14px; margin-bottom: 24px;
    }
    .source-card {
        background: var(--surface);
        backdrop-filter: blur(10px);
        border: 1.5px solid var(--border);
        border-radius: var(--radius-lg);
        padding: 22px 16px;
        cursor: pointer;
        text-align: center;
        transition: all 0.25s cubic-bezier(0.4,0,0.2,1);
        box-shadow: var(--shadow);
        animation: fadeIn 0.5s ease;
    }
    .source-card:hover {
        border-color: rgba(99,102,241,0.4);
        transform: translateY(-3px);
        box-shadow: 0 16px 40px rgba(99,102,241,0.12);
    }
    .source-card.active {
        background: var(--grad);
        border-color: transparent;
        box-shadow: 0 12px 32px rgba(99,102,241,0.3);
        transform: translateY(-3px);
    }
    .source-icon { font-size: 2rem; margin-bottom: 10px; }
    .source-label { font-size: 0.88rem; font-weight: 600; color: #374151; }
    .source-card.active .source-label { color: white; }
    .source-sub { font-size: 0.75rem; color: #9ca3af; margin-top: 4px; }
    .source-card.active .source-sub { color: rgba(255,255,255,0.75); }

    /* ── Input Panel ── */
    .input-panel {
        background: var(--surface);
        backdrop-filter: blur(12px);
        border: 1.5px solid var(--border);
        border-radius: var(--radius-xl);
        padding: 28px 32px;
        box-shadow: var(--shadow);
        margin-bottom: 24px;
        animation: fadeIn 0.4s ease;
    }
    .panel-label {
        font-size: 0.78rem; font-weight: 700;
        letter-spacing: 0.07em; text-transform: uppercase;
        color: var(--accent); margin-bottom: 12px;
    }

    /* ── Main Button ── */
    .stButton > button {
        width: 100%; border-radius: 14px;
        padding: 0.9rem 2rem;
        background: var(--grad);
        color: white !important; font-weight: 700;
        font-size: 1rem; letter-spacing: 0.3px;
        border: none;
        transition: all 0.35s cubic-bezier(0.4,0,0.2,1);
        box-shadow: 0 4px 14px rgba(99,102,241,0.25);
        margin-top: 8px;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 28px rgba(99,102,241,0.4);
    }
    .stButton > button:active { transform: translateY(0px); }

    /* ── Results Panel ── */
    .results-header {
        font-size: 1.3rem; font-weight: 700; color: #1e1b4b;
        margin: 2rem 0 1rem; display: flex; align-items: center; gap: 10px;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px; background: transparent;
        border-bottom: 2px solid rgba(99,102,241,0.1);
        padding-bottom: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: var(--radius-md); height: 42px;
        background: var(--surface);
        border: 1.5px solid var(--border) !important;
        color: #4b5563; font-weight: 600; font-size: 0.9rem;
        padding: 0 20px; transition: all 0.2s;
    }
    .stTabs [aria-selected="true"] {
        background: var(--grad) !important;
        color: white !important; border-color: transparent !important;
        box-shadow: 0 4px 12px rgba(99,102,241,0.25);
    }

    /* ── Flashcards ── */
    .flashcard {
        background: white; border-radius: var(--radius-lg);
        padding: 24px; min-height: 160px;
        border: 1.5px solid #f1f0ff;
        box-shadow: 0 4px 16px rgba(99,102,241,0.06);
        display: flex; flex-direction: column; justify-content: center;
        transition: all 0.3s;
    }
    .flashcard:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 28px rgba(99,102,241,0.12);
        border-color: rgba(99,102,241,0.2);
    }
    .fc-q { font-size: 1rem; font-weight: 700; color: #1e1b4b; }
    .fc-badge {
        display: inline-block; font-size: 0.72rem;
        background: rgba(99,102,241,0.1); color: var(--accent);
        border-radius: 6px; padding: 2px 8px;
        margin-bottom: 10px; font-weight: 600;
    }

    /* ── Divider ── */
    .section-divider {
        height: 1px; background: linear-gradient(to right, transparent, rgba(99,102,241,0.2), transparent);
        margin: 2rem 0;
    }

    /* ── Status override ── */
    .stStatusWidget { border-radius: var(--radius-lg) !important; }

    /* ── Animations ── */
    @keyframes fadeIn { from {opacity:0} to {opacity:1} }
    @keyframes slideDown {
        from {opacity:0; transform:translateY(-20px)}
        to   {opacity:1; transform:translateY(0)}
    }
    @keyframes slideUp {
        from {opacity:0; transform:translateY(16px)}
        to   {opacity:1; transform:translateY(0)}
    }
</style>
""", unsafe_allow_html=True)

# ─── Session State Init ─────────────────────────────────────────────────────────
if "active_source" not in st.session_state:
    st.session_state.active_source = "YouTube Link"

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ─── Hero Section ───────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero-wrap">
    <div class="hero-badge">🎓 Powered by Faster-Whisper + DistilBART</div>
    <h1 class="hero-title">LecGen AI</h1>
    <p class="hero-desc">Transform any lecture into transcripts, summaries, notes, quizzes &amp; flashcards — in one click.</p>
</div>
""", unsafe_allow_html=True)

# ─── Source Selector (Card Grid) ────────────────────────────────────────────────
SOURCES = [
    {"key": "YouTube Link",  "icon": "▶️",  "label": "YouTube Link",  "sub": "Paste a video URL"},
    {"key": "Upload Video",  "icon": "🎬",  "label": "Upload Video",  "sub": "MP4, MKV, AVI, MOV"},
    {"key": "Upload Audio",  "icon": "🎙️", "label": "Upload Audio",  "sub": "MP3, WAV, M4A, FLAC"},
    {"key": "Paste Text",    "icon": "📄",  "label": "Paste Text",    "sub": "Raw lecture notes"},
]

cols = st.columns(4, gap="small")
for col, src in zip(cols, SOURCES):
    with col:
        is_active = st.session_state.active_source == src["key"]
        active_cls = "active" if is_active else ""
        card_html = f"""
        <div class="source-card {active_cls}">
            <div class="source-icon">{src["icon"]}</div>
            <div class="source-label">{src["label"]}</div>
            <div class="source-sub">{src["sub"]}</div>
        </div>"""
        st.markdown(card_html, unsafe_allow_html=True)
        # Invisible button overlay to detect clicks
        if st.button(src["label"], key=f"src_{src['key']}", use_container_width=True):
            st.session_state.active_source = src["key"]
            st.rerun()

# ─── Input Panel ────────────────────────────────────────────────────────────────
active = st.session_state.active_source
icons_map = {"YouTube Link": "▶️", "Upload Video": "🎬", "Upload Audio": "🎙️", "Paste Text": "📄"}

st.markdown('<div class="input-panel">', unsafe_allow_html=True)
st.markdown(f'<div class="panel-label">{icons_map[active]}  {active} — Enter your content below</div>',
            unsafe_allow_html=True)

audio_path = None
raw_text = None

if active == "YouTube Link":
    url = st.text_input(
        label="YouTube URL",
        placeholder="https://www.youtube.com/watch?v=...",
        label_visibility="collapsed",
    )
    if url:
        if st.button("🚀 Generate Knowledge Artifacts", key="go_yt"):
            audio_path = url

elif active == "Upload Video":
    uploaded_file = st.file_uploader(
        "Drop your video file here",
        type=["mp4", "mkv", "avi", "mov"],
        label_visibility="collapsed",
    )
    if uploaded_file and st.button("🚀 Generate Knowledge Artifacts", key="go_vid"):
        audio_path = os.path.join(UPLOAD_FOLDER, f"tmp_{uuid.uuid4().hex}_{uploaded_file.name}")
        with open(audio_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

elif active == "Upload Audio":
    uploaded_file = st.file_uploader(
        "Drop your audio file here",
        type=["mp3", "wav", "m4a", "flac"],
        label_visibility="collapsed",
    )
    if uploaded_file and st.button("🚀 Generate Knowledge Artifacts", key="go_aud"):
        audio_path = os.path.join(UPLOAD_FOLDER, f"tmp_{uuid.uuid4().hex}_{uploaded_file.name}")
        with open(audio_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

elif active == "Paste Text":
    raw_text_input = st.text_area(
        "Paste lecture text",
        placeholder="The lecture begins with an overview of...",
        height=180,
        label_visibility="collapsed",
    )
    if raw_text_input and st.button("🚀 Generate Knowledge Artifacts", key="go_txt"):
        raw_text = raw_text_input

st.markdown('</div>', unsafe_allow_html=True)

# ─── Processing ─────────────────────────────────────────────────────────────────
if audio_path or raw_text:
    start_time = time.time()
    with st.status("⚡ Nitro Engine is processing your lecture...", expanded=True) as status:
        try:
            source_type = (
                "youtube" if active == "YouTube Link"
                else "upload" if active in ["Upload Video", "Upload Audio"]
                else "text"
            )
            data = audio_path if audio_path else raw_text
            result = process_lecture_cached(source_type, data)

            if result:
                st.session_state["transcript"] = result["transcript"]
                st.session_state["notes"] = result["notes"]
                st.session_state["quiz"] = result.get("quiz", [])
                st.session_state["flashcards"] = result.get("flashcards", [])

                quiz_md = ""
                for idx, item in enumerate(result["quiz"]):
                    quiz_md += f"**Q{idx+1}:** {item['question']}  \n"
                    quiz_md += f"**A:** {item['correct']}  \n"
                    if "explanation" in item:
                        quiz_md += f"*{item['explanation']}*\n\n"
                st.session_state["quiz_md"] = quiz_md

                elapsed = time.time() - start_time
                status.update(label=f"✅ Done in {elapsed:.1f}s — results ready below!", state="complete")
            else:
                st.error("Processing returned no result. Please try again.")
        except Exception as e:
            st.error(f"An error occurred: {e}")

# ─── Results ────────────────────────────────────────────────────────────────────
if "transcript" in st.session_state:
    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="results-header">📋 Knowledge Artifacts</div>', unsafe_allow_html=True)

    t1, t2, t3, t4 = st.tabs([
        "📝 Transcript", "🗒️ Notes", "❓ Quiz", "🗂️ Flashcards"
    ])

    with t1:
        st.caption("Full transcript extracted from the lecture audio.")
        st.text_area(
            "transcript",
            st.session_state["transcript"],
            height=380,
            label_visibility="collapsed",
        )

    with t2:
        st.markdown(st.session_state["notes"])

    with t3:
        st.markdown("#### Self-Assessment Quiz")
        st.markdown(st.session_state.get("quiz_md", "_No quiz generated._"))

    with t4:
        st.markdown("#### Digital Flashcards")
        cards = st.session_state.get("flashcards", [])
        if cards:
            card_cols = st.columns(3)
            for i, card in enumerate(cards):
                with card_cols[i % 3]:
                    st.markdown(f"""
                    <div class="flashcard">
                        <span class="fc-badge">🃏 Card {i+1}</span>
                        <div class="fc-q">{card['front']}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    with st.expander("Show Answer"):
                        st.info(card["back"])
        else:
            st.markdown("_No flashcards generated._")
