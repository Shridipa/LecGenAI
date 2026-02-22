import gdown
import os

url = "https://drive.google.com/drive/folders/1VEq9gV2QEmVV299_FlgbL38Ds52BpsjT"
output = "drive_test_folder"
os.makedirs(output, exist_ok=True)

print(f"Testing download from: {url}")
try:
    files = gdown.download_folder(url, output=output, quiet=False, use_cookies=False)
    print(f"Returned: {files}")
    print("Files on disk:")
    for root, dirs, f in os.walk(output):
        for file in f:
            print(os.path.join(root, file))
except Exception as e:
    print(f"Error: {e}")
