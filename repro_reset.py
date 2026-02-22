
import requests
import os
import time

url = "http://127.0.0.1:8000/analyze/pyq"
# Using one of the existing PDFs
pdf_path = r"c:\Users\KIIT\LecGenAICTE\drive_test_folder\2024.pdf"

if not os.path.exists(pdf_path):
    print(f"File not found: {pdf_path}")
    exit(1)

print(f"Sending request to {url} with {pdf_path}...")
with open(pdf_path, 'rb') as f:
    files = {'files': (os.path.basename(pdf_path), f, 'application/pdf')}
    try:
        start_time = time.time()
        # Setting a long timeout for analysis
        response = requests.post(url, files=files, timeout=300)
        end_time = time.time()
        print(f"Status Code: {response.status_code}")
        print(f"Time taken: {end_time - start_time:.2f}s")
        if response.status_code == 200:
            print("Success! Result preview:")
            print(str(response.json())[:500])
        else:
            print(f"Error: {response.text}")
    except requests.exceptions.ConnectionError as e:
        print(f"Connection Error: {e}")
    except Exception as e:
        print(f"Other Error: {e}")
