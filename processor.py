"""
processor.py — Groq-accelerated lecture processing engine.
Transcription: Groq Whisper API (whisper-large-v3-turbo)
LLM Tasks:     Groq LLaMA 3 (llama-3.1-8b-instant) for notes, quiz, flashcards
"""

import os
import uuid
import subprocess
import sys

from dotenv import load_dotenv
load_dotenv()

# Windows Unicode Terminal Stability
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from groq import Groq

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY)

# ── Model Config ────────────────────────────────────────────────────────────────
TRANSCRIPTION_MODEL = "whisper-large-v3-turbo"   # Fastest Groq Whisper
LLM_MODEL           = "llama-3.1-8b-instant"      # Ultra-fast Groq LLaMA

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)


# ── Helpers ─────────────────────────────────────────────────────────────────────
def _llm(prompt: str, system: str = "You are an expert AI educational assistant.", max_tokens: int = 4096) -> str:
    """Single LLM call to Groq with error handling."""
    try:
        resp = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": system},
                {"role": "user",   "content": prompt},
            ],
            temperature=0.3,
            max_tokens=max_tokens,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        print(f"Groq LLM error: {e}")
        return ""


def inject_ffmpeg():
    import shutil
    ffmpeg_path = shutil.which("ffmpeg")
    if ffmpeg_path:
        return os.path.dirname(ffmpeg_path)
    for p in ["C:\\ffmpeg\\bin", "C:\\ffmpeg", os.path.expanduser("~\\Downloads\\ffmpeg\\bin")]:
        if os.path.exists(os.path.join(p, "ffmpeg.exe")):
            if p not in os.environ.get("PATH", ""):
                os.environ["PATH"] = p + os.pathsep + os.environ.get("PATH", "")
            return p
    return None

FFMPEG_PATH = inject_ffmpeg()


# ── Transcription ────────────────────────────────────────────────────────────────
def transcribe_audio(audio_path: str) -> str:
    """Transcribe using Groq Whisper API — fastest path."""
    try:
        # Read bytes into memory first — prevents 'I/O on closed file' error
        # because the Groq SDK may read the file handle lazily after the with-block exits.
        with open(audio_path, "rb") as f:
            audio_bytes = f.read()

        filename = os.path.basename(audio_path)
        resp = client.audio.transcriptions.create(
            model=TRANSCRIPTION_MODEL,
            file=(filename, audio_bytes),
            response_format="text",
        )
        return resp if isinstance(resp, str) else resp.text
    except Exception as e:
        print(f"Groq transcription error: {e}")
        return ""


# ── YouTube Download ─────────────────────────────────────────────────────────────
def handle_youtube(url: str) -> str | None:
    import yt_dlp
    uid = str(uuid.uuid4())[:8]
    out_tmpl = os.path.join(UPLOAD_FOLDER, f"yt_{uid}.%(ext)s")
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": out_tmpl,
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "96",   # Lower bitrate = smaller file = faster upload to Groq
        }],
        "quiet": True, "no_warnings": True, "nocheckcertificate": True,
        "http_headers": {"User-Agent": "Mozilla/5.0"},
    }
    if FFMPEG_PATH:
        ydl_opts["ffmpeg_location"] = FFMPEG_PATH
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        expected = os.path.join(UPLOAD_FOLDER, f"yt_{uid}.mp3")
        return expected if os.path.exists(expected) else None
    except Exception as e:
        print(f"yt-dlp error: {e}")
        return None


def extract_audio(video_path: str, out_audio: str = "lecture.mp3") -> str:
    dest = os.path.join(UPLOAD_FOLDER, out_audio)
    cmd = ["ffmpeg", "-y", "-i", video_path, "-vn", "-acodec", "libmp3lame", "-ab", "96k", "-ar", "22050", dest]
    subprocess.run(cmd, capture_output=True, check=False)
    return dest


# ── LLM-Powered Analysis ─────────────────────────────────────────────────────────
def generate_notes(transcript: str) -> str:
    if not transcript:
        return ""
    prompt = f"""Generate extremely concise, bullet-point only lecture notes from this transcript.
Mimic the style of an extractive summarizer (like DistilBART).
Start directly with "## 📌 Key Notes".
Each bullet point should be 1-2 sentences maximum, starting with "  • ".
Do not include conversational filler.

**Transcript:**
{transcript[:8000]}"""
    return _llm(prompt, max_tokens=1000)


