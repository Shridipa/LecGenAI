import os
import subprocess
import uuid
import torch
import nltk
import random
from threading import Lock
from pydub import AudioSegment
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor
# from faster_whisper import WhisperModel  # Moved to lazy load

# from transformers import pipeline, AutoModelForSeq2SeqLM, AutoTokenizer, AutoModelForQuestionAnswering # Moved to lazy load


# Ultra-optimized worker pool (2-3 is better for heavy models on CPU to avoid thrashing)
_executor = ThreadPoolExecutor(max_workers=3 if torch.cuda.is_available() else 2)

def translate_text(text, target_lang):
    if not text or target_lang == 'en': return text
    
    # Upgraded to NLLB-200 for high-fidelity academic translation
    NLLB_LANG_MAP = {
        'es': 'spa_Latn', 'fr': 'fra_Latn', 'de': 'deu_Latn',
        'hi': 'hin_Deva', 'zh': 'zho_Hans', 'ar': 'arb_Arab',
        'pt': 'por_Latn', 'ru': 'rus_Cyrl', 'ja': 'jpn_Jpan',
        'ko': 'kor_Hang', 'it': 'ita_Latn', 'bn': 'ben_Beng',
    }
    nllb_target = NLLB_LANG_MAP.get(target_lang)
    
    if nllb_target:
        try:
            from transformers import pipeline as hf_pipeline
            if 'translator' not in _models:
                print("Loading NLLB-200 translation model...")
                _models['translator'] = hf_pipeline(
                    "translation",
                    model="facebook/nllb-200-distilled-600M",
                    src_lang="eng_Latn",
                    tgt_lang=nllb_target,
                    device=device
                )
            else:
                # Update target lang on existing pipeline
                _models['translator'].tokenizer.src_lang = "eng_Latn"
                _models['translator'].task_specific_params = {"translation": {"tgt_lang": nllb_target}}
            
            # Chunk long texts to avoid token limit
            if len(text) > 1000:
                chunks = chunk_text(text, max_chars=800)
                translated_chunks = []
                for c in chunks:
                    result = _models['translator'](c, tgt_lang=nllb_target, max_length=512)
                    translated_chunks.append(result[0]['translation_text'])
                return " ".join(translated_chunks)
            
            result = _models['translator'](text, tgt_lang=nllb_target, max_length=512)
            return result[0]['translation_text']
        except Exception as e:
            print(f"NLLB translation error: {e}, falling back to Google Translate")
    
    # Fallback to cloud Google Translate for unsupported or on error
    try:
        from deep_translator import GoogleTranslator
        translator = GoogleTranslator(source='auto', target=target_lang)
        if len(text) > 4500:
            chunks = chunk_text(text, max_chars=4000)
            return " ".join([translator.translate(c) for c in chunks])
        return translator.translate(text)
    except Exception as e:
        print(f"Translation error: {e}")
        return text

# Download NLTK data
try:
    nltk.download("punkt", quiet=True)
    nltk.download("punkt_tab", quiet=True)
except Exception:
    pass


UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

device = 0 if torch.cuda.is_available() else -1
device_type = "cuda" if torch.cuda.is_available() else "cpu"
compute_type = "float16" if torch.cuda.is_available() else "int8"

# Models cache
_models = {}
_warmup_lock = Lock()

def get_whisper_model(model_name='large-v2'):  # Upgraded to large-v2 for best accuracy
    if 'whisper' not in _models:
        from faster_whisper import WhisperModel
        print(f"Loading faster-whisper model: {model_name} on {device_type} with {compute_type}...")
        _models['whisper'] = WhisperModel(model_name, device=device_type, compute_type=compute_type)
    return _models['whisper']

def _warmup_all_models():
    """Pre-load all models at startup so the first user request is instant."""
    with _warmup_lock:
        print("⚡ Pre-warming all AI models in background...")
        try:
            get_whisper_model('large-v2')
            get_summarizer()
            get_qg_generator()
            get_qa_answerer()
            print("✅ All models pre-warmed and ready!")
        except Exception as e:
            print(f"⚠️ Model pre-warm error (non-fatal): {e}")

