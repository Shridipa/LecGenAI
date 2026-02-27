# LecGen AI - API Documentation

This project uses **FastAPI**, which automatically generates interactive documentation based on the code.

## 🌐 Live Documentation

When the backend server is running, you can access the documentation at these local URLs:

- **Interactive Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)
  - _Best for: Testing endpoints directly from the browser, viewing request schemas, and seeing live responses._
- **ReDoc (Visual Documentation):** [http://localhost:8000/redoc](http://localhost:8000/redoc)
  - _Best for: Clean, readable technical reference._

## 📂 Source Code Location

The documentation logic (endpoints, docstrings, and tags) is located in:
`api/main.py`

## 🚀 Key API Endpoints

### 1. Lecture Processing (`/process/...`)

- `POST /process/youtube`: Submits a YouTube link for transcription and analysis.
- `POST /process/file`: Uploads media files (MP4, MP3, etc.) for processing.
- `POST /process/text`: Processes raw notes into structured study guides.

### 2. History Management (`/history/...`)

- `GET /history`: Lists all previous successful analyses.
- `GET /history/download/{task_id}`: Downloads the result as a JSON file.
- `DELETE /history/{task_id}`: Removes an entry from the history.

### 3. Exam Prep (`/analyze/pyq`)

- `POST /analyze/pyq`: Analyzes Previous Year Question papers from files or Google Drive links.

## 🛠️ Technology Stack

- **Engine:** FastAPI (Python)
- **Documentation Standard:** OpenAPI 3.0
- **Interactive UI:** Swagger UI / ReDoc
