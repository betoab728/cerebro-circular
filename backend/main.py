from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import os
import io
import json
import google.generativeai as genai
from dotenv import load_dotenv
import pypdf
from PIL import Image
from sqlmodel import SQLModel
from database import engine
from routers import auth
from utils.report_generator import generate_pdf_report, generate_predictive_report
from models import AnalysisResult, PredictiveAnalysisResult, User

# Load environment variables
load_dotenv()

app = FastAPI(title="CEREBRO CIRCULAR API", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://cerebro-circular.vercel.app",
        "*"
    ], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/report")
async def get_report(data: AnalysisResult):
    try:
        pdf_buffer = generate_pdf_report(data)
        return StreamingResponse(
            pdf_buffer, 
            media_type="application/pdf", 
            headers={"Content-Disposition": f"attachment; filename=technical_report_{data.materialName}.pdf"}
        )
    except Exception as e:
        print(f"Report Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Report Generation Failed: {str(e)}")

@app.post("/predictive-report")
async def get_predictive_report(data: PredictiveAnalysisResult):
    try:
        pdf_buffer = generate_predictive_report(data)
        return StreamingResponse(
            pdf_buffer, 
            media_type="application/pdf", 
            headers={"Content-Disposition": f"attachment; filename=prediccion_inteligente_{data.productOverview.productName}.pdf"}
        )
    except Exception as e:
        print(f"Predictive Report Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Report Generation Failed: {str(e)}")

# Initialize Database
@app.on_event("startup")
def on_startup():
    print("Startup: Creating database tables...")
    try:
        SQLModel.metadata.create_all(engine)
        print("Startup: Tables created successfully!")
    except Exception as e:
        print(f"Startup Error: Failed to create tables: {e}")

# Include Routers
app.include_router(auth.router)

# Initialize Gemini
# Ensure GOOGLE_API_KEY is set in your .env file
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Use a model that supports both text and vision
# Falling back to flash which is widely available and fast
model = genai.GenerativeModel('gemini-flash-latest')

@app.get("/")
def read_root():
    return {"message": "CEREBRO CIRCULAR Backend Online (Gemini Powered)"}

@app.post("/analyze", response_model=AnalysisResult)
async def analyze_waste(file: UploadFile = File(...), type: str = Form("technical")):
    print(f"Processing file: {file.filename} of type: {type}")
    
    if not os.getenv("GOOGLE_API_KEY"):
         raise HTTPException(status_code=500, detail="GOOGLE_API_KEY not configured on server.")

    content = await file.read()
    
    # Prompt for JSON generation
    prompt_text = """
    You are an expert Material Scientist. Analyze the input to identify the waste material.
    Return strictly valid JSON matching this schema:
    {
        "materialName": "String",
        "category": "String",
        "confidence": Number (0-100),
        "physicochemical": [ {"name": "String", "value": "String", "method": "String"} ],
        "elemental": [ {"label": "String (e.g., 'C (Carbono)')", "value": Number, "description": "String (e.g. 'Base polimérica')", "trace": Boolean} ],
        "elementalSummary": "String (Friendly paragraph explaining the chemical composition to a non-expert)",
        "engineeringContext": { "structure": "String", "processability": "String", "impurities": "String" },
        "valorizationRoutes": [ {"role": "String", "method": "String", "output": "String", "score": Number (0-100)} ]
    }
    Translate values to Spanish.
    """

    generation_parts = [prompt_text]

    try:
        if type == "photo":
            # Image Analysis
            image_stream = io.BytesIO(content)
            image = Image.open(image_stream)
            generation_parts.append(image)
            generation_parts.append("Analyze this waste image.")
            
        elif type == "technical" or type == "security":
            # PDF Analysis
            try:
                pdf_file = io.BytesIO(content)
                reader = pypdf.PdfReader(pdf_file)
                extracted_text = ""
                for page in reader.pages:
                    extracted_text += page.extract_text() + "\n"
                
                extracted_text = extracted_text[:20000] # Cap roughly
                generation_parts.append(f"Technical Document Content:\n{extracted_text}")
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Failed to read PDF: {str(e)}")
        else:
            raise HTTPException(status_code=400, detail="Invalid analysis type")

        # Generate content
        response = model.generate_content(
            generation_parts,
            generation_config=genai.types.GenerationConfig(
                response_mime_type="application/json"
            )
        )
        
        result_text = response.text
        print(f"Raw Gemini Response: {result_text}") # Debugging

        # Cleanup markdown code blocks if present (common with LLMs)
        if result_text.startswith("```json"):
            result_text = result_text[7:]
        if result_text.startswith("```"):
            result_text = result_text[3:]
        if result_text.endswith("```"):
            result_text = result_text[:-3]
        
        result_json = json.loads(result_text.strip())
        return result_json

    except Exception as e:
        print(f"Gemini Error Details: {str(e)}")
        # Return meaningful error to frontend
        raise HTTPException(status_code=500, detail=f"AI Processing Failed: {str(e)}")


