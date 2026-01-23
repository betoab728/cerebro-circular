from fastapi import FastAPI, UploadFile, File, HTTPException, Form, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import os
import io
import json
import re
import google.generativeai as genai
from dotenv import load_dotenv
import pypdf
from PIL import Image
from sqlmodel import SQLModel, Session, select
from database import engine
from routers import auth, waste
from utils.report_generator import generate_pdf_report, generate_predictive_report
from models import AnalysisResult, PredictiveAnalysisResult, User, Residuo, PredictiveRegistration, BaselCatalog
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

def clean_json_response(response_text: str) -> str:
    """
    Robust cleaning of JSON response from LLM.
    - Extracts distinct JSON block
    - Removes markdown
    - Removes trailing commas which break json.loads
    """
    # 1. Remove markdown code blocks
    text = response_text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()

    # 2. Extract JSON object/list if there's extra text
    # Find the first { or [ and the last } or ]
    start_brace = text.find('{')
    start_bracket = text.find('[')
    
    start_idx = -1
    end_idx = -1

    # Determine start
    if start_brace != -1 and start_bracket != -1:
        start_idx = min(start_brace, start_bracket)
    elif start_brace != -1:
        start_idx = start_brace
    elif start_bracket != -1:
        start_idx = start_bracket
    
    # Determine end (search from right)
    end_brace = text.rfind('}')
    end_bracket = text.rfind(']')
    
    if end_brace != -1 and end_bracket != -1:
        end_idx = max(end_brace, end_bracket)
    elif end_brace != -1:
        end_idx = end_brace
    elif end_bracket != -1:
        end_idx = end_bracket

    if start_idx != -1 and end_idx != -1:
        text = text[start_idx : end_idx + 1]

    # 3. Regex to remove trailing commas
    # Removes , followed by newline/space and } or ]
    text = re.sub(r',\s*}', '}', text)
    text = re.sub(r',\s*]', ']', text)
    
    return text

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
        "baselCode": "String (MANDATORY: Basel Convention code, e.g., A1180, B3010, Y46)",
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
        }} ]
    }}
    
    INSTRUCTIONS:
    1. SCALING SENSITIVITY: Assess technical properties and valorization based on quantity.
    2. BASEL CONVENTION (CRITICAL): Assign the correct 'baselCode' from the Basel Convention Annexes (I, II, VIII, or IX).
       - Examples: A1180 (E-waste), B3010 (Plastic waste), A1010 (Lead batteries), Y46 (Household waste).
       - ALWAYS provide the most specific code. If the material is a common recyclable, use the 'B' series. If hazardous, use 'A' or 'Y'.
       - THIS FIELD IS MANDATORY.
    3. MATERIAL ID: Use user description and visual cues to identify the material.
    4. VALORIZATION: Focus on high-impact circular alternatives.
    5. Translate all string values to Spanish (except baselCode).
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

        # 1. First Pass: Identify Material
        id_prompt = f"""
        Identify the waste material in this input.
        Context: {context_data.get('caracteristica', 'None')}
        Quantity: {context_data.get('cantidad', 'Not specified')}
        Return JSON: {{"materialName": "String", "shortDescription": "String", "isHazardous": Boolean}}
        """
        
        id_response = model.generate_content(
            [id_prompt] + ([image] if type == "photo" else [f"Technical Text: {extracted_text[:5000]}"]),
            generation_config=genai.types.GenerationConfig(response_mime_type="application/json")
        )
        
        id_result = json.loads(id_response.text)
        material_name = id_result.get("materialName", "Waste")
        
        # 2. Search Basel Catalog
        potential_codes = []
        with Session(engine) as session:
            # Search by name or description using SQL ILIKE if possible, or simple filter
            words = material_name.split()
            keywords = [w for w in words if len(w) > 3]
            
            # For simplicity and cross-DB compatibility, we can still do some filtering in Python 
            # but let's at least try to be more efficient.
            # Actually, with 124 rows, the issue isn't the data size, it's the connection stability.
            # I'll add a retry logic if needed, but pool_pre_ping should help.
            
            catalog_items = session.exec(select(BaselCatalog)).all()
            scored_items = []
            for item in catalog_items:
                score = 0
                for kw in keywords:
                    if kw.lower() in item.descripcion.lower() or kw.lower() in item.codigo.lower():
                        score += 1
                if score > 0:
                    scored_items.append((score, item))
            
            scored_items.sort(key=lambda x: x[0], reverse=True)
            potential_codes = [f"{item.codigo}: {item.descripcion}" for _, item in scored_items[:15]]

        # 3. Second Pass: Full Analysis with Catalog Context
        catalog_context = "\n".join(potential_codes) if potential_codes else "No specific matches found in local catalog."
        
        final_prompt = f"""
        {prompt_text}
        
        POTENTIAL BASEL CODES FROM YOUR EXTRACED CATALOG (Annex I, II, VIII, or IX):
        {catalog_context}
        
        Use the catalog above to select the most accurate 'baselCode'. 
        If none fit perfectly, use your general knowledge but prefer the catalog if applicable.
        The identified material is: {material_name}
        """

        response = model.generate_content(
            [final_prompt] + ([image] if type == "photo" else [f"Technical Text: {extracted_text[:20000]}"]),
            generation_config=genai.types.GenerationConfig(
                response_mime_type="application/json"
            )
        )
        
        result_text = response.text
        # Clean response with helper
        cleaned_text = clean_json_response(result_text)
        
        result_json = json.loads(cleaned_text)
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
        cleaned_text = clean_json_response(result_text)

        parsed_json = json.loads(cleaned_text)
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
        Eres un experto Científico de Materiales y Consultor de Economía Circular.
        Tu tarea es doble:
        1. EXTRAER: Identifica cada fila de la tabla de residuos en el texto del reporte PDF.
        2. CARACTERIZAR: Para CADA residuo extraído, realiza un análisis técnico profundo (como si estuvieras analizando una ficha técnica individual).
        
        Tu objetivo es devolver una lista de objetos JSON. Cada objeto debe ser un registro completo compatible con la base de datos (Modelo Residuo).
        
        ESQUEMA REQUERIDO:
        {
            "records": [
                {
                    "razon_social": "String",
                    "planta": "String",
                    "departamento": "String",
                    "tipo_residuo": "String (PELIGROSO / NO PELIGROSO / ESPECIAL / NFU / RAEE / OTROS)",
                    "codigo_basilea": "String",
                    "caracteristica": "String (Descripción original)",
                    "cantidad": Number,
                    "unidad_medida": "String (TONELADAS / KILOGRAMOS / ETC)",
                    "peso_total": Number (En KILOGRAMOS - calcula segun cantidad/unidad),
                    
                    "analysis_material_name": "Nombre científico/claro del material",
                    "analysis_physicochemical": [ {"name": "String", "value": "String", "method": "String"} ],
                    "analysis_elemental": [ {"label": "String", "value": Number, "description": "String", "trace": Boolean} ],
                    "analysis_engineering": { "structure": "String", "processability": "String", "impurities": "String" },
                    "analysis_valorization": [ {"role": "String", "method": "String", "output": "String", "score": Number} ],
                    "oportunidades_ec": "String (Resumen corto de max 15 palabras sobre la mejor oportunidad de EC)",
                    "viabilidad_ec": Number (Porcentaje 0-100 de viabilidad de la oportunidad)
                }
            ]
        }
        
        INSTRUCCIONES DE ANÁLISIS TÉCNICO:
        - Para cada residuo, infiere sus propiedades físico-químicas y composición elemental basándote en su descripción y contexto industrial.
        - En 'analysis_engineering.processability', evalúa específicamente cómo manejar el volumen extraído (peso_total).
        - En 'analysis_valorization', propón rutas de economía circular con puntajes de viabilidad realistas según normativa peruana.
        - En 'oportunidades_ec', redacta un resumen ejecutivo y persuasivo (máximo 15 palabras) de la oportunidad de valorización más rentable.
        - En 'viabilidad_ec', asigna un puntaje de viabilidad (0-100) coherente con el análisis técnico.
        - IMPORTANTE: Devuelve objetos JSON nativos para los campos de análisis, NO cadenas de texto.
        
        Devuelve ÚNICAMENTE el JSON.
        """

        generation_parts = [prompt_text, f"TEXTO DEL REPORTE:\n{extracted_text}"]

        # Define Schema for Strict JSON Output
        batch_analysis_schema = {
            "type": "OBJECT",
            "properties": {
                "records": {
                    "type": "ARRAY",
                    "items": {
                        "type": "OBJECT",
                        "properties": {
                            "razon_social": {"type": "STRING"},
                            "planta": {"type": "STRING"},
                            "departamento": {"type": "STRING"},
                            "tipo_residuo": {"type": "STRING"},
                            "codigo_basilea": {"type": "STRING"},
                            "caracteristica": {"type": "STRING"},
                            "cantidad": {"type": "NUMBER"},
                            "unidad_medida": {"type": "STRING"},
                            "peso_total": {"type": "NUMBER"},
                            "analysis_material_name": {"type": "STRING"},
                            "analysis_physicochemical": {
                                "type": "ARRAY",
                                "items": {
                                    "type": "OBJECT",
                                    "properties": {
                                        "name": {"type": "STRING"},
                                        "value": {"type": "STRING"},
                                        "method": {"type": "STRING"}
                                    }
                                }
                            },
                            "analysis_elemental": {
                                "type": "ARRAY",
                                "items": {
                                    "type": "OBJECT",
                                    "properties": {
                                        "label": {"type": "STRING"},
                                        "value": {"type": "NUMBER"},
                                        "description": {"type": "STRING"},
                                        "trace": {"type": "BOOLEAN"}
                                    }
                                }
                            },
                            "analysis_engineering": {
                                "type": "OBJECT",
                                "properties": {
                                    "structure": {"type": "STRING"},
                                    "processability": {"type": "STRING"},
                                    "impurities": {"type": "STRING"}
                                }
                            },
                            "analysis_valorization": {
                                "type": "ARRAY",
                                "items": {
                                    "type": "OBJECT",
                                    "properties": {
                                        "role": {"type": "STRING"},
                                        "method": {"type": "STRING"},
                                        "output": {"type": "STRING"},
                                        "score": {"type": "NUMBER"}
                                    }
                                }
                            },
                            "oportunidades_ec": {"type": "STRING"},
                            "viabilidad_ec": {"type": "NUMBER"}
                        },
                        "required": ["tipo_residuo", "peso_total"] # Relaxed requirements
                    }
                }
            },
            "required": ["records"]
        }

        schema_error = None
        try:
            print("Attempting Strict Schema Generation...")
            response = model.generate_content(
                generation_parts,
                generation_config=genai.types.GenerationConfig(
                    response_mime_type="application/json",
                    response_schema=batch_analysis_schema,
                    max_output_tokens=8192
                )
            )
            
            # Check for safety blocks or empty responses
            if not response.parts:
                 raise ValueError(f"Gemini blocked response. Finish Reason: {response.candidates[0].finish_reason if response.candidates else 'Unknown'}")

            result_text = response.text
            # response_schema guarantees valid JSON, so strictly load it.
            # However, sometimes it wraps in a code block or has whitespace.
            cleaned_text = result_text.strip() 
            if cleaned_text.startswith("```json"): cleaned_text = cleaned_text[7:]
            if cleaned_text.startswith("```"): cleaned_text = cleaned_text[3:]
            if cleaned_text.endswith("```"): cleaned_text = cleaned_text[:-3]

            parsed_json = json.loads(cleaned_text.strip())

        except Exception as e:
            schema_error = str(e)
            print(f"Schema Generation Failed: {schema_error}. Fallback to Standard Generation + Regex Cleaning.")
            
            try:
                # Fallback to standard generation
                response = model.generate_content(
                    generation_parts,
                    generation_config=genai.types.GenerationConfig(
                        response_mime_type="application/json",
                        max_output_tokens=8192
                    )
                )
                
                result_text = response.text
                cleaned_text = clean_json_response(result_text)
                parsed_json = json.loads(cleaned_text)
            except Exception as fallback_e:
                error_msg = f"Analysis Failed. Strict Error: {schema_error}. Fallback Error: {str(fallback_e)}"
                print(error_msg)
                raise HTTPException(status_code=500, detail=error_msg)

        # Post-process: Stringify complex fields for the DB
        if "records" in parsed_json and isinstance(parsed_json["records"], list):
            for record in parsed_json["records"]:
                if "analysis_physicochemical" in record:
                    record["analysis_physicochemical"] = json.dumps(record["analysis_physicochemical"])
                if "analysis_elemental" in record:
                    record["analysis_elemental"] = json.dumps(record["analysis_elemental"])
                if "analysis_engineering" in record:
                    record["analysis_engineering"] = json.dumps(record["analysis_engineering"])
                if "analysis_valorization" in record:
                    record["analysis_valorization"] = json.dumps(record["analysis_valorization"])
        return parsed_json

    except json.JSONDecodeError as e:
        print(f"JSON Parsing Error: {str(e)}")
        print(f"Truncated Response Tail: {result_text[-500:]}")
        raise HTTPException(status_code=500, detail=f"Analysis Response Truncated or Invalid: {str(e)}")
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

