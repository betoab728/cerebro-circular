import google.generativeai as genai
import os
from dotenv import load_dotenv
from PIL import Image
import io
import json

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-flash-latest')

# Create a small blank image for testing (red square)
image = Image.new('RGB', (100, 100), color = 'red')

print(f"Testing Gemini Vision with synthetic image...")

try:
    prompt = """
    Analyze this image. Return strictly valid JSON:
    { "materialName": "String", "confidence": Number }
    """
    
    print("Sending to Gemini...")
    response = model.generate_content([prompt, image])
    
    print("--- RAW RESPONSE ---")
    print(response.text)
    print("--------------------")

except Exception as e:
    print(f"FATAL ERROR: {e}")
