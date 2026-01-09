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

engine = create_engine(database_url)

migration_queries = [
    # 1. Make columns nullable
    "ALTER TABLE residuo ALTER COLUMN volumen DROP NOT NULL;",
    "ALTER TABLE residuo ALTER COLUMN frecuencia DROP NOT NULL;",
    
    # 2. Change types to TEXT for long AI content
    "ALTER TABLE residuo ALTER COLUMN analysis_physicochemical TYPE TEXT;",
    "ALTER TABLE residuo ALTER COLUMN analysis_elemental TYPE TEXT;",
    "ALTER TABLE residuo ALTER COLUMN analysis_engineering TYPE TEXT;",
    "ALTER TABLE residuo ALTER COLUMN analysis_valorization TYPE TEXT;"
]

print(f"Connecting to: {database_url.split('@')[0]}...")

with engine.connect() as conn:
    for query in migration_queries:
        try:
            print(f"Executing: {query}")
            conn.execute(text(query))
            conn.commit()
            print("Successfully applied.")
        except Exception as e:
            print(f"Skipped/Failed: {query} (Error: {e})")

print("Migration completed.")
