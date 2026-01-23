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

def get_response_text(response) -> str:
    """Safely extracts text from response, handling quick accessor errors on truncation."""
    try:
        return response.text
    except Exception:
        # Fallback for when 'finish_reason' is MAX_TOKENS (2) or SAFETY (3)
        if response.candidates and response.candidates[0].content.parts:
            return response.candidates[0].content.parts[0].text
        return ""

def repair_truncated_json(text: str) -> str:
    """
    Aggressively attempts to repair a truncated JSON string for a 'records' list.
    """
    try:
        # 1. Basic cleanup
        text = text.strip()
        
        # 2. If it's empty, we can't do much
        if not text: return text

        # 3. Find the last "}," which signifies a complete object in the list
        last_item_end = text.rfind("},")
        if last_item_end != -1:
            return text[:last_item_end + 1] + "]}"
        
        # 4. If no "}," maybe it cut off during the very first record? 
        # Or at the end of the last record without a comma?
        last_brace = text.rfind("}")
        if last_brace != -1:
            # Check if this brace is after the "records": [ part
            records_start = text.find('"records"')
            if records_start != -1 and last_brace > records_start:
                return text[:last_brace + 1] + "]}"
        
        # 5. Fallback: just try to close everything if we have the start
        if '"records"' in text and "[" in text:
            # If we don't even have a closing brace, it's very badly truncated
            # but we can try to close the current object if it has some fields.
            return text + '}]}' 
            
        return text
    except Exception as e:
        print(f"JSON Repair Failed: {e}")
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
        # Read PDF and Split into Chunks (e.g., 4 pages at a time)
        pdf_file = io.BytesIO(content)
        reader = pypdf.PdfReader(pdf_file)
        all_records = []
        chunk_size = 1  # Process 1 page at a time for maximum accuracy and token space
        total_pages = len(reader.pages)
        print(f"DEBUG: Total PDF Pages: {total_pages}")

        # Common Prompt Config
        prompt_text = """
        Eres un experto en valorización de residuos y economía circular.
        TU MISIÓN: Extraer TODAS las filas del PDF. El documento incluye una COLUMNA DE NUMERACIÓN (Item #). 
        REGLA DE ORO: No te saltes ningún número correlativo. Si la página tiene del ítem 1 al 20, debes generar exactamente 20 objetos JSON en el array 'records'.
        SCHEMA: {"records": [{"razon_social": str, "planta": str, "departamento": str, "tipo_residuo": str, "codigo_basilea": str, "caracteristica": str, "cantidad": float, "unidad_medida": str, "peso_total": float, "analysis_material_name": str, "analysis_physicochemical": list, "analysis_elemental": list, "analysis_engineering": dict, "analysis_valorization": list, "proceso_tratamiento": str, "viabilidad_ec": int}]}
        IMPORTANTE: Usa la numeración para asegurar que tu lista sea completa. En 'proceso_tratamiento', propone rutas de VALORIZACIÓN técnica.
        """

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
                            "analysis_physicochemical": {"type": "ARRAY", "items": {"type": "OBJECT", "properties": {"name": {"type": "STRING"}, "value": {"type": "STRING"}, "method": {"type": "STRING"}}}},
                            "analysis_elemental": {"type": "ARRAY", "items": {"type": "OBJECT", "properties": {"label": {"type": "STRING"}, "value": {"type": "NUMBER"}, "description": {"type": "STRING"}, "trace": {"type": "BOOLEAN"}}}},
                            "analysis_engineering": {"type": "OBJECT", "properties": {"structure": {"type": "STRING"}, "processability": {"type": "STRING"}, "impurities": {"type": "STRING"}}},
                            "analysis_valorization": {"type": "ARRAY", "items": {"type": "OBJECT", "properties": {"role": {"type": "STRING"}, "method": {"type": "STRING"}, "output": {"type": "STRING"}, "score": {"type": "NUMBER"}}}},
                            "proceso_tratamiento": {"type": "STRING"},
                            "viabilidad_ec": {"type": "NUMBER"}
                        },
                        "required": ["tipo_residuo", "peso_total"]
                    }
                }
            },
            "required": ["records"]
        }

        import time

        for i in range(0, total_pages, chunk_size):
            chunk_pages = reader.pages[i : i + chunk_size]
            extracted_text = ""
            current_chunk_label = f"Pages {i+1}-{min(i+chunk_size, total_pages)}"
            
            for page_idx, page in enumerate(chunk_pages):
                text = page.extract_text() or ""
                extracted_text += text + "\n"
                print(f"DEBUG: Page {i + page_idx + 1} extracted length: {len(text)}")
            
            if not extracted_text.strip():
                print(f"DEBUG: Skipping {current_chunk_label} - No text found.")
                continue

            # NEW: Retry loop for each chunk
            max_retries = 3
            parsed_json = {"records": []}
            success = False

            for attempt in range(max_retries):
                try:
                    print(f"DEBUG: Processing {current_chunk_label} (Attempt {attempt+1}/{max_retries})")
                    generation_parts = [prompt_text, f"TEXTO DEL REPORTE:\n{extracted_text}"]

                    # Attempt 1: Strict Schema
                    response = model.generate_content(
                        generation_parts,
                        generation_config=genai.types.GenerationConfig(
                            response_mime_type="application/json",
                            response_schema=batch_analysis_schema,
                            max_output_tokens=8192
                        )
                    )
                    
                    # Check for safety blocks
                    if not response.parts and not response.candidates:
                         raise ValueError("Gemini blocked response (Safety/Other)")

                    result_text = get_response_text(response)
                    cleaned_text = result_text.strip()
                    if cleaned_text.startswith("```json"): cleaned_text = cleaned_text[7:]
                    if cleaned_text.startswith("```"): cleaned_text = cleaned_text[3:]
                    if cleaned_text.endswith("```"): cleaned_text = cleaned_text[:-3]

                    try:
                        parsed_json = json.loads(cleaned_text.strip())
                    except json.JSONDecodeError:
                        print(f"DEBUG: {current_chunk_label} JSON truncated. Repairing...")
                        repaired_text = repair_truncated_json(cleaned_text)
                        parsed_json = json.loads(repaired_text)
                    
                    success = True
                    time.sleep(1) # Extra safety delay between successful page calls
                    break # Exit retry loop on success

                except Exception as e:
                    error_str = str(e)
                    print(f"DEBUG: Error in {current_chunk_label} (Attempt {attempt+1}): {error_str}")
                    
                    if "429" in error_str or "quota" in error_str.lower():
                        wait_time = (attempt + 1) * 2
                        print(f"DEBUG: Rate limit hit. Waiting {wait_time}s...")
                        time.sleep(wait_time)
                    elif attempt == max_retries - 1:
                        print(f"DEBUG: Max retries reached for {current_chunk_label}. Skipping data.")
                    else:
                        time.sleep(1) # General small wait

            # Consolidate results if we got anything
            if success and "records" in parsed_json and isinstance(parsed_json["records"], list):
                chunk_records = 0
                for record in parsed_json["records"]:
                    # Ensure default values
                    record.setdefault("analysis_material_name", "Material no identificado")
                    
                    # Map 'proceso_tratamiento' to 'oportunidades_ec' (existing DB field)
                    if "proceso_tratamiento" in record:
                        record["oportunidades_ec"] = record.pop("proceso_tratamiento")
                    else:
                        record.setdefault("oportunidades_ec", "Tratamiento no especificado")
                        
                    record.setdefault("viabilidad_ec", 0)
                    
                    # Stringify for DB
                    for field in ["analysis_physicochemical", "analysis_elemental", "analysis_engineering", "analysis_valorization"]:
                        if field in record:
                            record[field] = json.dumps(record[field])
                    all_records.append(record)
                    chunk_records += 1
                print(f"DEBUG: Success for {current_chunk_label}. Records found: {chunk_records}")

        print(f"DEBUG: Final Count: {len(all_records)} records from {total_pages} pages.")
        return {"records": all_records}

    except Exception as e:
        print(f"Batch Analysis CRITICAL Failure: {str(e)}")
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

