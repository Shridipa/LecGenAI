import os
import sys
import json
from processor import process_lecture

def main():
    print("🎓 LecGen AI - Command Line Interface (Powered by Groq)")
    print("======================================================")
    print("Choose input type:")
    print("1. Paste YouTube link")
    print("2. Provide path to recorded video lecture")
    print("3. Provide path to recorded audio lecture")
    print("4. Provide path to raw text file")
    
    try:
        choice = input("Enter 1, 2, 3, or 4: ").strip()
    except EOFError:
        print("\nInput aborted.")
        return

    source_type = ""
    data = ""

    if choice == "1":
        data = input("Paste YouTube link: ").strip()
        source_type = "youtube"
    elif choice == "2":
        data = input("Enter path to your video file: ").strip()
        source_type = "video"
    elif choice == "3":
        data = input("Enter path to your audio file: ").strip()
        source_type = "audio"
    elif choice == "4":
        data = input("Enter path to your text file: ").strip()
        source_type = "text_file"
    else:
        print("❌ Invalid choice. Please run the script again and select a valid number.")
        return

    if not data:
        print("❌ No input provided.")
        return

    print("\n⚡ Initializing Nitro Engine (Groq API)...")
    
    try:
        result = process_lecture(source_type, data)
    except Exception as e:
        print(f"❌ Processing failed: {e}")
        return
        
    if not result:
        print("❌ Processing returned no result. Check the logs for details.")
        return

    folder = "outputs"
    os.makedirs(folder, exist_ok=True)

    print("\n💾 Saving Knowledge Artifacts...")

    # Save Transcript
    with open(f"{folder}/transcript.txt", "w", encoding="utf-8") as f:
        f.write(result.get("transcript", ""))
    
    # Save Notes
    with open(f"{folder}/notes.txt", "w", encoding="utf-8") as f:
        f.write(result.get("notes", ""))
        
    # Save Quiz
    quiz_text = ""
    for idx, q in enumerate(result.get("quiz", [])):
        quiz_text += f"Q{idx+1}: {q.get('question', '')}\n"
        quiz_text += f"A: {q.get('correct', '')}\n"
        quiz_text += f"{q.get('explanation', '')}\n\n"
        
    with open(f"{folder}/quiz.txt", "w", encoding="utf-8") as f:
        f.write(quiz_text)
        
    # Save Flashcards
    cards_text = ""
    for idx, c in enumerate(result.get("flashcards", [])):
        cards_text += f"Front: {c.get('front', '')}\n"
        cards_text += f"Back: {c.get('back', '')}\n\n"
        
    with open(f"{folder}/flashcards.txt", "w", encoding="utf-8") as f:
        f.write(cards_text)

    print(f"✅ Success! All artifacts saved in the '{folder}' directory.")

if __name__ == "__main__":
    main()
