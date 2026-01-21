import json
from sqlmodel import Session, create_engine, select
from models import BaselCatalog
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")
engine = create_engine(DATABASE_URL)

def populate():
    # Ensure table exists
    from sqlmodel import SQLModel
    SQLModel.metadata.create_all(engine)
    
    with open("backend/basel_catalog.json", "r", encoding="utf-8") as f:
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