def _create_summarizer(model_name):
    kwargs = {"device": device} if device == 0 else {}
    if device == 0:
        kwargs["torch_dtype"] = torch.float16
        
    try:
        from transformers import pipeline
        return pipeline("summarization", model=model_name, framework="pt", **kwargs)
    except Exception as e:
        from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
        print(f"⚠️ Pipeline creation failed for {model_name}: {e}. Falling back to manual loading.")
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
        if device == 0:
            model = model.to(device).half()
            
        def manual_summ(text, **gen_kwargs):
            if "max_length" not in gen_kwargs: gen_kwargs["max_length"] = 150
            if "min_length" not in gen_kwargs: gen_kwargs["min_length"] = 40
            if "do_sample" not in gen_kwargs: gen_kwargs["do_sample"] = False
            
            inputs = tokenizer(text, return_tensors="pt", max_length=1024, truncation=True).to(model.device)
            summary_ids = model.generate(inputs["input_ids"], **gen_kwargs)
            summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True)
            return [{"summary_text": summary}]
            
        return manual_summ

def get_summarizer():
    # facebook/bart-large-cnn — best fit for extractive lecture summarization
    if 'summarizer' not in _models:
        _models['summarizer'] = _create_summarizer("facebook/bart-large-cnn")
    return _models['summarizer']

def get_qg_generator():
    if 'qg' not in _models:
        # Upgraded to flan-t5-large for higher quality question generation
        model_name = "google/flan-t5-large"
        kwargs = {"device": device} if device == 0 else {}
        if device == 0:
            kwargs["torch_dtype"] = torch.float16
        
        try:
            from transformers import pipeline
            _models['qg'] = pipeline("text2text-generation", model=model_name, framework="pt", **kwargs)
        except Exception:
            from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
            if device == 0:
                model = model.to(device).half()
            def manual_qg(text, **gen_kwargs):
                if not isinstance(text, list): text = [text]
                inputs = tokenizer(text, return_tensors="pt", max_length=512, truncation=True, padding=True).to(model.device)
                gen_params = {"max_new_tokens": 128, "num_beams": 4, "early_stopping": True, **gen_kwargs}
                out = model.generate(**inputs, **gen_params)
                results = []
                for idx in range(len(text)):
                    results.append({"generated_text": tokenizer.decode(out[idx], skip_special_tokens=True)})
                return results
            _models['qg'] = manual_qg
    return _models['qg']

def get_qa_answerer():
    if 'qa' not in _models:
        # Upgraded to deepset/roberta-base-squad2 for higher precision answer extraction
        model_name = "deepset/roberta-base-squad2"
        kwargs = {"device": device} if device == 0 else {}
        if device == 0:
            kwargs["torch_dtype"] = torch.float16
        try:
            from transformers import pipeline
            _models['qa'] = pipeline("question-answering", model=model_name, framework="pt", **kwargs)
        except Exception:
            from transformers import AutoModelForQuestionAnswering, AutoTokenizer
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            model = AutoModelForQuestionAnswering.from_pretrained(model_name)
            if device == 0:
                model = model.to(device).half()
            def manual_qa(question=None, context=None, **kwargs):
                inputs = tokenizer(question=question, context=context, return_tensors="pt", truncation=True, max_length=512).to(model.device)
                with torch.no_grad():
                    outputs = model(**inputs)
                start_idx = torch.argmax(outputs.start_logits)
                end_idx = torch.argmax(outputs.end_logits)
                tokens = inputs.input_ids[0][start_idx : end_idx + 1]
                return {'score': 1.0, 'answer': tokenizer.decode(tokens, skip_special_tokens=True)}
            _models['qa'] = manual_qa
    return _models['qa']

def chunk_text(text, max_chars=3000):
    sentences = nltk.sent_tokenize(text)
    chunks = []
    current_chunk = ""
    for sentence in sentences:
        if len(current_chunk) + len(sentence) + 1 <= max_chars:
            current_chunk += sentence + " "
        else:
            chunks.append(current_chunk.strip())
            current_chunk = sentence + " "
    if current_chunk:
        chunks.append(current_chunk.strip())
    return chunks

def summarize_text(text):
    """Generate a clean bullet-point summary exactly as done last month."""
    if not text: return ""
    summarizer = get_summarizer()
    words = text.split()
    chunks = [" ".join(words[i:i+800]) for i in range(0, len(words), 800)]
    summaries = []

    for chunk in chunks:
        try:
            s = summarizer(chunk, max_length=200, min_length=50, do_sample=False)[0]["summary_text"]
            summaries.append(s)
        except Exception as e:
            pass

    combined_text = " ".join(summaries)
    sentences = nltk.sent_tokenize(combined_text)
    seen = set()
    bullet_points = []
    for s in sentences:
        s = s.strip()
        if len(s) > 20 and s not in seen:
            bullet_points.append(f"• {s}")
            seen.add(s)
    return "\n".join(bullet_points)

