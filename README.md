# LecGen AI - Intelligent Lecture Assistant

LecGen AI is a powerful tool designed to transform lecture recordings (YouTube links, video files, or audio files) into structured study materials.

## Features

- **Transcription:** High-accuracy transcription using OpenAI's Whisper model.
- **Summarization:** Smart summaries that capture the essence of the lecture.
- **PYQ Analysis:** Intelligent analysis of Previous Year Question papers with:
  - **Topic Clustering:** ML-powered grouping of related questions.
  - **Smart Naming:** Context-aware expansion of topic names (e.g., "M" → "Memory Management").
  - **Diagram Support:** Automatic extraction and inline rendering of diagrams and graphs.
  - **Question Rewriting:** Transformation of vague questions into clear, context-rich queries.
  - **Curated Resources:** Direct links to verified tutorials (GeeksforGeeks, TutorialsPoint) for every topic.
  - **Difficulty Classification:** Categorization into Standard, Important, and Critical levels.
- **Notes Generation:** Structured notes for easy review.
- **Quiz Generation:** AI-generated questions and answers to test your knowledge.
- **Flashcards:** Interactive flashcards for active recall.

## Setup

1.  **Clone the repository:**

    ```bash
    git clone <repository-url>
    cd LecGenAICTE
    ```

2.  **Create and activate a virtual environment:**

    ```bash
    python -m venv venv
    .\venv\Scripts\activate  # Windows
    source venv/bin/activate  # Linux/Mac
    ```

3.  **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

4.  **Install FFmpeg:**
    FFmpeg is required for audio processing. Download it from [ffmpeg.org](https://ffmpeg.org/) and add it to your system PATH.

## Running the App

### Recommended: React + FastAPI (Modern Stack)

This is the new modern interface built with React and FastAPI.

1.  **Install Frontend Dependencies:**

    ```bash
    cd frontend
    npm install
    cd ..
    ```

2.  **Start both Backend and Frontend:**
    Run the handy batch script:
    ```bash
    .\start_app.bat
    ```
    Or manually:
    - Backend: `python -m uvicorn api.main:app --reload --port 8000`
    - Frontend: `cd frontend && npm run dev`

### Legacy: Streamlit Frontend

To run the legacy Streamlit interface:

```bash
streamlit run streamlit_app.py
```

### CLI Interface

To run the command-line interface:

```bash
python main.py
```

## Tech Stack

- **Frontend:** [React JS](https://react.dev/) + [Vite](https://vitejs.dev/) + [Lucide Icons](https://lucide.dev/)
- **Backend:** [FastAPI](https://fastapi.tiangolo.com/)
- **Transcription:** [OpenAI Whisper](https://github.com/openai/whisper)
- **AI Models:** [Hugging Face Transformers](https://huggingface.co/docs/transformers/index) (BART, T5, RoBERTa)
- **Audio Processing:** [Pydub](http://pydub.com/)
- **Video Download:** [yt-dlp](https://github.com/yt-dlp/yt-dlp)
