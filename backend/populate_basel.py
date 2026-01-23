import json
from sqlmodel import Session, select
from models import BaselCatalog
from database import engine
import os

def populate():
    # Ensure table exists
    from sqlmodel import SQLModel
    SQLModel.metadata.create_all(engine)
    
    json_path = os.path.join(os.path.dirname(__file__), "basel_catalog.json")
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    with Session(engine) as session:
        for item in data:
            # Check if exists
            statement = select(BaselCatalog).where(BaselCatalog.codigo == item["codigo"])
            existing = session.exec(statement).first()
            if not existing:
                catalog_item = BaselCatalog(
                    codigo=item["codigo"],
                    descripcion=item["descripcion"]
                )
                session.add(catalog_item)
            else:
                existing.descripcion = item["descripcion"]
                session.add(existing)
        
        session.commit()
        print(f"Successfully populated {len(data)} Basel codes.")

if __name__ == "__main__":
    populate()
