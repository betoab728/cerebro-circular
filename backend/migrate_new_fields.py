import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

database_url = os.getenv("DATABASE_URL")

if not database_url:
    print("Error: DATABASE_URL not found in environment. Falling back to SQLite...")
    database_url = "sqlite:///database.db"
else:
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)

def migrate():
    print(f"Connecting to database...")
    engine = create_engine(database_url)
    
    # New columns added in recent updates
    columns_to_add = [
        ("oportunidades_ec", "TEXT"),
        ("viabilidad_ec", "FLOAT")
    ]

    with engine.connect() as conn:
        for col_name, col_type in columns_to_add:
            try:
                print(f"Adding column {col_name} ({col_type})...")
                # SQLite doesn't support IF NOT EXISTS in ALTER TABLE ADD COLUMN directly in some versions, 
                # but we'll try it for Postgres and handle the error if it fails on SQLite or already exists.
                if "postgresql" in database_url:
                    conn.execute(text(f"ALTER TABLE residuo ADD COLUMN IF NOT EXISTS {col_name} {col_type}"))
                else:
                    # Generic approach for SQLite/Other
                    try:
                        conn.execute(text(f"ALTER TABLE residuo ADD COLUMN {col_name} {col_type}"))
                    except Exception as sl_e:
                        if "duplicate column name" in str(sl_e).lower() or "already exists" in str(sl_e).lower():
                            print(f"Column {col_name} already exists.")
                        else:
                            raise sl_e
                
                conn.commit()
                print(f"Column {col_name} processed successfully.")
            except Exception as e:
                print(f"Error handling column {col_name}: {e}")

    print("Migration complete.")

if __name__ == "__main__":
    migrate()
