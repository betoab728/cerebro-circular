import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

database_url = os.getenv("DATABASE_URL")
if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

print(f"Connecting to: {database_url.split('@')[0]}...")

try:
    engine = create_engine(database_url, pool_pre_ping=True)
    with engine.connect() as conn:
        print("Connection successful!")
        
        # Check tables
        result = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"))
        tables = [row[0] for row in result]
        print(f"Tables found: {tables}")
        
        if 'codigo_basilea' in tables:
            count = conn.execute(text("SELECT count(*) FROM codigo_basilea")).scalar()
            print(f"Table 'codigo_basilea' exists with {count} records.")
        
        if 'baselcatalog' in tables:
            count = conn.execute(text("SELECT count(*) FROM baselcatalog")).scalar()
            print(f"Table 'baselcatalog' still exists with {count} records.")
            
except Exception as e:
    print(f"Connection failed: {e}")
