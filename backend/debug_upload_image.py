import requests
from PIL import Image
import io

# Create a dummy image
img = Image.new('RGB', (100, 100), color='green')
img_byte_arr = io.BytesIO()
img.save(img_byte_arr, format='JPEG')
img_byte_arr.seek(0)

url = 'http://127.0.0.1:8000/analyze'
files = {'file': ('test_image.jpg', img_byte_arr, 'image/jpeg')}
data = {'type': 'photo'}

print("Sending POST request to /analyze...")
try:
    response = requests.post(url, files=files, data=data)
    print(f"Status Code: {response.status_code}")
    print("Response Body:")
    print(response.text)
except Exception as e:
    print(f"Request failed: {e}")