@app.post("/predictive-analysis", response_model=PredictiveAnalysisResult)
async def predictive_analysis(
    image: UploadFile = File(...),
    document: UploadFile = File(...)
):
    print(f"Starting Predictive Analysis with Image: {image.filename} and Document: {document.filename}")
    
    if not os.getenv("GOOGLE_API_KEY"):
         raise HTTPException(status_code=500, detail="GOOGLE_API_KEY not configured on server.")

    try:
        # 1. Read Inputs
        image_content = await image.read()
        pdf_content = await document.read()

        # 2. Process Image
        image_stream = io.BytesIO(image_content)
        img_pil = Image.open(image_stream)

        # 3. Process PDF
        try:
            pdf_file = io.BytesIO(pdf_content)
            reader = pypdf.PdfReader(pdf_file)
            extracted_text = ""
            for page in reader.pages:
                extracted_text += page.extract_text() + "\n"
            extracted_text = extracted_text[:30000] # Cap for context window
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to read PDF: {str(e)}")

        # 4. Construct Multi-modal Prompt
        prompt_text = """
        ACT AS: Expert AI Engine for Classification and Regulatory Management of Health Sector Waste in Peru.
        CONTEXT: You analyze hospital materials/supplies when they become waste, using visual evidence and technical data (FDS/MSDS).
        PRIORITY: Correct classification and strict adherence to NTS N.° 199-MINSA/DIGESA (RM 1295-2018-MINSA).
        
        CRITICAL RULES:
        1. DO NOT propose valorization/recycling if the regulation prohibits it (Class A/Biocontaminated or Class B/Special).
        2. Commercial or environmental criteria are SECONDARY to sanitary regulations.
        3. Compliance with MINAM and DIGEMID/IPEN regulations.

        BEHAVIOR:
        Step 1: IDENTIFICATION (From image + PDF)
        - Material: Plastic, glass, metal, paper, mixed.
        - Usage: Patient contact, lab, pharmacy, cleaning.
        - Contamination: Blood, fluids, sharps, chemical residues.
        - Hazard (GHS): Toxic, corrosive, flammable, etc.
        - Condition: Clean, used, expired.

        Step 2: SANITARY DECISION (CLASSIFICATION)
        - Class A (Biocontaminated): Contact with biological fluids/tissues/sharps.
        - Class B (Special): Chemical/Pharma/Radioactive risk (even without bio contact).
        - Class C (Common): Safe, clean, admin/logistics usage ONLY. If in doubt -> Classify as Hazardous.

        Step 3: VALORIZATION (RESTRICTIVE RULE)
        - Class A or B -> VALORIZATION PROHIBITED.
        - Class C -> Optional (via authorized EO-RS). Never reuse direct in EESS.

        Step 4: FINAL DISPOSAL
        - Class A: Treatment (autoclave/incineration) + Final Disposal.
        - Class B: Specialized treatment.
        - Class C: Municipal disposal or Valorization.

        OUTPUT: Return strictly valid JSON matching this schema. MAPPING INSTRUCTIONS:
        {
          "productOverview": {
             "productName": "String (Commercial Name + Status)",
             "detectedPackaging": "String (Material Type)",
             "detectedContent": "String (Usage context & Contaminant evidence)"
          },
          "lifecycleMetrics": {
             "estimatedLifespan": "String (Condition: Used/Expired/Clean)",
             "durabilityScore": Number (0-100. NOTE: If Class A/B, set to 0 as it must be destroyed)",
             "disposalStage": "String (Step 4 Requirement, e.g., 'Tratamiento por Incineración')"
          },
          "environmentalImpact": {
             "carbonFootprintLevel": "String (Low/Medium/High - considering treatment)",
             "recycledContentPotential": "String (e.g., 'PROHIBIDO por NTS 199' for Class A/B, or potential for Class C)",
             "hazardLevel": "String (STRICTLY: 'Clase A - Biocontaminado', 'Clase B - Especial', or 'Clase C - Común')"
          },
          "economicAnalysis": {
             "recyclingViability": "String ('NULA (Prohibido)' for Class A/B, or 'Alta/Media' for Class C)",
             "estimatedRecyclingValue": "String (e.g., 'S/. 0.00 (Residuo Peligroso)' or market value for Class C)",
             "costBenefitAction": "String (Compliance Action: e.g., 'Segregar en Bolsa Roja/Amarilla')"
          },
          "circularStrategy": {
             "recommendedRoute": "String (e.g., 'Destrucción Controlada' for Class A/B, 'Reciclaje' for Class C)",
             "justification": "String (Cite NTS N.° 199-MINSA/DIGESA and reasons)"
          }
        }
        Translate string values to Spanish. Return ONLY valid JSON.
        """

        generation_parts = [
            prompt_text,
            "--- PRODUCT IMAGE ---",
            img_pil,
            "--- TECHNICAL DOCUMENT CONTENT ---",
            extracted_text
        ]

        # 5. Generate with Gemini
        response = model.generate_content(
            generation_parts,
            generation_config=genai.types.GenerationConfig(
                response_mime_type="application/json"
            )
        )
        
        result_text = response.text
        print(f"Gemini Predictive Response: {result_text}")

        # Cleanup
        if result_text.startswith("```json"): result_text = result_text[7:]
        if result_text.startswith("```"): result_text = result_text[3:]
        if result_text.endswith("```"): result_text = result_text[:-3]

        parsed_json = json.loads(result_text.strip())
        return parsed_json

    except Exception as e:
        print(f"Predictive Analysis Failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analysis Failed: {str(e)}")

async def get_report(data: AnalysisResult):
    try:
        pdf_buffer = generate_pdf_report(data)
        return StreamingResponse(
            pdf_buffer, 
            media_type="application/pdf", 
            headers={"Content-Disposition": f"attachment; filename=technical_report_{data.materialName}.pdf"}
        )
    except Exception as e:
        print(f"Report Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Report Generation Failed: {str(e)}")
