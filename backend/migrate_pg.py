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
    print(f"Connecting to PostgreSQL...")
    engine = create_engine(database_url)
    
    columns_to_add = [
        ("analysis_material_name", "TEXT"),
        ("analysis_physicochemical", "TEXT text"), # In Postgres it's just TEXT
        ("analysis_elemental", "TEXT"),
        ("analysis_engineering", "TEXT"),
        ("analysis_valorization", "TEXT"),
        ("razon_social", "TEXT"),
        ("planta", "TEXT"),
        ("departamento", "TEXT"),
        ("codigo_basilea", "TEXT")
    ]

    with engine.connect() as conn:
        for col_name, col_type in columns_to_add:
            try:
                # Need to handle 'TEXT text' fix, actually just use TEXT
                actual_type = "TEXT"
                print(f"Adding column {col_name}...")
                conn.execute(text(f"ALTER TABLE residuo ADD COLUMN IF NOT EXISTS {col_name} {actual_type}"))
                conn.commit()
                print(f"Column {col_name} checked/added successfully.")
            except Exception as e:
                print(f"Error handling column {col_name}: {e}")

    print("PostgreSQL Migration complete.")

if __name__ == "__main__":
    migrate()
