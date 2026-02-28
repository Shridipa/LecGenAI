import sys
import os
from datetime import datetime
from typing import Optional, Dict, List, Any

# Add project root and local api folder to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.middleware.cors import CORSMiddleware
import uuid
import shutil
import json
import processor
from pyq_analyzer import PYQAnalyzer

from fastapi.staticfiles import StaticFiles
from fastapi import Header, HTTPException, Depends
from passlib.context import CryptContext
from jose import JWTError, jwt
from pydantic import BaseModel, EmailStr

from fastapi import FastAPI, BackgroundTasks, UploadFile, File, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional, Dict, Any
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html

# --- API Models for Documentation ---
class ProcessingTaskStatus(BaseModel):
    task_id: str = Field(..., example="550e8400-e29b-41d4-a716-446655440000")
    status: str = Field(..., example="processing")
    type: str = Field(..., example="youtube")
    title: str = Field(..., example="Introduction to AI")

class Flashcard(BaseModel):
    front: str = Field(..., example="What is a Neural Network?")
    back: str = Field(..., example="A computational model inspired by the human brain.")

class QuizItem(BaseModel):
    id: int = Field(..., example=1)
    type: str = Field(..., example="mcq")
    question: str = Field(..., example="Capital of France?")
    options: Optional[List[str]] = Field(None, example=["Paris", "London", "Berlin"])
    correct: str = Field(..., example="Paris")

class LectureResult(BaseModel):
    transcript: str = Field(..., example="Full text of the lecture...")
    notes: str = Field(..., example="- Point A\n- Point B")
    quiz: List[QuizItem]
    flashcards: List[Flashcard]
    language: str = Field(..., example="en")

class TaskResponse(BaseModel):
    status: str = Field(..., example="completed")
    result: Optional[LectureResult] = None
    error: Optional[str] = None
    wordCount: Optional[int] = None

# --- Security Configuration ---
SECRET_KEY = "lecgen_ai_secret_key_change_me"
ALGORITHM = "HS256"
# Reduced rounds for faster performance in development/demo environments
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=10)

DATA_DIR = "data"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

USERS_FILE = os.path.join(DATA_DIR, "users.json")
HISTORY_FILE = os.path.join(DATA_DIR, "history.json")

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class User(BaseModel):
    email: str
    name: str

def load_users():
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_users(users_data):
    with open(USERS_FILE, "w") as f:
        json.dump(users_data, f, indent=4)

users = load_users()

