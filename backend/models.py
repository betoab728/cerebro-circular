from typing import List, Optional
from sqlmodel import Field, SQLModel
from pydantic import BaseModel

class UserBase(SQLModel):
    email: str = Field(index=True, unique=True)
    full_name: str | None = None
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
