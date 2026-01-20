
import requests
import os

# Create a dummy image for testing if one doesn't exist
def create_dummy_image():
    from PIL import Image
    img = Image.new('RGB', (100, 100), color = 'red')
    img.save('test_image.jpg')
    return 'test_image.jpg'

def test_analyze():
    url = "http://localhost:8000/analyze"
    img_path = create_dummy_image()
    
    files = {'file': open(img_path, 'rb')}
    data = {
        'type': 'photo',
        'context': '{"cantidad": 10, "unidad_medida": "kg"}'
    }
    
    print(f"Sending request to {url}...")
    try:
        response = requests.post(url, files=files, data=data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
    except requests.exceptions.ConnectionError:
        print("ERROR: Connection refused. Is the backend server running?")
    except Exception as e:
        print(f"ERROR: {e}")
    finally:
        if os.path.exists(img_path):
            os.remove(img_path)

if __name__ == "__main__":
    test_analyze()
