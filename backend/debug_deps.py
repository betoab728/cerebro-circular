import sys
print("Checking dependencies...")
try:
    import sqlmodel
    print("sqlmodel: OK")
    import passlib
    print("passlib: OK")
    import jose
    print("python-jose: OK")
    from database import engine
    from sqlmodel import SQLModel
    print("Database engine: OK")
    SQLModel.metadata.create_all(engine)
    print("Database creation: OK")
except ImportError as e:
    print(f"MISSING DEPENDENCY: {e}")
    sys.exit(1)
except Exception as e:
    print(f"ERROR: {e}")
    sys.exit(1)
