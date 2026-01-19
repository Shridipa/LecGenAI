import os
import subprocess
from pydub import AudioSegment
import whisper
import nltk
from transformers import pipeline
from jiwer import wer
from rouge_score import rouge_scorer
from bert_score import score
import torch

try:
    from static_ffmpeg import run as ffmpeg_run
    FFMPEG_EXE, FFPROBE_EXE = ffmpeg_run.get_or_fetch_platform_executables_else_raise()
    FFMPEG_PATH = os.path.dirname(FFMPEG_EXE)
except ImportError:
    FFMPEG_PATH = None

potential_paths = []
if FFMPEG_PATH: potential_paths.append(FFMPEG_PATH)
user_download_ffmpeg = r"C:\Users\KIIT\Downloads\ffmpeg-8.0.1-essentials_build\bin"
if os.path.exists(user_download_ffmpeg): potential_paths.append(user_download_ffmpeg)

for p in potential_paths:
    if p not in os.environ["PATH"]:
        os.environ["PATH"] = p + os.pathsep + os.environ["PATH"]

nltk.download("punkt")
folder = "outputs"
os.makedirs(folder, exist_ok=True)

device = 0 if torch.cuda.is_available() else -1

def handle_youtube(url):
    cmd = ["yt-dlp", "-x", "--audio-format", "mp3", "-o", "%(title)s.%(ext)s"]
    if FFMPEG_PATH:
        cmd.extend(["--ffmpeg-location", FFMPEG_PATH])
    cmd.append(url)
    print("Downloading from YouTube...")
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError("yt-dlp error:\n" + r.stderr)
    for f in os.listdir():
        if f.endswith(".mp3"):
            return f
    raise FileNotFoundError("MP3 not found after download.")

def handle_uploaded_video(filename, out_audio="lecture.mp3"):
    print(f"Extracting audio from {filename}...")
    video = AudioSegment.from_file(filename)
    video.export(out_audio, format="mp3")
    return out_audio

def handle_uploaded_audio(filename):
    print(f"Using audio file: {filename}")
    return filename

def transcribe_audio(audio_path):
    print("🔎 Transcribing audio...")
    model = whisper.load_model("base")
    result = model.transcribe(audio_path)
    return result["text"]

def summarize_text(transcript):
    summarizer_led = pipeline(
        "summarization",
        model="allenai/led-large-16384",
        tokenizer="allenai/led-large-16384",
        device=device
    )
    summary = summarizer_led(transcript, max_length=256, min_length=80, do_sample=False)[0]["summary_text"]
    return summary

summarizer_bart = pipeline("summarization", model="facebook/bart-large-cnn", device=device)
quiz_generator = pipeline("text2text-generation", model="valhalla/t5-small-qa-qg-hl", device=device)
flashcard_generator = pipeline("question-answering", model="distilbert-base-uncased-distilled-squad", device=device)

def generate_notes(transcript):
    words = transcript.split()
    chunks = [" ".join(words[i:i+800]) for i in range(0, len(words), 800)]
    summaries = []
    for chunk in chunks:
        try:
            s = summarizer_bart(chunk, max_length=200, min_length=50, do_sample=False)[0]["summary_text"]
            summaries.append(s)
        except Exception as e:
            print("⚠️ Skipped a chunk:", e)
    return "\n".join([f"- {s}" for s in summaries])

def generate_quiz(transcript):
    words = transcript.split()
    chunks = [" ".join(words[i:i+800]) for i in range(0, len(words), 800)]
    quizzes = []
    for chunk in chunks[:2]:
        q = quiz_generator(chunk, max_length=256)[0]["generated_text"]
        quizzes.append(q)
    return "\n".join(quizzes)

def generate_flashcards(transcript):
    words = transcript.split()
    chunks = [" ".join(words[i:i+800]) for i in range(0, len(words), 800)]
    cards = []
    for chunk in chunks[:3]:
        question = "What is a key concept in this section?"
        answer = flashcard_generator(question=question, context=chunk)["answer"]
        cards.append(f"Front: {question}\nBack: {answer}")
    return "\n\n".join(cards)

def evaluate(reference_transcript, reference_summary, transcript, summary):
    results = []
    if reference_transcript.strip():
        wer_score = wer(reference_transcript, transcript)
        results.append(f"WER: {wer_score}")
    else:
        results.append("WER: skipped (no reference transcript provided)")
    if reference_summary.strip():
        scorer = rouge_scorer.RougeScorer(['rougeL'], use_stemmer=True)
        rouge_scores = scorer.score(reference_summary, summary)
        results.append(f"ROUGE-L: {rouge_scores}")
        P, R, F1 = score([summary], [reference_summary], lang="en")
        results.append(f"BERTScore F1: {F1.mean().item()}")
    else:
        results.append("ROUGE-L: skipped (no reference summary provided)")
        results.append("BERTScore: skipped (no reference summary provided)")
    return "\n".join(results)

print("Choose input type:")
print("1. Paste YouTube link")
print("2. Provide path to recorded video lecture")
print("3. Provide path to recorded audio lecture")
choice = input("Enter 1, 2, or 3: ").strip()

if choice == "1":
    url = input("Paste YouTube link: ").strip()
    audio_path = handle_youtube(url)
elif choice == "2":
    filename = input("Enter path to your video file: ").strip()
    audio_path = handle_uploaded_video(filename)
elif choice == "3":
    filename = input("Enter path to your audio file: ").strip()
    audio_path = handle_uploaded_audio(filename)
else:
    raise ValueError("Invalid choice.")

print("🎵 Audio ready at:", audio_path)
transcript = transcribe_audio(audio_path)

with open(f"{folder}/transcript.txt", "w", encoding="utf-8") as f:
    f.write(transcript)

summary = summarize_text(transcript)
with open(f"{folder}/summary.txt", "w", encoding="utf-8") as f:
    f.write(summary)

notes = generate_notes(transcript)
quiz = generate_quiz(transcript)
flashcards = generate_flashcards(transcript)

with open(f"{folder}/notes.txt", "w", encoding="utf-8") as f: f.write(notes)
with open(f"{folder}/quiz.txt", "w", encoding="utf-8") as f: f.write(quiz)
with open(f"{folder}/flashcards.txt", "w", encoding="utf-8") as f: f.write(flashcards)

results = evaluate("", "", transcript, summary)
with open(f"{folder}/evaluation_results.txt", "w", encoding="utf-8") as f:
    f.write(results)

print("✅ Transcript, summary, notes, quiz, flashcards, and evaluation saved in:", folder)
