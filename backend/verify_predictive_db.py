from sqlmodel import Session, SQLModel, select
from database import engine
from models import PredictiveRegistration
from datetime import datetime

# Ensure tables are created
print("Creating tables...")
SQLModel.metadata.create_all(engine)

def verify_persistence():
    print("Testing persistence...")
    
    # Create dummy record
    record = PredictiveRegistration(
        fecha=datetime.now(),
        responsable="Test User",
        area_solicitante="Test Area",
        producto="Test Product",
        cantidad=10.5,
        descripcion="Test Description",
        valor_economico_unitario=2.5,
        valor_economico_total=26.25,
        tipo_valor_ambiental="reciclable",
        analysis_snapshot="{}"
    )
    
    try:
        with Session(engine) as session:
            session.add(record)
            session.commit()
            session.refresh(record)
            
            print(f"Record created with ID: {record.id}")
            
            # Read back
            statement = select(PredictiveRegistration).where(PredictiveRegistration.id == record.id)
            retrieved = session.exec(statement).first()
            
            if retrieved:
                print(f"Verified Record: {retrieved.producto} - {retrieved.responsable}")
                return True
            else:
                print("Failed to retrieve record.")
                return False
                
    except Exception as e:
        print(f"Error during verification: {e}")
        return False

if __name__ == "__main__":
    if verify_persistence():
        print("VERIFICATION SUCCESSFUL")
    else:
        print("VERIFICATION FAILED")
