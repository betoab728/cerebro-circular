import os
from sqlmodel import SQLModel, create_engine, Session
from dotenv import load_dotenv

load_dotenv()

# Check for DATABASE_URL environment variable (from Render/Neon)
# If not found, fall back to local SQLite
database_url = os.getenv("DATABASE_URL")

if database_url:
    # Postgres connection
    # Fix for some cloud providers using postgres:// instead of postgresql://
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    
    engine = create_engine(database_url, echo=True, pool_pre_ping=True)
    print(f"--- DATABASE CONNECTION: POSTGRESQL ({database_url.split('@')[0]}...) ---")
else:
    # Local SQLite connection
    sqlite_file_name = "database.db"
    sqlite_url = f"sqlite:///{sqlite_file_name}"
    connect_args = {"check_same_thread": False}
    engine = create_engine(sqlite_url, connect_args=connect_args)
    print(f"--- DATABASE CONNECTION: SQLITE (Local Fallback) ---")

def get_session():
    with Session(engine) as session:
        yield session
