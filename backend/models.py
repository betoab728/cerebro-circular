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

from sqlalchemy import Text, Column

class Residuo(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    responsable: str
    unidad_generadora: str
    tipo_residuo: str
    caracteristica: str
    cantidad: float
    unidad_medida: str
    volumen: Optional[float] = Field(default=None)
    peso_total: float
    frecuencia: Optional[str] = Field(default=None)
    fecha_registro: datetime = Field(default_factory=datetime.now)
    
    # AI Analysis Fields - Using Text for long content
    analysis_material_name: Optional[str] = Field(default=None)
    analysis_physicochemical: Optional[str] = Field(default=None, sa_column=Column(Text))
    analysis_elemental: Optional[str] = Field(default=None, sa_column=Column(Text))
    analysis_engineering: Optional[str] = Field(default=None, sa_column=Column(Text))
    analysis_valorization: Optional[str] = Field(default=None, sa_column=Column(Text))
    
    # Financial Estimates
    costo_disposicion_final: Optional[float] = Field(default=0.0)
    ingreso_economia_circular: Optional[float] = Field(default=0.0)

class PredictiveRegistration(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    fecha: datetime
    responsable: str
    area_solicitante: str
    producto: str
    cantidad: float
    descripcion: str
    valor_economico_unitario: float
    valor_economico_total: float
    tipo_valor_ambiental: str  # reciclable, reutilizable, reaprovechable
    analysis_snapshot: Optional[str] = Field(default=None, sa_column=Column(Text))  # Store JSON as text

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
    
    # Financials
    disposalCost: float
    circularIncome: float

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
