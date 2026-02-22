import processor
import os

url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
print(f"Testing YouTube download for: {url}")
result = processor.handle_youtube(url)
if result:
    print(f"SUCCESS: Downloaded to {result}")
else:
    print("FAILED: handle_youtube returned None")
