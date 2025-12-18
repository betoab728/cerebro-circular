import google.generativeai as genai
import os
from dotenv import load_dotenv
import pypdf
import json

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    print("ERROR: GOOGLE_API_KEY not found in .env")
    exit(1)

genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-flash-latest')

file_path = r"C:\Users\ELIAS\Downloads\03_MSDS_Empaque_de_Carton_Corrugado_ES_2021.pdf"

print(f"Testing with file: {file_path}")

try:
    # 1. Extract Text
    reader = pypdf.PdfReader(file_path)
    extracted_text = ""
    for page in reader.pages:
        extracted_text += page.extract_text() + "\n"
    
    print(f"Extracted {len(extracted_text)} characters from PDF.")
    
    # 2. Call Gemini
    prompt = """
    Analyze this Technical Datasheet. Return strictly valid JSON matching this schema:
    { "materialName": "String", "confidence": 99 }
    """
    
    print("Sending to Gemini...")
    response = model.generate_content([prompt, extracted_text])
    
    print("--- RAW RESPONSE ---")
    print(response.text)
    print("--------------------")

except Exception as e:
    print(f"FATAL ERROR: {e}")
