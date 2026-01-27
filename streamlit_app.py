import streamlit as st
import os
import subprocess
import sys
import torch
import uuid
import time
from threading import Lock

# Compat for Python 3.13+ which removed audioop
if sys.version_info >= (3, 13):
    try:
        import audioop # noqa: F401
    except ImportError:
        try:
            import pyaudioop as audioop # noqa: F401
            sys.modules["audioop"] = audioop
        except ImportError:
            pass

# DEBUG: Check environment
print(f"Python Version: {sys.version}")
print(f"Torch Version: {torch.__version__}")
print(f"Torch Cuda Available: {torch.cuda.is_available()}")

def inject_ffmpeg():
    potential_paths = []
    
    try:
        from static_ffmpeg import run as ffmpeg_run
        ffmpeg_exe, _ = ffmpeg_run.get_or_fetch_platform_executables_else_raise()
        potential_paths.append(os.path.dirname(ffmpeg_exe))
    except Exception:
        pass

    user_home = os.path.expanduser("~")
    search_roots = [os.path.join(user_home, "Downloads"), "C:\\Program Files", "C:\\ffmpeg"]
    
    for root in search_roots:
        if os.path.exists(root):
            for dirpath, dirnames, filenames in os.walk(root):
                if "ffmpeg.exe" in filenames:
                    potential_paths.append(dirpath)
                    break
                if dirpath.count(os.sep) - root.count(os.sep) > 2:
                    break

    found = False
    for p in potential_paths:
        if p and os.path.exists(os.path.join(p, "ffmpeg.exe")):
            if p not in os.environ["PATH"]:
                os.environ["PATH"] = p + os.pathsep + os.environ["PATH"]
            found = True
            print(f"✅ FFmpeg injected from: {p}")
    
    return found

FFMPEG_FOUND = inject_ffmpeg()
FFMPEG_PATH = next((p for p in os.environ["PATH"].split(os.pathsep) if os.path.exists(os.path.join(p, "ffmpeg.exe"))), None)

# Import pydub AFTER injecting ffmpeg path
from pydub import AudioSegment
import whisper
import nltk
from transformers import pipeline, AutoModelForSeq2SeqLM, AutoTokenizer, AutoModelForQuestionAnswering


