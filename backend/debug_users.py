from sqlmodel import Session, select
from database import engine
from models import Usuario

def list_users():
    try:
        with Session(engine) as session:
            statement = select(Usuario)
            results = session.exec(statement).all()
            print(f"--- Users in 'usuarios' table ---")
            for user in results:
                print(f"ID: {user.id}, Nombre: '{user.nombre}', Clave: '{user.clave}'")
            print(f"---------------------------------")
            if not results:
                print("Table 'usuarios' is empty or could not be read.")
    except Exception as e:
        print(f"Error reading database: {e}")

if __name__ == "__main__":
    list_users()
