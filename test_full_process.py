import processor
import traceback

url = "https://www.youtube.com/watch?v=f_rhQ8B8-5Y"

print("=" * 80)
print("FULL PIPELINE TEST")
print("=" * 80)

try:
    result = processor.process_lecture("youtube", url)
    
    if result:
        print("\n✅ SUCCESS! Processing completed.")
        print(f"\nTranscript length: {len(result.get('transcript', ''))}")
        print(f"Summary length: {len(result.get('summary', ''))}")
        print(f"Notes length: {len(result.get('notes', ''))}")
        print(f"Quiz questions: {len(result.get('quiz', []))}")
        print(f"Flashcards: {len(result.get('flashcards', []))}")
        
        print("\n--- FIRST 200 CHARS OF SUMMARY ---")
        print(result.get('summary', '')[:200])
    else:
        print("\n❌ FAILURE: process_lecture returned None")
        
except Exception as e:
    print(f"\n❌ EXCEPTION: {e}")
    print("\n--- TRACEBACK ---")
    traceback.print_exc()
