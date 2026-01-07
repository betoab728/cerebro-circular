import os

env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")

if os.path.exists(env_path):
    print(f"Reading {env_path}...")
    try:
        # Read with utf-8-sig to automatically handle/remove BOM
        with open(env_path, 'r', encoding='utf-8-sig') as f:
            content = f.read()
        
        # Write back with utf-8 (no BOM)
        with open(env_path, 'w', encoding='utf-8') as f:
            f.write(content)
            
        print("Successfully removed BOM and saved .env as UTF-8.")
    except Exception as e:
        print(f"Error: {e}")
else:
    print(".env not found.")