def generate_important_questions(text):
    """Extract Q&A using T5 for generation and distilbert-squad for answering."""
    if not text: return []
    qg = get_qg_generator()
    qa = get_qa_answerer()
    words = text.split()
    chunks = [" ".join(words[i:i+800]) for i in range(0, len(words), 800)]
    qa_list = []
    seen = set()
    
    for chunk in chunks[:4]:
        try:
            # T5 generates the question based on the content
            q = qg(f"generate questions: {chunk}", max_length=128)[0]["generated_text"].strip()
            # Distilbert provides the exact answer
            ans = qa(question=q, context=chunk)["answer"].strip()
            
            if len(ans) > 2 and q.lower() not in seen:
                qa_list.append({"question": q, "answer": ans, "type": "short"})
                seen.add(q.lower())
        except Exception:
            pass

    # Ensure UI never gets empty array if AI struggles with specific chunks
    if len(qa_list) < 2:
        for chunk in chunks[:2]:
            for fallback_q in ["What is a key concept in this section?", "What does this section explain?"]:
                try:
                    ans = qa(question=fallback_q, context=chunk)["answer"].strip()
                    if len(ans) > 2 and fallback_q.lower() not in seen:
                        qa_list.append({"question": fallback_q, "answer": ans, "type": "long"})
                        seen.add(fallback_q.lower())
                except Exception:
                    continue

    return qa_list

def generate_notes(text):
    """Generate notes strictly using the summarizer on chunks, exactly like early Jan."""
    if not text: return ""
    summarizer = get_summarizer()
    words = text.split()
    chunks = [" ".join(words[i:i+800]) for i in range(0, len(words), 800)]
    summaries = []
    
    for chunk in chunks:
        try:
            s = summarizer(chunk, max_length=200, min_length=50, do_sample=False)[0]["summary_text"]
            summaries.append(s)
        except Exception:
            pass
            
    notes_parts = ["## 📌 Key Notes"]
    for s in summaries:
        notes_parts.append(f"  • {s}")
        
    return "\n".join(notes_parts)

def generate_quiz(text, is_pro=False):
    """Generate quiz components by piping standard text into t5-qa-qg (one month ago behavior)."""
    if not text: return []
    qg = get_qg_generator()
    qa = get_qa_answerer()
    words = text.split()
    chunks = [" ".join(words[i:i+800]) for i in range(0, len(words), 800)]
    questions = []
    idx = 1
    
    seen = set()
    for chunk in chunks[:4]: 
        try:
            # T5 generates context-specific question
            q = qg(f"generate questions: {chunk}", max_length=256)[0]["generated_text"].strip()
            # Distilbert scores the exact answer
            ans = qa(question=q, context=chunk)["answer"].strip()
            
            if len(ans) > 2 and q.lower() not in seen:
                questions.append({
                    "id": idx,
                    "type": "short",
                    "question": q,
                    "correct": ans,
                    "explanation": f"AI verified answer: {ans}"
                })
                seen.add(q.lower())
                idx += 1
        except Exception:
            pass
            
    # Guarantee at least one valid quiz question returns via fallback
    if len(questions) == 0 and chunks:
        try:
            q = "What is the primary topic of the lecture?"
            ans = qa(question=q, context=chunks[0])["answer"].strip()
            questions.append({
                "id": idx, "type": "short", "question": q, 
                "correct": ans, "explanation": "Fallback verification"
            })
        except Exception: pass
            
    return questions

def generate_flashcards(qa_data):
    """Convert the dynamically generated explicit Q&A directly into flashcards."""
    if not qa_data: return []
    cards = []
    for item in qa_data[:10]:
        cards.append({"front": item['question'], "back": item['answer']})
    return cards

