import processor
import sys

url = "https://www.youtube.com/watch?v=f_rhQ8B8-5Y"

print(f"Testing handle_youtube with URL: {url}")
result = processor.handle_youtube(url)

if result:
    print(f"SUCCESS: Audio downloaded to {result}")
else:
    print("FAILURE: handle_youtube returned None")

# Also test get_whisper_model loading while we are at it
print("Testing Whisper model loading...")
try:
    processor.get_whisper_model()
    print("SUCCESS: Whisper model loaded")
except Exception as e:
    print(f"FAILURE: Whisper model loading failed: {e}")
