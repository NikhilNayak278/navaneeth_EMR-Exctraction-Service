import requests
from PIL import Image, ImageDraw, ImageFont
import io

def create_dummy_image():
    """Creates a dummy medical image with text."""
    img = Image.new('RGB', (400, 200), color = (255, 255, 255))
    d = ImageDraw.Draw(img)
    
    # Text to be OCR'd
    text = "Patient: John Doe\nDOB: 01/01/1980\nDiagnosis: Hypertension\nPrescription: Lisinopril 10mg"
    
    # minimal font handling (default bitmap font if no ttf)
    d.text((10,10), text, fill=(0,0,0))
    
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    img_byte_arr.name = 'test_image.png'
    return img_byte_arr

def test_service():
    url = "http://127.0.0.1:8000/extract"
    
    print("Generating test image...")
    # img_bytes = create_dummy_image()
    img_name = 'report.png'
    img_bytes = open(img_name, 'rb')
    
    files = {'file': (img_name, img_bytes, f'image/{img_name.split(".")[1]}')}
    
    print(f"Sending request to {url}...")
    try:
        # Added use_gemini=True to use the Gemini model as requested
        params = {'use_gemini': True}
        response = requests.post(url, files=files, params=params)
        if response.status_code == 200:
            print("\n--- Success! ---")
            print("Response JSON:")
            print(response.json().get('entities'))
            # print(response.json().get('Lab_value'))
            # print(response.json().get('Sign_symptoms'))
        else:
            print(f"\n--- Failed ---")
            print(f"Status Code: {response.status_code}")
            print(f"Detail: {response.text}")
    except requests.exceptions.ConnectionError:
        print(f"\n--- Connection Error ---")
        print("Make sure the service is running! (uvicorn app.main:app --reload)")

if __name__ == "__main__":
    test_service()