def get_password_hash(password):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict):
    to_encode = data.copy()
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization.split(" ")[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            return None
        return email
    except JWTError:
        return None

# --- App Initialization ---
app = FastAPI(
    title="LecGen AI - Educational Intelligence API",
    description="""
    ## 🚀 Premium Educational Intelligence
    Transform complex lectures into structured knowledge nodes instantly.
    
    ### 🛡️ Features
    - **Fast Transcription:** Powered by Whisper (base)
    - **Smart Synthesis:** DistilBART & T5 Small
    - **Knowledge Extraction:** Interactive Flashcards & Quizzes
    - **Academic Analysis:** Comprehensive PYQ Analyzer
    """,
    version="1.1.0",
    docs_url=None, # Disable default docs to use custom ones
    redoc_url=None,
    contact={
        "name": "Shridipa",
        "url": "https://github.com/Shridipa/LecGenAI",
    }
)
pyq_analyzer = PYQAnalyzer()

# Ensure static directory exists
os.makedirs("static/images", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Enable CORS for React frontend (Allow all origins for testing)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Task storage
tasks: Dict[str, dict] = {}

def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_history():
    with open(HISTORY_FILE, "w") as f:
        json.dump(tasks, f, indent=4)

# Load existing history on startup
tasks = load_history()

# --- Custom Documentation Endpoints ---
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=app.title + " - Interactive Docs",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        swagger_favicon_url="https://cdn-icons-png.flaticon.com/512/2103/2103930.png",
        swagger_ui_parameters={
            "defaultModelsExpandDepth": -1, # Hide schemas by default for cleaner UI
            "persistAuthorization": True,
        }
    )

@app.get("/redoc", include_in_schema=False)
async def redoc_html():
    return get_redoc_html(
        openapi_url=app.openapi_url,
        title=app.title + " - ReDoc",
        redoc_favicon_url="https://cdn-icons-png.flaticon.com/512/2103/2103930.png",
    )

@app.get("/api-reference", response_class=HTMLResponse, include_in_schema=False)
async def api_reference():
    """Serve the premium visual documentation page."""
    with open("static/DOCUMENTATION.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/", tags=["System Information"])
async def root():
    """Verify that the LecGen AI Engine is online and operational."""
    return {"status": "online", "engine": "LecGen AI v1.1.0"}

@app.get("/ping")
async def ping():
    return {"status": "ok"}

# --- Auth Endpoints ---
@app.post("/auth/signup", tags=["Authentication"])
async def signup(user_data: UserCreate):
    if user_data.email in users:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    users[user_data.email] = {
        "password": get_password_hash(user_data.password),
        "name": user_data.name
    }
    save_users(users)
    
    access_token = create_access_token(data={"sub": user_data.email})
    return {"access_token": access_token, "token_type": "bearer", "user": {"email": user_data.email, "name": user_data.name}}

@app.post("/auth/login", tags=["Authentication"])
async def login(user_data: UserLogin):
    user = users.get(user_data.email)
    if not user or not verify_password(user_data.password, user["password"]):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    
    access_token = create_access_token(data={"sub": user_data.email})
    return {"access_token": access_token, "token_type": "bearer", "user": {"email": user_data.email, "name": user["name"]}}

@app.get("/auth/me", tags=["Authentication"])
async def get_me(current_user: str = Depends(get_current_user)):
    if not current_user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    user = users.get(current_user)
    return {"email": current_user, "name": user.get("name", "User")}

# --- Modified History Endpoint ---
@app.get("/history", tags=["Task Management"])
async def get_history(current_user: str = Depends(get_current_user)):
    """Retrieve history for the logged-in user."""
    user_history = []
    for task_id, task in tasks.items():
        # Backward compatibility: show all if no user_email, or only user's
        if task.get("user_email") == current_user or (not current_user and not task.get("user_email")):
            user_history.append({
                "id": task_id,
                "title": task.get("title", "Lecture"),
                "date": task.get("timestamp", ""),
                "type": task.get("type", "unknown"),
                "wordCount": task.get("wordCount", 0),
                "result": task.get("result")
            })
    
    # Sort by recent first
    user_history.sort(key=lambda x: x["date"], reverse=True)
    return user_history

@app.get("/tasks/{task_id}", tags=["Task Management"], response_model=TaskResponse)
async def get_task_status(task_id: str):
    """
    Check the current status and get results of a specific processing task.
    
    ### Statuses:
    - **pending**: Task is in queue.
    - **processing/compressing**: AI is analyzing content.
    - **completed**: Results are ready.
    - **failed**: An error occurred.
    """
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    return tasks[task_id]

@app.delete("/history/{task_id}", tags=["History Management"])
async def delete_history_item(task_id: str):
    """Remove a specific analysis from the local history database."""
    if task_id in tasks:
        del tasks[task_id]
        save_history()
        return {"status": "success"}
    raise HTTPException(status_code=404, detail="Item not found")

@app.get("/history/download/{task_id}", tags=["History Management"])
async def download_history_result(task_id: str):
    """Download the full JSON result of a previous analysis."""
    if task_id not in tasks or "result" not in tasks[task_id]:
        raise HTTPException(status_code=404, detail="Result not found")
    
    result_data = tasks[task_id]["result"]
    title = tasks[task_id].get("title", "lecture_analysis")
    safe_title = "".join([c if c.isalnum() else "_" for c in title])
    
    temp_json = f"temp_{task_id}.json"
    with open(temp_json, "w") as f:
        json.dump(result_data, f, indent=4)
    
    from fastapi.responses import FileResponse
    return FileResponse(
        temp_json, 
        media_type='application/json', 
        filename=f"{safe_title}.json"
    )

@app.get("/history", tags=["History Management"])
async def get_all_history():
    """Retrieve a list of all successfully completed analysis tasks."""
    # Return sorted history (newest first)
    history_list = []
    for tid, data in tasks.items():
        if data.get("status") == "completed":
            history_list.append({"id": tid, **data})
    
    # Sort by date
    history_list.sort(key=lambda x: x.get("date", ""), reverse=True)
    return history_list

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
SILENT_COMPRESS_SIZE = 5 * 1024 * 1024 # 5MB

def compress_file(input_path):
    """Compress video/audio using ffmpeg efficiently"""
    import subprocess
    output_path = input_path.rsplit('.', 1)[0] + "_processed.mp3"
    
    # Check if already processed
    if os.path.exists(output_path):
        return output_path
        
    # Bitrate 64k is perfect for voice-heavy lectures, much faster than defaults
    cmd = [
        'ffmpeg', '-y', '-i', input_path, 
        '-vn', # Disable video for speed
        '-acodec', 'libmp3lame', 
        '-ab', '64k', 
        '-ar', '22050', # Lower sample rate for processing speed, enough for speech
        output_path
    ]
    
    try:
        subprocess.run(cmd, check=True, capture_output=True)
        return output_path if os.path.exists(output_path) else input_path
    except:
        return input_path

def run_processing_task(task_id: str, source_type: str, data: str, target_lang: str = 'en'):
    # Tiered Compression Logic (Only for Media)
    is_media = source_type in ["video", "audio", "upload", "youtube"]
    if is_media and os.path.exists(data):
        size = os.path.getsize(data)
        if size > MAX_FILE_SIZE:
             # > 10MB: Explicit notification
            tasks[task_id]["status"] = "compressing"
            save_history()
            data = compress_file(data)
        elif size < SILENT_COMPRESS_SIZE:
            # < 5MB: Silent auto-compression
            tasks[task_id]["status"] = "optimizing" 
            save_history()
            data = compress_file(data)
            
    tasks[task_id]["status"] = "processing"
    save_history()
    
    try:
        # Default generation in English for speed
        result = processor.process_lecture(source_type, data, target_lang="en")
        
        if result:
            tasks[task_id]["status"] = "completed"
            tasks[task_id]["result"] = result
            tasks[task_id]["date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            # Calculate word count for history view
            transcript = result.get('transcript', '')
            tasks[task_id]["wordCount"] = len(transcript.split())
        else:
            tasks[task_id]["status"] = "failed"
            tasks[task_id]["error"] = "AI Engine failed to extract content."
    except Exception as e:
        tasks[task_id]["status"] = "failed"
        tasks[task_id]["error"] = str(e)
    
    save_history()

@app.post("/process/youtube", tags=["Processing"])
async def process_youtube(
    background_tasks: BackgroundTasks, 
    url: str = Form(...),
    current_user: Optional[str] = Depends(get_current_user)
):
    """
    Process a YouTube video into study materials.
    """
    task_id = str(uuid.uuid4())
    tasks[task_id] = {
        "status": "processing",
        "timestamp": datetime.now().isoformat(),
        "type": "youtube",
        "title": url.split('=')[-1] if '=' in url else "YouTube Lecture",
        "user_email": current_user
    }
    background_tasks.add_task(run_processing_task, task_id, "youtube", url)
    return {"task_id": task_id}

@app.post("/process/file", tags=["Processing"])
async def process_file(
    background_tasks: BackgroundTasks, 
    file: UploadFile = File(...),
    current_user: Optional[str] = Depends(get_current_user)
):
    """
    Upload and process an audio or video file.
    """
    task_id = str(uuid.uuid4())
    file_path = os.path.join(UPLOAD_DIR, f"{task_id}_{file.filename}")
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    tasks[task_id] = {
        "status": "processing",
        "timestamp": datetime.now().isoformat(),
        "type": "file",
        "title": file.filename,
        "user_email": current_user
    }
    background_tasks.add_task(run_processing_task, task_id, "file", file_path)
    return {"task_id": task_id}

@app.post("/process/text", tags=["Processing"])
async def process_text(
    background_tasks: BackgroundTasks, 
    text: str = Form(...),
    current_user: Optional[str] = Depends(get_current_user)
):
    """
    Transform raw text into structured study materials.
    """
    task_id = str(uuid.uuid4())
    tasks[task_id] = {
        "status": "processing",
        "timestamp": datetime.now().isoformat(),
        "type": "text",
        "title": f"Text: {text[:20]}...",
        "user_email": current_user
    }
    background_tasks.add_task(run_processing_task, task_id, "text", text)
    return {"task_id": task_id}

@app.post("/translate/{task_id}", tags=["Knowledge Translation"])
async def translate_task_result(task_id: str, target_lang: str = Form(...)):
    """
    Translate an existing analysis result into a different language.
    Utilizes high-speed cloud translation services.
    """
    if task_id not in tasks or "result" not in tasks[task_id]:
        raise HTTPException(status_code=404, detail="Task result not found")
        
    tasks[task_id]["status"] = "translating"
    save_history()
    
    try:
        # Perform translation on existing result
        translated_result = processor.translate_result(tasks[task_id]["result"], target_lang)
        tasks[task_id]["result"] = translated_result
        tasks[task_id]["status"] = "completed"
        tasks[task_id]["language"] = target_lang
        save_history()
        return {"status": "success", "result": translated_result}
    except Exception as e:
        tasks[task_id]["status"] = "completed" # Reset to completed even if translation fails
        raise HTTPException(status_code=500, detail=str(e))

from typing import List

@app.post("/analyze/pyq", tags=["Exam Preparation"])
def analyze_pyq(files: List[UploadFile] = File(default=None), drive_link: str = Form(default=None)):
    """
    Perform a Previous Year Question (PYQ) analysis.
    Accepts direct file uploads or a Google Drive link containing multiple documents.
    """
    try:
        temp_files = []
        
        # 1. Handle File Uploads
        if files:
            for file in files:
                file_ext = file.filename.split(".")[-1].lower()
                if file_ext in ['pdf', 'docx', 'txt', 'csv']:
                    temp_path = os.path.join(UPLOAD_FOLDER, f"pyq_{uuid.uuid4().hex}.{file_ext}")
                    with open(temp_path, "wb") as buffer:
                        shutil.copyfileobj(file.file, buffer)
                    temp_files.append(temp_path)

        # 2. Handle Google Drive Link
        if drive_link:
            clean_link = drive_link.strip()
            drive_files = pyq_analyzer.process_drive_link(clean_link, UPLOAD_FOLDER)
            temp_files.extend(drive_files)
            
        if not temp_files:
             raise HTTPException(status_code=400, detail="No valid files provided. Upload files or provide a valid Google Drive link.")
        
        # 3. Analyze content
        result = pyq_analyzer.perform_full_analysis(temp_files)
        
        # Cleanup
        for path in temp_files:
            if os.path.exists(path):
                try:
                    os.remove(path)
                except:
                    pass
            
        return result
    except Exception as e:
        # Cleanup on error too
        for path in temp_files:
            if os.path.exists(path):
                try:
                    os.remove(path)
                except:
                    pass
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
