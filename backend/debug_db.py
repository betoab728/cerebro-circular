import os
import sys
from sqlmodel import create_engine, text
from dotenv import load_dotenv

# Add the current directory to sys.path to make sure we can import from local modules if needed
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
print(f"DEBUG: Loading .env from: {env_path}")
if os.path.exists(env_path):
    print("DEBUG: File exists.")
    try:
        with open(env_path, 'r', encoding='utf-8') as f:
            print(f"DEBUG: First line of file: {f.readline().strip()}")
    except Exception as e:
        print(f"DEBUG: Failed to read file: {e}")
else:
    print("DEBUG: File DOES NOT exist.")

loaded = load_dotenv(env_path, verbose=True)
print(f"DEBUG: load_dotenv returned: {loaded}")


def debug_database_connection():
    database_url = os.getenv("DATABASE_URL")
    
    print("--- Database Debug Info ---")
    if not database_url:
        print("ERROR: DATABASE_URL environment variable is NOT set.")
        print("Using fallback to local SQLite (as per database.py logic)?")
    else:
        # Mask the password for security in logs
        masked_url = database_url
        if "@" in database_url:
            part1 = database_url.split("@")[0]
            part2 = database_url.split("@")[1]
            # simplistic masking, assumes standard format
            if ":" in part1:
                protocol_user = part1.split(":")[0] + ":" + part1.split(":")[1]
                masked_url = f"{protocol_user}:******@{part2}"
        
        print(f"DATABASE_URL found: {masked_url}")
        
    # Replicate logic from database.py for connection creation
    if database_url and database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
        
    if database_url:
        try:
            print("Attempting to connect to the database...")
            engine = create_engine(database_url)
            
            with engine.connect() as connection:
                print("Connection SUCCESSFUL!")
                
                # Check for tables
                print("\nListing existings tables in 'public' schema:")
                result = connection.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"))
                tables = result.fetchall()
                
                if not tables:
                    print("  [!] No tables found in the 'public' schema.")
                else:
                    for table in tables:
                        print(f"  - {table[0]}")
                        
                # Specifically check for 'user' table
                user_table_exists = any(t[0] == 'user' for t in tables)
                if user_table_exists:
                    print("\n[OK] 'user' table EXISTS.")
                    # Optional: Count users
                    try:
                        count = connection.execute(text("SELECT count(*) FROM \"user\"")).scalar()
                        print(f"     -> Contains {count} records.")
                    except Exception as e:
                        print(f"     -> Could not count records: {e}")
                else:
                    print("\n[CRITICAL] 'user' table DOES NOT EXIST.")
                    
        except Exception as e:
            print(f"\n[FATAL] Connection FAILED: {e}")
    else:
        print("\nSkipping connection test because DATABASE_URL is missing.")

if __name__ == "__main__":
    debug_database_connection()
