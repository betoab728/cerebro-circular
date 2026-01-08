from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select
from database import get_session
from models import Residuo

router = APIRouter(
    prefix="/waste",
    tags=["waste"],
    responses={404: {"description": "Not found"}},
)

@router.post("/generation", response_model=Residuo)
async def create_waste_generation(residuo: Residuo, session: Session = Depends(get_session)):
    try:
        session.add(residuo)
        session.commit()
        session.refresh(residuo)
        return residuo
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to register waste generation: {str(e)}")

@router.get("/generation", response_model=list[Residuo])
async def read_waste_generation(session: Session = Depends(get_session)):
    try:
        # Sort by fecha_registro descending
        statement = select(Residuo).order_by(Residuo.fecha_registro.desc())
        results = session.exec(statement).all()
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch waste generation records: {str(e)}")
