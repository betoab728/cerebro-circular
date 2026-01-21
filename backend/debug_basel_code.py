
import os
import json
import asyncio
import google.generativeai as genai
from dotenv import load_dotenv
from PIL import Image
import io

# Load .env from the backend directory
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

# Configure Gemini
api_key = os.getenv("GOOGLE_API_KEY")
print(f"Loaded API Key: {api_key[:5]}...{api_key[-5:] if api_key else 'None'}")
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-1.5-flash-latest')

async def test_analyze_prompt():
    prompt_text = """
    You are an expert Material Scientist and Circular Economy consultant. 
    Analyze the input to identify the waste material. 
    
    Return strictly valid JSON matching this schema:
    {
        "materialName": "String",
        "category": "String (Peligroso / No Peligroso / Especial)",
        "baselCode": "String (MANDATORY: Basel Convention code, e.g., A1180, B3010, Y46)",
        "confidence": Number (0-100),
        "physicochemical": [ {"name": "String", "value": "String", "method": "String"} ],
        "elemental": [ {"label": "String (e.g., 'C (Carbono)')", "value": Number, "description": "String", "trace": Boolean} ],
        "elementalSummary": "String",
        "engineeringContext": { 
            "structure": "String", 
            "processability": "String", 
            "impurities": "String" 
        },
        "valorizationRoutes": [ {
            "role": "String", 
            "method": "String", 
            "output": "String", 
            "score": Number (0-100)
        } ]
    }
    
    INSTRUCTIONS:
    1. SCALING SENSITIVITY: Assess technical properties and valorization based on quantity.
    2. BASEL CONVENTION (CRITICAL): Assign the correct 'baselCode' from the Basel Convention Annexes.
       - Use List A (e.g., A1010, A1180) for hazardous waste.
       - Use List B (e.g., B1010, B3010) for non-hazardous/recyclable waste.
       - If unclear, use the most specific code applicable to the material's chemical nature.
    3. MATERIAL ID: Use user description and visual cues to identify the material.
    4. VALORIZATION: Focus on high-impact circular alternatives.
    5. Translate all string values to Spanish (except baselCode).
    """

    # Test with a common hazardous waste: Lead-acid battery
    test_material = "Batería de plomo-ácido usada"
    print(f"Testing with: {test_material}")
    
    response = model.generate_content(
        [prompt_text, f"Identify this waste: {test_material}"],
        generation_config=genai.types.GenerationConfig(
            response_mime_type="application/json"
        )
    )
    
    print("\n--- AI Response ---")
    print(response.text)
    
    try:
        data = json.loads(response.text)
        if "baselCode" in data:
            print(f"\n✅ Basel Code detected: {data['baselCode']}")
        else:
            print("\n❌ Basel Code field missing in response.")
    except Exception as e:
        print(f"\n❌ Failed to parse JSON: {e}")

if __name__ == "__main__":
    asyncio.run(test_analyze_prompt())
