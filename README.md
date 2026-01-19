# LecGen AI - Intelligent Lecture Assistant

LecGen AI is a powerful tool designed to transform lecture recordings (YouTube links, video files, or audio files) into structured study materials.

## Features

- **Transcription:** High-accuracy transcription using OpenAI's Whisper model.
- **Summarization:** Smart summaries that capture the essence of the lecture.
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

### Streamlit Frontend (Recommended)

To run the modern Streamlit interface:

```bash
streamlit run streamlit_app.py
```

### CLI Interface

To run the command-line interface:

```bash
python main.py
```

## Tech Stack

- **Frontend:** [Streamlit](https://streamlit.io/)
- **Transcription:** [OpenAI Whisper](https://github.com/openai/whisper)
- **AI Models:** [Hugging Face Transformers](https://huggingface.co/docs/transformers/index) (BART, T5, RoBERTa)
- **Audio Processing:** [Pydub](http://pydub.com/)
- **Video Download:** [yt-dlp](https://github.com/yt-dlp/yt-dlp)
