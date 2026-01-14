import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

database_url = os.getenv("DATABASE_URL")

if not database_url:
    print("Error: DATABASE_URL not found in environment.")
    exit(1)

if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

def migrate():
    print(f"Connecting to database...")
    engine = create_engine(database_url)
    
    with engine.connect() as conn:
        try:
            print("Adding costo_disposicion_final...")
            conn.execute(text("ALTER TABLE residuo ADD COLUMN IF NOT EXISTS costo_disposicion_final FLOAT DEFAULT 0.0"))
            conn.commit()
            print("costo_disposicion_final added.")
        except Exception as e:
            print(f"Error adding costo_disposicion_final: {e}")
            
        try:
            print("Adding ingreso_economia_circular...")
            conn.execute(text("ALTER TABLE residuo ADD COLUMN IF NOT EXISTS ingreso_economia_circular FLOAT DEFAULT 0.0"))
            conn.commit()
            print("ingreso_economia_circular added.")
        except Exception as e:
            print(f"Error adding ingreso_economia_circular: {e}")

    print("Migration complete.")

if __name__ == "__main__":
    migrate()
