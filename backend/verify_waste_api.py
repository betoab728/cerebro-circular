from fastapi.testclient import TestClient
from main import app
from models import Residuo
import json

client = TestClient(app)

def test_waste_generation_flow():
    print("Testing Waste Generation API...")

    with TestClient(app) as client:
        # Data payload matching the form
        payload = {
            "responsable": "Juan Perez",
            "unidad_generadora": "MANTENIMIENTO",
            "tipo_residuo": "PELIGRO",
            "caracteristica": "Aceite usado de motor",
            "cantidad": 5.5,
            "unidad_medida": "KILOGRAMO",
            "volumen": 0.02,
            "peso_total": 5.5,
            "frecuencia": "Semanal"
        }

        print(f"Sending POST request with payload: {json.dumps(payload, indent=2)}")

        # 1. Test POST /waste/generation
        response = client.post("/waste/generation", json=payload)
        
        if response.status_code == 200:
            print("✅ POST Success! Response:")
            print(response.json())
            created_id = response.json()["id"]
        else:
            print(f"❌ POST Failed: {response.status_code}")
            print(response.text)
            return

        # 2. Test GET /waste/generation
        print("\nTesting GET List...")
        response_get = client.get("/waste/generation")
        
        if response_get.status_code == 200:
            items = response_get.json()
            print(f"✅ GET Success! Found {len(items)} items.")
            
            # Verify our item is there
            found = False
            for item in items:
                if item["id"] == created_id:
                    print(f"✅ Verified item {created_id} is present in list.")
                    found = True
                    break
            
            if not found:
                print("❌ Created item not found in list!")
        else:
            print(f"❌ GET Failed: {response_get.status_code}")
            print(response_get.text)

if __name__ == "__main__":
    test_waste_generation_flow()
