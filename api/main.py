from fastapi.middleware.cors import CORSMiddleware
import os
# Triggering reload for deep-translator
import uuid
import shutil
import json
import processor

from datetime import datetime
from typing import Optional, Dict
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from pyq_analyzer import PYQAnalyzer

from fastapi.staticfiles import StaticFiles

from fastapi import FastAPI, BackgroundTasks, UploadFile, File, Form, HTTPException

app = FastAPI(title="LecGen AI API")
pyq_analyzer = PYQAnalyzer()

# Ensure static directory exists
os.makedirs("static/images", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_FOLDER = "uploads"
HISTORY_FILE = "history.json"
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

@app.get("/")
async def root():
    return {"message": "LecGen AI API is running"}

@app.get("/ping")
async def ping():
    return {"status": "ok"}

@app.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    return tasks[task_id]

@app.delete("/history/{task_id}")
async def delete_history_item(task_id: str):
    if task_id in tasks:
        del tasks[task_id]
        save_history()
        return {"status": "success"}
    raise HTTPException(status_code=404, detail="Item not found")

@app.get("/history/download/{task_id}")
async def download_history_result(task_id: str):
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

@app.get("/history")
async def get_all_history():
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
    """Compress video/audio using ffmpeg"""
    output_path = input_path.rsplit('.', 1)[0] + "_comp.mp3"
    # Bitrate 64k is perfect for lectures
    cmd = f'ffmpeg -y -i "{input_path}" -ab 64k "{output_path}"'
    os.system(cmd)
    return output_path if os.path.exists(output_path) else input_path

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

@app.post("/process/youtube")
async def process_youtube(background_tasks: BackgroundTasks, url: str = Form(...)):
    task_id = str(uuid.uuid4())
    tasks[task_id] = {
        "status": "pending", 
        "type": "youtube", 
        "title": f"YouTube: {url[:30]}...",
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "language": "en"
    }
    background_tasks.add_task(run_processing_task, task_id, "youtube", url)
    return {"task_id": task_id}

@app.post("/process/file")
async def process_file(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    try:
        file_ext = file.filename.split(".")[-1].lower()
        temp_path = os.path.join(UPLOAD_FOLDER, f"upload_{uuid.uuid4().hex}.{file_ext}")
        
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        task_id = str(uuid.uuid4())
        tasks[task_id] = {
            "status": "pending", 
            "type": "file", 
            "title": file.filename,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "language": "en"
        }
        
        if file_ext in ["mp4", "mkv", "avi", "mov"]:
            source_type = "video"
        elif file_ext in ["txt", "md", "pdf"]: # Handle text files directly
            source_type = "text_file"
        else:
            source_type = "audio"
            
        background_tasks.add_task(run_processing_task, task_id, source_type, temp_path)
        
        return {"task_id": task_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/process/text")
async def process_text(background_tasks: BackgroundTasks, text: str = Form(...)):
    task_id = str(uuid.uuid4())
    tasks[task_id] = {
        "status": "pending", 
        "type": "text", 
        "title": f"Notes: {text[:30]}...",
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "language": "en"
    }
    background_tasks.add_task(run_processing_task, task_id, "text", text)
    return {"task_id": task_id}

@app.post("/translate/{task_id}")
async def translate_task_result(task_id: str, target_lang: str = Form(...)):
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

@app.post("/analyze/pyq")
def analyze_pyq(files: List[UploadFile] = File(default=None), drive_link: str = Form(default=None)):
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
