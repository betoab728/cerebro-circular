from typing import List, Optional
from sqlmodel import Field, SQLModel
from pydantic import BaseModel

class UserBase(SQLModel):
    email: str = Field(index=True, unique=True)
    full_name: str | None = None
    role: str = Field(default="user")
    is_active: bool = True

class User(UserBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    hashed_password: str

class UserCreate(UserBase):
    password: str

class UserRead(UserBase):
    id: int

class Token(SQLModel):
    access_token: str
    token_type: str

class TokenData(SQLModel):
    email: str | None = None
    
# Manual User Table Model
from datetime import datetime
class Usuario(SQLModel, table=True):
    __tablename__ = "usuarios"
    id: int | None = Field(default=None, primary_key=True)
    nombre: str = Field(index=True, unique=True)
    clave: str
    fecha_creacion: datetime = Field(default_factory=datetime.now)

class Residuo(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    responsable: str
    unidad_generadora: str
    tipo_residuo: str
    caracteristica: str
    cantidad: float
    unidad_medida: str
    volumen: float
    peso_total: float
    frecuencia: str
    fecha_registro: datetime = Field(default_factory=datetime.now)
    
    # AI Analysis Fields (Optional, stored as JSON strings for simplicity in SQLite/Generic DB)
    analysis_material_name: Optional[str] = None
    analysis_physicochemical: Optional[str] = None # JSON string
    analysis_elemental: Optional[str] = None # JSON string
    analysis_engineering: Optional[str] = None # JSON string
    analysis_valorization: Optional[str] = None # JSON string

# Analysis Models
class PhysicochemicalProp(BaseModel):
    name: str
    value: str
    method: str

class ElementalComp(BaseModel):
    label: str
    value: float
    description: str | None = None
    trace: bool = False

class EngineeringContext(BaseModel):
    structure: str
    processability: str
    impurities: Optional[str] = None

class ValorizationRoute(BaseModel):
    role: str
    method: str
    output: str
    score: float

class AnalysisResult(BaseModel):
    materialName: str
    category: str
    confidence: float
    physicochemical: List[PhysicochemicalProp]
    elemental: List[ElementalComp]
    elementalSummary: str | None = None
    engineeringContext: EngineeringContext
    valorizationRoutes: List[ValorizationRoute]

# Predictive Analysis Models
class ProductOverview(BaseModel):
    productName: str = "Producto Desconocido"
    detectedPackaging: str = "No identificado"
    detectedContent: str = "No identificado"

class LifecycleMetrics(BaseModel):
    estimatedLifespan: str = "Desconocido"
    durabilityScore: float = 0.0
    disposalStage: str = "Desconocido"

class EnvironmentalImpact(BaseModel):
    carbonFootprintLevel: str = "Desconocido"
    recycledContentPotential: str = "Desconocido"
    hazardLevel: str = "Desconocido"

class EconomicAnalysis(BaseModel):
    recyclingViability: str = "Desconocido"
    estimatedRecyclingValue: str = "S/. 0.00"
    costBenefitAction: str = "Sin recomendación"

class CircularStrategy(BaseModel):
    recommendedRoute: str = "Reciclaje General"
    justification: str = "Falta información suficiente para una estrategia específica."

class ComplianceSpec(BaseModel):
    mrsp_applicability: str = "Requerido si es residuo peligroso"
    sigersol_reporting: str = "Declaración Anual obligatoria"
    competent_authority: str = "DIGESA / Municipalidad"

class PredictiveAnalysisResult(BaseModel):
    productOverview: ProductOverview = Field(default_factory=ProductOverview)
    lifecycleMetrics: LifecycleMetrics = Field(default_factory=LifecycleMetrics)
    environmentalImpact: EnvironmentalImpact = Field(default_factory=EnvironmentalImpact)
    economicAnalysis: EconomicAnalysis = Field(default_factory=EconomicAnalysis)
    circularStrategy: CircularStrategy = Field(default_factory=CircularStrategy)
    compliance: ComplianceSpec = Field(default_factory=ComplianceSpec)