def inject_ffmpeg():
    import shutil
    # 1. Check if ffmpeg is already in PATH
    ffmpeg_path = shutil.which("ffmpeg")
    if ffmpeg_path:
        return os.path.dirname(ffmpeg_path)
    
    # 2. Check common installation paths without walking
    common_paths = [
        "C:\\ffmpeg\\bin",
        "C:\\ffmpeg",
        os.path.expanduser("~\\Downloads\\ffmpeg\\bin"),
        os.path.expandvars("%PROGRAMFILES%\\ffmpeg\\bin"),
        os.path.expandvars("%LOCALAPPDATA%\\ffmpeg\\bin")
    ]
    
    for p in common_paths:
        if os.path.exists(os.path.join(p, "ffmpeg.exe")):
            if p not in os.environ["PATH"]:
                os.environ["PATH"] = p + os.pathsep + os.environ["PATH"]
            return p
            
    # 3. Try static-ffmpeg as a fallback (fast)
    try:
        from static_ffmpeg import run as ffmpeg_run
        ffmpeg_exe, _ = ffmpeg_run.get_or_fetch_platform_executables_else_raise()
        p = os.path.dirname(ffmpeg_exe)
        if p not in os.environ["PATH"]:
            os.environ["PATH"] = p + os.pathsep + os.environ["PATH"]
        return p
    except Exception:
        pass
        
    return None

FFMPEG_PATH = inject_ffmpeg()


def handle_youtube(url):
    import yt_dlp
    uid = str(uuid.uuid4())[:8]
    out_tmpl = os.path.join(UPLOAD_FOLDER, f"yt_{uid}.%(ext)s")
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': out_tmpl,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        }
    }
    
    if FFMPEG_PATH:
        ydl_opts['ffmpeg_location'] = FFMPEG_PATH
        
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
            
        expected_file = os.path.join(UPLOAD_FOLDER, f"yt_{uid}.mp3")
        if os.path.exists(expected_file):
            return expected_file
            
        # Fallback search
        for f in os.listdir(UPLOAD_FOLDER):
            if f.startswith(f"yt_{uid}") and f.endswith(".mp3"):
                return os.path.join(UPLOAD_FOLDER, f)
    except Exception as e:
        print(f"yt-dlp error: {e}")
        return None
    return None

def extract_audio(video_path, out_audio="lecture.mp3"):
    audio = AudioSegment.from_file(video_path)
    dest_audio = os.path.join(UPLOAD_FOLDER, out_audio)
    audio.export(dest_audio, format="mp3")
    return dest_audio

def translate_result(result, target_lang):
    if not result or target_lang == 'en':
        return result
        
    # Translate core components
    if 'transcript' in result:
        result['transcript'] = translate_text(result['transcript'], target_lang)
    if 'notes' in result:
        result['notes'] = translate_text(result['notes'], target_lang)
    if 'qa' in result:
        for item in result['qa']:
            item["question"] = translate_text(item["question"], target_lang)
            item["answer"] = translate_text(item["answer"], target_lang)
    
    result['language'] = target_lang
    return result

# Global worker pool for speed
_executor = ThreadPoolExecutor(max_workers=8)

def process_lecture(source_type, data, target_lang='en'):
    # data can be URL, local path, or raw text
    audio_path = None
    transcript = None
    
    if source_type == "youtube":
        audio_path = handle_youtube(data)
    elif source_type in ["upload", "video", "audio"]:
        if data.lower().endswith(('.mp4', '.avi', '.mov', '.mkv')):
             audio_path = extract_audio(data, out_audio=f"uploaded_{uuid.uuid4().hex}.mp3")
        else:
             audio_path = data
    elif source_type == "text_file":
        try:
            with open(data, "r", encoding="utf-8") as f:
                transcript = f.read()
        except Exception as e:
            print(f"Error reading text file: {e}")
            return None
    elif source_type == "text":
        transcript = data
        
    if audio_path and not transcript:
        # Use large-v2 for best accuracy on academic lectures
        model = get_whisper_model("large-v2")
        segments, info = model.transcribe(
            audio_path, 
            beam_size=5, 
            temperature=0, 
            vad_filter=True, 
            task="transcribe",
            initial_prompt="Educational lecture with clear terminology and technical jargon."
        )
        transcript = "".join([segment.text for segment in segments])
        
    if not transcript:
        return None
        
    # Parallelize core tasks using global executor
    future_qa = _executor.submit(generate_important_questions, transcript)
    future_notes = _executor.submit(generate_notes, transcript)
    future_quiz = _executor.submit(generate_quiz, transcript)
    
    qa_data = future_qa.result()
    notes = future_notes.result()
    quiz_data = future_quiz.result()
    
    result = {
        "transcript": transcript,
        "qa": qa_data,
        "notes": notes,
        "quiz": quiz_data,
        "flashcards": generate_flashcards(qa_data),
        "language": "en"
    }

    # If target_lang was specified initially (backward compatibility), translate it
    if target_lang != 'en':
        result = translate_result(result, target_lang)
        
    return result