st.set_page_config(
    page_title="LecGen AI - Smart Lecture Assistant",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .main {
        background-color: #f8f9fa;
    }
    .stButton>button {
        width: 100%;
        border-radius: 10px;
        height: 3em;
        background-color: #4F46E5;
        color: white;
        font-weight: bold;
        border: none;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #4338CA;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(79, 70, 229, 0.3);
    }
    .stTextInput>div>div>input {
        border-radius: 10px;
    }
    .stTextArea>div>div>textarea {
        border-radius: 10px;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 20px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #ffffff;
        border-radius: 10px 10px 0 0;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #EEF2FF !important;
        border-bottom: 2px solid #4F46E5 !important;
    }
    .flashcard {
        padding: 20px;
        background-color: white;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
        margin-bottom: 20px;
        border: 1px solid #e5e7eb;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def download_nltk():
    try:
        nltk.download("punkt", quiet=True)
        nltk.download("punkt_tab", quiet=True)
    except Exception:
        pass

download_nltk()

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

device = 0 if torch.cuda.is_available() else -1

@st.cache_resource
def get_whisper_model(model_name='base'):
    return whisper.load_model(model_name)

def _create_summarizer(model_name):
    kwargs = {"device": device} if device == 0 else {}
    if device == 0:
        kwargs["torch_dtype"] = torch.float16
        
    try:
        return pipeline("summarization", model=model_name, framework="pt", **kwargs)
    except Exception as e:
        print(f"⚠️ Pipeline creation failed for {model_name}: {e}. Falling back to manual loading.")
        try:
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
            if device == 0:
                model = model.to(device).half()
                
            def manual_summ(text, **gen_kwargs):
                # Defaults
                if "max_length" not in gen_kwargs: gen_kwargs["max_length"] = 150
                if "min_length" not in gen_kwargs: gen_kwargs["min_length"] = 40
                if "do_sample" not in gen_kwargs: gen_kwargs["do_sample"] = False
                
                inputs = tokenizer(text, return_tensors="pt", max_length=1024, truncation=True).to(model.device)
                summary_ids = model.generate(inputs["input_ids"], **gen_kwargs)
                summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True)
                return [{"summary_text": summary}]
                
            return manual_summ
        except Exception as e2:
            st.error(f"Critical error loading {model_name}: {e2}")
            return None

@st.cache_resource
def get_summarizer():
    return _create_summarizer("facebook/bart-large-cnn")

@st.cache_resource
def get_notes_summarizer():
    return _create_summarizer("philschmid/bart-large-cnn-samsum")

@st.cache_resource
def get_qg_generator():
    model_name = "valhalla/t5-base-e2e-qg"
    kwargs = {"device": device} if device == 0 else {}
    if device == 0:
        kwargs["torch_dtype"] = torch.float16
    
    try:
        return pipeline("text2text-generation", model=model_name, framework="pt", **kwargs)
    except Exception as e:
        print(f"⚠️ Pipeline failed for QG: {e}. Fallback to manual.")
        try:
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
            if device == 0:
                model = model.to(device).half()
                
            def manual_qg(text, **gen_kwargs):
                inputs = tokenizer(text, return_tensors="pt", max_length=512, truncation=True).to(model.device)
                out = model.generate(inputs["input_ids"], **gen_kwargs)
                decoded = tokenizer.decode(out[0], skip_special_tokens=True)
                return [{"generated_text": decoded}]
            return manual_qg
        except Exception as e2:
            st.error(f"Failed to load QG model: {e2}")
            return None

@st.cache_resource
def get_qa_answerer():
    model_name = "deepset/roberta-base-squad2"
    kwargs = {"device": device} if device == 0 else {}
    if device == 0:
        kwargs["torch_dtype"] = torch.float16
        
    try:
        return pipeline("question-answering", model=model_name, framework="pt", **kwargs)
    except Exception as e:
        print(f"⚠️ Pipeline failed for QA: {e}. Fallback to manual.")
        try:
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            model = AutoModelForQuestionAnswering.from_pretrained(model_name)
            if device == 0:
                model = model.to(device).half()
                
            def manual_qa(question=None, context=None, **kwargs):
                if not question or not context: return {'score': 0, 'answer': ''}
                inputs = tokenizer(question, context, return_tensors="pt", truncation=True, max_length=512).to(model.device)
                with torch.no_grad():
                    outputs = model(**inputs)
                
                # Get best span
                start_scores = torch.softmax(outputs.start_logits, dim=1)
                end_scores = torch.softmax(outputs.end_logits, dim=1)
                
                start_idx = torch.argmax(start_scores)
                end_idx = torch.argmax(end_scores)
                
                score = (start_scores[0][start_idx] * end_scores[0][end_idx]).item()
                
                # Check for invalid span
                if end_idx < start_idx:
                    return {'score': score, 'answer': ''}
                    
                tokens = inputs.input_ids[0][start_idx : end_idx + 1]
                answer = tokenizer.decode(tokens, skip_special_tokens=True)
                return {'score': score, 'answer': answer}
            return manual_qa
        except Exception as e2:
            st.error(f"Failed to load QA model: {e2}")
            return None

def handle_youtube(url):
    uid = str(uuid.uuid4())[:8]
    out_tmpl = os.path.join(UPLOAD_FOLDER, f"yt_{uid}.%(ext)s")
    cmd = ["yt-dlp", "-x", "--audio-format", "mp3", "-o", out_tmpl]
    if FFMPEG_PATH:
        cmd.extend(["--ffmpeg-location", FFMPEG_PATH])
    cmd.append(url)
    
    with st.status(f"Downloading from YouTube...", expanded=True) as status:
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            st.error(f"yt-dlp error: {r.stderr}")
            return None
        
        expected_file = os.path.join(UPLOAD_FOLDER, f"yt_{uid}.mp3")
        if os.path.exists(expected_file):
            status.update(label="Download complete!", state="complete", expanded=False)
            return expected_file
            
        for f in os.listdir(UPLOAD_FOLDER):
            if f.startswith(f"yt_{uid}") and f.endswith(".mp3"):
                status.update(label="Download complete!", state="complete", expanded=False)
                return os.path.join(UPLOAD_FOLDER, f)
    
    st.error("MP3 not found after download.")
    return None

def handle_uploaded_video(file, out_audio="lecture.mp3"):
    temp_video = os.path.join(UPLOAD_FOLDER, f"temp_{uuid.uuid4().hex}_{file.name}")
    with open(temp_video, "wb") as f:
        f.write(file.getbuffer())
    
    st.info(f"Extracting audio from {file.name}...")
    video = AudioSegment.from_file(temp_video)
    dest_audio = os.path.join(UPLOAD_FOLDER, out_audio)
    video.export(dest_audio, format="mp3")
    return dest_audio

def chunk_text_by_sentences(text, max_chars=1000):
    sentences = nltk.sent_tokenize(text)
    chunks, current = [], ""
    for s in sentences:
        if len(current) + len(s) + 1 <= max_chars:
            current = (current + " " + s).strip()
        else:
            if current:
                chunks.append(current)
            current = s
    if current:
        chunks.append(current)
    return chunks

def chunk_text_by_words(text, words_per_chunk=300):
    words = text.split()
    return [" ".join(words[i:i+words_per_chunk]) for i in range(0, len(words), words_per_chunk)]

def summarize_text(transcript):
    chunks = chunk_text_by_sentences(transcript, max_chars=1024)
    if not chunks: return ""
    
    summarizer = get_summarizer()
    summaries = []
    for ch in chunks:
        # Dynamic length adjustment for short text
        input_len = len(ch.split())
        curr_max = min(250, int(input_len * 0.8))
        curr_min = min(80, int(input_len * 0.2))
        
        # Ensure min < max
        if curr_max <= curr_min:
            curr_max = input_len
            curr_min = 10 if input_len > 10 else 1
            
        try:
            out = summarizer(ch, max_length=curr_max, min_length=curr_min, do_sample=False)
            summaries.append(out[0]["summary_text"])
        except Exception:
            # Fallback for extremely short text
            summaries.append(ch[:200] + "...")
            
    return "\n".join(f"- {s}" for s in summaries)

def generate_notes(transcript):
    chunks = chunk_text_by_sentences(transcript, max_chars=900)
    if not chunks: return ""
    summarizer = get_notes_summarizer()
    notes = []
    for ch in chunks:
        input_len = len(ch.split())
        curr_max = min(128, int(input_len * 0.8))
        curr_min = min(40, int(input_len * 0.2))
        
        if curr_max <= curr_min:
            curr_max = input_len
            curr_min = 5 if input_len > 5 else 1
            
        try:
            out = summarizer(ch, max_length=curr_max, min_length=curr_min, do_sample=False)
            notes.append(out[0]["summary_text"])
        except Exception:
            notes.append(ch[:150] + "...")
            
    return "\n".join(f"- {n}" for n in notes)

def generate_quiz(transcript, max_questions=8):
    words = transcript.split()
    total_words = len(words)
    if total_words < 50: return "Transcript too short for quiz."
    
    num_chunks = 4
    chunk_size = 350
    chunks = []
    
    indices = [0, total_words // 3, (2 * total_words) // 3, max(0, total_words - chunk_size)]
    for idx in sorted(list(set(indices))):
        chunk = " ".join(words[idx : idx + chunk_size])
        if chunk: chunks.append(chunk)

    questions = []
    qg = get_qg_generator()
    
    with st.status("Thinking about questions...", expanded=False):
        for chunk in chunks:
            try:
                res = qg(f"generate questions: {chunk}", max_length=256, do_sample=False)
                out = res[0]["generated_text"]
                raw_qs = out.split("<sep>") if "<sep>" in out else out.split("?")
                for q in raw_qs:
                    q = q.strip()
                    if q and not q.endswith("?"): q += "?"
                    if len(q.split()) > 4:
                        questions.append((q, chunk))
                    if len(questions) >= max_questions: break
            except Exception:
                continue
            if len(questions) >= max_questions: break

    if not questions:
        return "Couldn't generate specific questions. Try a longer lecture."

    answers = []
    qa_pipeline = get_qa_answerer()
    
    for q_text, context in questions:
        try:
            res = qa_pipeline(question=q_text, context=context)
            if res['score'] > 0.05:
                answers.append((q_text, res['answer']))
        except Exception:
            answers.append((q_text, "Refer to the transcript for details."))

    return "\n".join(f"**Q{i+1}:** {q}  \n**A{i+1}:** {a}\n" for i, (q, a) in enumerate(answers))

def generate_flashcards(transcript, cards_per_section=3, max_cards_total=9):
    words = transcript.split()
    total_words = len(words)
    if total_words < 60: return []
    
    chunk_size = 400
    indices = [0, total_words // 2, max(0, total_words - chunk_size)]
    chunks = [" ".join(words[idx : idx + chunk_size]) for idx in indices]
    
    cards = []
    qg = get_qg_generator()
    qa = get_qa_answerer()
    
    for chunk in chunks:
        try:
            res = qg(f"generate questions: {chunk}", max_length=256, do_sample=True, top_p=0.9)
            raw_out = res[0]["generated_text"]
            raw_qs = raw_out.split("<sep>") if "<sep>" in raw_out else raw_out.split("?")
            
            section_qs = []
            for q in raw_qs:
                q = q.strip()
                if q and len(q.split()) > 5:
                    if not q.endswith("?"): q += "?"
                    section_qs.append(q)
                if len(section_qs) >= cards_per_section: break
            
            for q_text in section_qs:
                ans_res = qa(question=q_text, context=chunk)
                if ans_res['score'] > 0.03:
                    cards.append({"front": q_text, "back": ans_res['answer']})
                if len(cards) >= max_cards_total: break
        except Exception:
            continue
        if len(cards) >= max_cards_total: break

    return cards

st.title("🎓 LecGen AI")
st.markdown("### Intelligent Lecture Summarizer & Study Material Generator")

with st.sidebar:
    st.markdown("### 🎓 LecGen AI")
    st.write("Transforming your lecture recordings into structured study materials using state-of-the-art AI.")
    st.divider()
    st.markdown("### 🛠️ Features")
    st.write("- Smart Summarization")
    st.write("- Structured Notes")
    st.write("- AI-Powered Quizzes")
    st.write("- Active Recall Flashcards")

input_type = st.radio("Select Input Source:", ["YouTube Link", "Upload Video", "Upload Audio", "Paste Text"], horizontal=True)

audio_path = None
raw_text = None

if input_type == "YouTube Link":
    url = st.text_input("Paste YouTube URL:", placeholder="https://www.youtube.com/watch?v=...")
    if url:
        if st.button("🚀 Start Generation"):
            audio_path = handle_youtube(url)

elif input_type == "Upload Video":
    uploaded_file = st.file_uploader("Upload Video Lecture:", type=["mp4", "mkv", "avi", "mov"])
    if uploaded_file:
        if st.button("🚀 Start Generation"):
            audio_path = handle_uploaded_video(uploaded_file, out_audio=f"uploaded_{uuid.uuid4().hex}.mp3")

elif input_type == "Upload Audio":
    uploaded_file = st.file_uploader("Upload Audio Lecture:", type=["mp3", "wav", "m4a", "flac"])
    if uploaded_file:
        if st.button("🚀 Start Generation"):
            audio_path = os.path.join(UPLOAD_FOLDER, f"uploaded_{uuid.uuid4().hex}_{uploaded_file.name}")
            with open(audio_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

elif input_type == "Paste Text":
    raw_text = st.text_area("Paste Transcript Text:", height=300)
    if raw_text:
        if st.button("🚀 Start Generation"):
            pass

if audio_path or raw_text:
    start_time = time.time()
    with st.status("⏳ Initializing AI Models...", expanded=True) as status:
        if audio_path:
            status.update(label="🔎 Transcribing audio (using OpenAI Whisper)...")
            model = get_whisper_model("base")
            result = model.transcribe(audio_path)
            transcript = result["text"]
        else:
            transcript = raw_text

        st.session_state['transcript'] = transcript
        
        status.update(label="📊 Generating Summary (BART-Large)...")
        summary = summarize_text(transcript)
        st.session_state['summary'] = summary
        
        status.update(label="🗒️ Structuring Notes...")
        notes = generate_notes(transcript)
        st.session_state['notes'] = notes
        
        status.update(label="❓ Crafting Quiz Questions...")
        quiz = generate_quiz(transcript)
        st.session_state['quiz'] = quiz
        
        status.update(label="🗂️ Creating Active Recall Flashcards...")
        flashcards = generate_flashcards(transcript)
        st.session_state['flashcards'] = flashcards
        
        end_time = time.time()
        elapsed = end_time - start_time
        status.update(label=f"✅ Completed in {elapsed:.1f}s!", state="complete", expanded=False)
        st.success(f"Processing complete! Total time: **{elapsed:.1f} seconds**.")

if 'transcript' in st.session_state:
    st.divider()
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📝 Transcript", "📊 Summary", "🗒️ Notes", "❓ Quiz", "🗂️ Flashcards"])
    
    with tab1:
        st.text_area("Transcript", st.session_state['transcript'], height=400)
        st.download_button("Download Transcript", st.session_state['transcript'], file_name="transcript.txt")
        
    with tab2:
        st.markdown(st.session_state['summary'])
        st.download_button("Download Summary", st.session_state['summary'], file_name="summary.txt")

    with tab3:
        st.markdown(st.session_state['notes'])
        st.download_button("Download Notes", st.session_state['notes'], file_name="notes.txt")

    with tab4:
        st.markdown(st.session_state['quiz'])
        st.download_button("Download Quiz", st.session_state['quiz'], file_name="quiz.txt")

    with tab5:
        flashcards = st.session_state['flashcards']
        if flashcards:
            cols = st.columns(3)
            for i, card in enumerate(flashcards):
                with cols[i % 3]:
                    st.markdown(f"""
                    <div class="flashcard">
                        <div style="font-size: 0.9em; color: #6B7280; margin-bottom: 5px;">Flashcard {i+1}</div>
                        <div style="font-weight: bold; margin-bottom: 15px;">{card['front']}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    with st.expander("Show Answer"):
                        st.markdown(f"**Answer:** {card['back']}")
        else:
            st.write("No flashcards generated.")

else:
    st.info("Provide an input to start generating study materials.")

st.divider()
st.markdown(
    "<div style='text-align: center; color: #888; font-size: 0.8em;'>"
    "Built with ❤️ using Streamlit & Hugging Face Transformers"
    "</div>",
    unsafe_allow_html=True
)
