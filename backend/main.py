from fastapi import FastAPI, UploadFile, File, HTTPException, Form, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import os
import io
import json
import google.generativeai as genai
from dotenv import load_dotenv
import pypdf
from PIL import Image
from sqlmodel import SQLModel, Session
from database import engine
from routers import auth, waste
from utils.report_generator import generate_pdf_report, generate_predictive_report
from models import AnalysisResult, PredictiveAnalysisResult, User, Residuo, PredictiveRegistration
import asyncio


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

@app.post("/predictive-registry")
async def create_predictive_registry(registry: PredictiveRegistration):
    try:
        with Session(engine) as session:
            session.add(registry)
            session.commit()
            session.refresh(registry)
            return registry
    except Exception as e:
        print(f"Registry Save Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to save registry: {str(e)}")

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
app.include_router(waste.router)

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
async def analyze_waste(
    file: UploadFile = File(...), 
    type: str = Form("technical"),
    context: str = Form(None)
):
    print(f"Processing file: {file.filename} of type: {type}")
    if context:
        print(f"Form Context received: {context}")
    
    if not os.getenv("GOOGLE_API_KEY"):
         raise HTTPException(status_code=500, detail="GOOGLE_API_KEY not configured on server.")

    content = await file.read()
    
    # Base Context from Form
    context_data = {}
    if context:
        try:
            context_data = json.loads(context)
        except:
            pass

    # Prompt for JSON generation
    prompt_text = f"""
    You are an expert Material Scientist and Circular Economy consultant. 
    Analyze the input to identify the waste material. 
    
    IMPORTANT CONTEXT FROM USER FORM (Scale matters!):
    - Quantity/Amount: {context_data.get('cantidad', 'Not specified')} {context_data.get('unidad_medida', '')}
    - Total Weight: {context_data.get('peso_total', 'Not specified')} kg
    - User Description: {context_data.get('caracteristica', 'None')}
    - Origin Unit: {context_data.get('unidad_generadora', 'Unknown')}

    Return strictly valid JSON matching this schema:
    {{
        "materialName": "String",
        "category": "String (Peligroso / No Peligroso / Especial)",
        "confidence": Number (0-100),
        "physicochemical": [ {{"name": "String", "value": "String", "method": "String"}} ],
        "elemental": [ {{"label": "String (e.g., 'C (Carbono)')", "value": Number, "description": "String", "trace": Boolean}} ],
        "elementalSummary": "String (Friendly paragraph explaining the chemical composition)",
        "engineeringContext": {{ 
            "structure": "String (Detailed material structure)", 
            "processability": "String (CRITICAL: Assess how to process THIS SPECIFIC AMOUNT. e.g., 'Apto para prensa industrial' for high volumes)", 
            "impurities": "String" 
        }},
        "valorizationRoutes": [ {{
            "role": "String", 
            "method": "String", 
            "output": "String", 
            "score": Number (0-100)
        }} ],
        "disposalCost": Number (ESTIMATED Total cost in Soles S/ for disposal of this quantity),
        "circularIncome": Number (ESTIMATED Total potential income in Soles S/ from circular economy)
    }}
    
    INSTRUCTIONS:
    1. SCALING ECONOMICS: If weight/quantity is high (e.g., >100kg), prioritize industrial recycling routes and bulk sales. If low, focus on local segregation.
    2. MATERIAL ID: Use the user description to help identify the material in the file/photo.
    3. VALORIZATION: In the 'method' or 'output' of valorizationRoutes, include an ESTIMATED ECONOMIC VALUE in Soles (S/.) per kg or per total batch based on the provided weight.
    4. Translate all string values to Spanish.
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
        Rol
        Eres un motor experto en normativa peruana de residuos del sector salud (NTS 144 + Ley 1278).
        TU OBJETIVO PRINCIPAL: IDENTIFICAR OPORTUNIDADES DE VALORIZACIÓN. NO te limites a la disposición final. Busca SIEMPRE la alternativa de Economía Circular (reciclaje/reaprovechamiento) mediante adecuada segregación o tratamiento previo.

        METODOLOGÍA DE ANÁLISIS (ENFOQUE DE OPORTUNIDAD)

        PASO 1 – DESGLOSE DEL MATERIAL (CRUCIAL)
        Distingue claramente:
        1. EL CONTENIDO (Residuo líquido/químico/biológico)
        2. EL ENVASE (Plástico, vidrío, cartón)
        * ¿El envase puede separarse del contenido? ¿Si se lava/neutraliza, deja de ser peligroso?

        PASO 2 – CLASIFICACIÓN SANITARIA INTELIGENTE (NTS 144)
        - Clase A (Biocontaminado): ¿Realmente todo es A? ¿O solo el contenido? (Ej: Aguja vs Capuchón).
        - Clase B (Especial): ¿El envase vacío de fármaco es peligroso? (Verificar FDS).
        - Clase C (Común): MATERIAL OBJETIVO.
        
        📌 ESTRATEGIA DE RECLASIFICACIÓN:
        Si un material (ej: frasco de suero) es Clase A/B por contenido, EVALÚA:
        "¿Si se vacía y se somete a lavado/desinfección química, el envase pasa a ser Clase C?"
        -> SI LA RESPUESTA ES SÍ, PROPÓN ESTA RUTA.

        PASO 3 – RUTAS DE VALORIZACIÓN (NO TE RINDAS EN LA PRIMERA OPCIÓN)
        Busca alternativas antes que Incineración/Relleno:

        1. RECICLAJE (Prioridad):
           - Plásticos (PE, PP, PET) de sueros/jeringas SIN contacto directo con sangre (o tras desinfección).
           - Vidrio de frascos ampollas (tras trituración/tratamiento).
           - Cartón/Papel de empaques secundarios (siempre reciclar).

        2. TRATAMIENTO PARA VALORIZACIÓN:
           - Esterilización (Autoclave) -> Trituración -> Reciclaje (Como materia prima inerte).
           - Neutralización química -> Vertido seguro del líquido -> Reciclaje del envase.

        3. DISPOSICIÓN (Solo si es imposible valorizar):
           - Incineración / Relleno de Seguridad.

        PASO 4 – DESTINO FINAL RECOMENDADO
        Debes dar la alternativa más circular posible legalmente.
        Ejemplo: "Frasco de Suero" -> NO digas "Incineración". DI: "Vaciar contenido, desinfectar envase (Clase C) y RECICLAR plástico PP".

        PASO 5 – CUMPLIMIENTO LEGAL
        Determina obligaciones (MRSP, SIGERSOL) para la ruta elegida.

        OUTPUT: Return strictly valid JSON matching this schema. MAPPING INSTRUCTIONS:
        {
          "productOverview": {
             "productName": "String (Commercial Name)",
             "detectedPackaging": "String (Detailed Material, e.g. 'PP Rígido')",
             "detectedContent": "String"
          },
          "lifecycleMetrics": {
             "estimatedLifespan": "String",
             "durabilityScore": Number (0-100),
             "disposalStage": "String (e.g. 'Segregación -> Tratamiento -> RECICLAJE')"
          },
          "environmentalImpact": {
             "carbonFootprintLevel": "String",
             "recycledContentPotential": "String (Highlight OPPORTUNITY, e.g. 'Alto potencial tras lavado')",
             "hazardLevel": "String (Initial Classification vs Potential Clean Classification)"
          },
          "economicAnalysis": {
             "recyclingViability": "String (High/Medium/Low - Be Optimistic but Realistic)",
             "estimatedRecyclingValue": "String (INDISPENSABLE: Dar un valor monetario en SOLES S/. por Kg o Unidad. Ej: 'S/. 1.50 por Kg')",
             "costBenefitAction": "String (e.g. 'Rentable segregar para reciclar')"
          },
          "circularStrategy": {
             "recommendedRoute": "String (THE BEST CIRCULAR OPTION)",
             "justification": "String (Explain HOW to achieve this legaly per NTS 144)"
          },
          "compliance": {
             "mrsp_applicability": "String",
             "sigersol_reporting": "String",
             "competent_authority": "String"
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

@app.post("/analyze-batch")
async def analyze_batch(file: UploadFile = File(...)):
    print(f"Processing Batch PDF: {file.filename}")
    
    if not os.getenv("GOOGLE_API_KEY"):
         raise HTTPException(status_code=500, detail="GOOGLE_API_KEY not configured on server.")

    content = await file.read()
    
    try:
        # Read PDF
        pdf_file = io.BytesIO(content)
        reader = pypdf.PdfReader(pdf_file)
        extracted_text = ""
        for page in reader.pages:
            extracted_text += page.extract_text() + "\n"
        
        extracted_text = extracted_text[:40000] # Cap for context window

        prompt_text = """
        Eres un experto en extracción de datos estructurados de documentos de gestión de residuos.
        Analiza el texto extraído de un reporte PDF que contiene una tabla de registros de residuos.
        
        Tu objetivo es extraer cada fila de la tabla y convertirla a un objeto JSON compatible con este esquema:
        {
            "records": [
                {
                    "razon_social": "String (Razón Social)",
                    "planta": "String (Planta)",
                    "departamento": "String (ANCASH, etc)",
                    "tipo_residuo": "String (PELIGROSO / NO PELIGROSO / ESPECIAL / NFU / RAEE / OTROS)",
                    "codigo_basilea": "String (Código de Basilea)",
                    "caracteristica": "String (Descripción del residuo)",
                    "cantidad": Number,
                    "unidad_medida": "String (TONELADAS / KILOGRAMOS / METROS CUBICOS / OTROS)",
                    "peso_total": Number (Calculado en KILOGRAMOS. Si la unidad es Toneladas, multiplica x 1000. Si está en kg ya, dejar igual.)
                }
            ]
        }
        
        INSTRUCCIONES:
        1. Procesa TODAS las filas visibles en el texto.
        2. Mantén la fidelidad de los datos originales.
        3. Si la unidad es Toneladas (o TON), multiplica por 1000 para obtener el peso_total en Kg.
        4. Traduce los tipos de residuo a los valores permitidos (PELIGROSO, NO PELIGROSO, etc).
        5. Devuelve ÚNICAMENTE el JSON.
        """

        generation_parts = [prompt_text, f"TEXTO DEL REPORTE:\n{extracted_text}"]

        response = model.generate_content(
            generation_parts,
            generation_config=genai.types.GenerationConfig(
                response_mime_type="application/json"
            )
        )
        
        result_text = response.text
        if result_text.startswith("```json"): result_text = result_text[7:]
        if result_text.startswith("```"): result_text = result_text[3:]
        if result_text.endswith("```"): result_text = result_text[:-3]

        parsed_json = json.loads(result_text.strip())
        return parsed_json

    except Exception as e:
        print(f"Batch Analysis Failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Batch Analysis Failed: {str(e)}")

@app.post("/save-batch")
async def save_batch(records: list[Residuo], session: Session = Depends(waste.get_session)):
    try:
        saved_count = 0
        for record in records:
            record.id = None
            session.add(record)
            saved_count += 1
        
        session.commit()
        return {"message": f"Successfully saved {saved_count} records", "count": saved_count}
    except Exception as e:
        session.rollback()
        print(f"Save Batch Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to save batch: {str(e)}")

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
