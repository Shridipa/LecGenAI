import requests

url = "http://localhost:8000/analyze/pyq"
files = {'files': ('test.txt', 'This is a sample question paper. Q1. What is machine learning? Q2. Explain AI.', 'text/plain')}

try:
    response = requests.post(url, files=files)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