def generate_quiz(transcript: str) -> list[dict]:
    if not transcript:
        return []
    prompt = f"""Based on this transcript, generate 5 short-answer quiz questions.
Mimic the style of a T5 Question Generator and TinyRoBERTa model.
- Questions should be very direct.
- Answers must be extremely short (1-5 words if possible).
- The explanation must be exactly in this format: "AI verified answer: [answer]"

Return exactly as a JSON array, no markdown fences:
[
  {{"id":1, "type":"short", "question":"...", "correct":"...", "explanation":"AI verified answer: ..."}},
  ...
]

Transcript:
{transcript[:6000]}"""
    raw = _llm(prompt, max_tokens=1500)
    try:
        import json, re
        match = re.search(r'\[.*\]', raw, re.DOTALL)
        if match:
            return json.loads(match.group())
    except Exception as e:
        print(f"Quiz parse error: {e}")
    # Fallback to guarantee at least one question (matching old behavior)
    return [{"id": 1, "type": "short", "question": "What is the primary topic of the lecture?", "correct": "The main topic discussed.", "explanation": "Fallback verification"}]


def generate_flashcards(transcript: str) -> list[dict]:
    # The user's old logic passed QA data directly to flashcards.
    # We will generate extremely short term/definition pairs.
    if not transcript:
        return []
    prompt = f"""From this lecture transcript, create 10 flashcards.
They must be extremely brief.
Front: A single term or short question.
Back: A 1-2 chunk factual answer.

Return exactly as a JSON array, no markdown fences:
[
  {{"front":"...", "back":"..."}},
  ...
]

Transcript:
{transcript[:6000]}"""
    raw = _llm(prompt, max_tokens=1500)
    try:
        import json, re
        match = re.search(r'\[.*\]', raw, re.DOTALL)
        if match:
            return json.loads(match.group())
    except Exception as e:
        print(f"Flashcard parse error: {e}")
    return []


# ── Main Pipeline ────────────────────────────────────────────────────────────────
def process_lecture(source_type: str, data: str, target_lang: str = "en") -> dict | None:
    audio_path = None
    transcript = None

    # 1. Resolve source → audio or text
    if source_type == "youtube":
        audio_path = handle_youtube(data)
    elif source_type in ["upload", "video", "audio"]:
        if data.lower().endswith((".mp4", ".avi", ".mov", ".mkv")):
            audio_path = extract_audio(data, out_audio=f"uploaded_{uuid.uuid4().hex}.mp3")
        else:
            audio_path = data
    elif source_type == "text":
        transcript = data
    elif source_type == "text_file":
        with open(data, "r", encoding="utf-8") as f:
            transcript = f.read()

    # 2. Transcribe with Groq Whisper (fast cloud API)
    if audio_path and not transcript:
        print(f"Transcribing with Groq Whisper ({TRANSCRIPTION_MODEL})...")
        transcript = transcribe_audio(audio_path)

    if not transcript:
        return None

    print(f"Transcript ready ({len(transcript.split())} words). Running Groq LLM tasks in parallel...")

    # 3. Run all LLM tasks in parallel via threads
    import concurrent.futures
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:
        f_notes      = ex.submit(generate_notes, transcript)
        f_quiz       = ex.submit(generate_quiz, transcript)
        f_flashcards = ex.submit(generate_flashcards, transcript)

        notes      = f_notes.result(timeout=60)      or "• Notes unavailable."
        quiz_data  = f_quiz.result(timeout=60)       or []
        flashcards = f_flashcards.result(timeout=60) or []

    return {
        "transcript":  transcript,
        "notes":       notes,
        "qa":          [{"question": q["question"], "answer": q["correct"], "type": "short"} for q in quiz_data],
        "quiz":        quiz_data if quiz_data else [{"id":1,"question":"No quiz generated","correct":"Retry","explanation":"N/A"}],
        "flashcards":  flashcards if flashcards else [{"front":"Retry","back":"No cards generated"}],
        "language":    "en",
    }
