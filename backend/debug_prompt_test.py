
import os
import google.generativeai as genai
from dotenv import load_dotenv
import json

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    print("Error: GOOGLE_API_KEY not found.")
    exit(1)

genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-flash-latest')

prompt_text = """
    You are an expert Material Scientist and Circular Economy consultant. 
    Analyze the input to identify the waste material. 
    
    IMPORTANT CONTEXT FROM USER FORM (Scale matters!):
    - Quantity/Amount: 50 KILOGRAMO
    - Total Weight: 50 kg
    - User Description: Botellas de plástico PET vacías y aplastadas
    - Origin Unit: ALMACEN1

    Return strictly valid JSON matching this schema:
    {
        "materialName": "String",
        "category": "String (Peligroso / No Peligroso / Especial)",
        "confidence": Number (0-100),
        "physicochemical": [ {"name": "String", "value": "String", "method": "String"} ],
        "elemental": [ {"label": "String (e.g., 'C (Carbono)')", "value": Number, "description": "String", "trace": Boolean} ],
        "elementalSummary": "String (Friendly paragraph explaining the chemical composition)",
        "engineeringContext": { 
            "structure": "String (Detailed material structure)", 
            "processability": "String (CRITICAL: Assess how to process THIS SPECIFIC AMOUNT. e.g., 'Apto para prensa industrial' for high volumes)", 
            "impurities": "String" 
        },
        "valorizationRoutes": [ {
            "role": "String", 
            "method": "String", 
            "output": "String", 
            "score": Number (0-100)
        } ],
        "disposalCost": Number (Estimated cost to dispose/process this TOTAL amount in Soles. Positive value.),
        "circularIncome": Number (Estimated POTENTIAL income/saving from circular economy for this TOTAL amount in Soles. Positive value.)
    }
    
    INSTRUCTIONS:
    1. SCALING ECONOMICS: If weight/quantity is high (e.g., >100kg), prioritize industrial recycling routes and bulk sales. If low, focus on local segregation.
    2. MATERIAL ID: Use the user description to help identify the material in the file/photo.
    3. FINANCIALS: Estimate 'disposalCost' (how much it costs to treat/landfill) and 'circularIncome' (how much they could make by selling/recycling). USE PERUVIAN MARKET REALISTIC VALUES in Soles (PEN). If unknown, estimate based on material type and weight.
        - disposalCost: E.g., Landfill cost ~ S/. 0.50/kg, Incineration ~ S/. 3.00/kg.
        - circularIncome: E.g., PET Scrap ~ S/. 1.20/kg, Scrap Metal ~ S/. 0.80/kg.
        - Calculate TOTAL for the provided weight.
    4. Translate all string values to Spanish.
"""

print("Sending prompt to Gemini...")
try:
    response = model.generate_content(
        [prompt_text, "Analyze this description: Botellas de plástico PET vacías."],
        generation_config=genai.types.GenerationConfig(
            response_mime_type="application/json"
        )
    )
    print("\n--- GEMINI RESPONSE ---")
    print(response.text)
    
    data = json.loads(response.text)
    if "disposalCost" in data and "circularIncome" in data:
        print("\n✅ SUCCESS: Financial fields found in response.")
        print(f"Disposal Cost: {data['disposalCost']}")
        print(f"Circular Income: {data['circularIncome']}")
    else:
        print("\n❌ FAILED: Financial fields MISSING in response.")

except Exception as e:
    print(f"\n❌ Error calling Gemini: {e}")
