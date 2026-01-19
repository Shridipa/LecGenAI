import time
import sys
import os

sys.path.append(os.path.join(os.getcwd(), 'LectureAIWeb'))

from app import summarize_text, generate_notes, generate_quiz, generate_flashcards

test_transcript = """
Artificial intelligence is a branch of computer science that aims to create machines that can perform tasks that typically require human intelligence. 
These tasks include learning, reasoning, problem-solving, perception, and language understanding. 
AI research has been highly successful in developing effective techniques for solving a wide range of problems, from playing games to medical diagnosis.
In recent years, the development of deep learning and large language models has led to significant breakthroughs in AI performance.
These models are trained on massive amounts of data and can generate human-like text, translate languages, and even write code.
As AI continues to evolve, it is expected to have a profound impact on society, transforming industries and changing the way we live and work.
The ethics of AI is an important area of research, as it addresses questions about bias, transparency, and accountability in AI systems.
"""

def test_speed():
    print("🚀 Starting benchmark...")
    
    actions = {
        "Summary": summarize_text,
        "Notes": generate_notes,
        "Quiz": generate_quiz,
        "Flashcards": generate_flashcards
    }
    
    for name, func in actions.items():
        start = time.time()
        print(f"Running {name}...")
        try:
            output = func(test_transcript)
            end = time.time()
            print(f"✅ {name} finished in {end - start:.2f}s")
        except Exception as e:
            print(f"❌ {name} failed: {e}")

if __name__ == "__main__":
    test_speed()
