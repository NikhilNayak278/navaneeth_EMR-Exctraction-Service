import requests
import sys

def test_ollama_service(image_path="report.png"):
    url = "http://127.0.0.1:8000/extract"
    
    print(f"Testing Ollama extraction with image: {image_path}")
    
    try:
        with open(image_path, 'rb') as f:
            img_bytes = f.read()
    except FileNotFoundError:
        print(f"Error: File {image_path} not found.")
        return

    files = {'file': (image_path, img_bytes, 'image/png')}
    # Requesting Ollama extraction
    params = {'use_ollama': 'true'}
    
    print(f"Sending request to {url} with use_ollama=true...")
    try:
        response = requests.post(url, files=files, params=params)
        if response.status_code == 200:
            print("\n--- Success! ---")
            print("Response JSON:")
            print(response.json())
            print("\nEntities:")
            print(response.json().get('entities'))
        else:
            print(f"\n--- Failed ---")
            print(f"Status Code: {response.status_code}")
            print(f"Detail: {response.text}")
    except requests.exceptions.ConnectionError:
        print(f"\n--- Connection Error ---")
        print("Make sure the service is running! (uvicorn app.main:app --reload)")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        test_ollama_service(sys.argv[1])
    else:
        test_ollama_service("report.png")
