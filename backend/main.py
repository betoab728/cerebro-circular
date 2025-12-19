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
from utils.report_generator import generate_pdf_report
from models import AnalysisResult

# Load environment variables
load_dotenv()

app = FastAPI(title="CEREBRO CIRCULAR API", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Database
@app.on_event("startup")
def on_startup():
    SQLModel.metadata.create_all(engine)

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
        "elemental": [ {"label": "String (e.g., 'C (Carbono)')", "value": Number, "trace": Boolean} ],
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
