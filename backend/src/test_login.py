"""
Script para testear el login y verificar credenciales.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from core.database import SessionLocal
from core.security import hash_password, verificar_password

# Importar todos los modelos para registrarlos
from models import usuario, perfil_cargo, cv, analisis, portal_credential, upload_batch, analysis_batch, session

from models.usuario import Usuario


def test_login():
    """Prueba el login con credenciales."""

    db = SessionLocal()

    try:
        # Datos para probar
        email = "admin@test.com"
        password = "admin123"

        print(f"[*] Buscando usuario con email: {email}")
        usuario_obj = db.query(Usuario).filter(Usuario.email == email).first()

        if not usuario_obj:
            print(f"[-] Usuario no encontrado!")
            return False

        print(f"[+] Usuario encontrado!")
        print(f"    ID: {usuario_obj.id}")
        print(f"    Email: {usuario_obj.email}")
        print(f"    Nombre: {usuario_obj.nombre}")
        print(f"    Rol: {usuario_obj.rol}")
        print(f"    Password Hash: {usuario_obj.password_hash}")

        print(f"\n[*] Verificando contraseña: '{password}'")
        es_valida = verificar_password(password, usuario_obj.password_hash)
        print(f"    Resultado: {es_valida}")

        if es_valida:
            print(f"\n[+] EXITO! Las credenciales son correctas!")
            print(f"    Puedes loguarte con:")
            print(f"    Email: {email}")
            print(f"    Password: {password}")
            return True
        else:
            print(f"\n[-] ERROR! La contraseña no coincide!")
            print(f"    Hash almacenado: {usuario_obj.password_hash}")

            # Intentar hashear la misma contraseña para comparar
            nuevo_hash = hash_password(password)
            print(f"    Nuevo hash generado: {nuevo_hash}")

            print(f"\n[!] Posibles causas:")
            print(f"    1. La contraseña escrita no es exactamente 'admin123'")
            print(f"    2. Hay espacios en blanco al inicio o final")
            print(f"    3. El hash se corrompió al guardar")

            return False

    except Exception as e:
        print(f"[-] Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


if __name__ == "__main__":
    print("[*] Iniciando test de login...")
    print()

    exito = test_login()

    print()
    if exito:
        sys.exit(0)
    else:
        sys.exit(1)
