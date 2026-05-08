"""
Prueba de Carga: Subir 50 CVs y medir tiempo total.
Meta: <5 minutos para 50 CVs.

Uso:
    cd backend/scripts
    python load_test_50_cvs.py
    
Requisitos:
    - Servidor corriendo en http://localhost:8000
    - Sesión activa (login previo)
"""
import requests
import time
import os
from pathlib import Path

# Configuración
BASE_URL = "http://localhost:8000"
LOGIN_URL = f"{BASE_URL}/api/auth/login"
UPLOAD_URL = f"{BASE_URL}/api/cvs/upload"
STATUS_URL = f"{BASE_URL}/api/cvs/upload-status"

# Credenciales de test (cambiar si es necesario)
EMAIL = "admin@test.com"
PASSWORD = "admin123"

# Cantidad de CVs a subir
NUM_CVS = 50


def login():
    """Inicia sesión y retorna cookie de sesión."""
    print("🔐 Iniciando sesión...")
    response = requests.post(LOGIN_URL, data={
        "email": EMAIL,
        "password": PASSWORD
    }, allow_redirects=False)
    
    if response.status_code == 303:
        cookies = response.cookies
        print("✅ Login exitoso")
        return cookies
    else:
        print(f"❌ Error en login: {response.status_code}")
        return None


def generar_cv_falso(index):
    """Genera un archivo PDF falso para testing."""
    # PDF mínimo válido
    pdf_content = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [] >>\nendobj\nxref\n0 3\n0000000000 65535 f\n0000000009 00000 n\n0000000058 00000 n\ntrailer\n<< /Size 3 /Root 1 0 R >>\nstartxref\n115\n%%EOF"
    
    filename = f"cv_test_{index:03d}.pdf"
    filepath = Path(__file__).parent / "test_cvs" / filename
    
    # Crear directorio si no existe
    filepath.parent.mkdir(exist_ok=True)
    
    # Escribir archivo
    with open(filepath, 'wb') as f:
        f.write(pdf_content)
    
    return filepath


def upload_cv(cookies, filepath):
    """Sube un CV al servidor."""
    with open(filepath, 'rb') as f:
        files = {"file": (filepath.name, f, "application/pdf")}
        response = requests.post(UPLOAD_URL, files=files, cookies=cookies)
    
    return response.status_code


def check_status(cookies):
    """Verifica el estado de la carga de CVs."""
    response = requests.get(STATUS_URL, cookies=cookies)
    if response.status_code == 200:
        return response.json()
    return None


def main():
    print("=" * 60)
    print("PRUEBA DE CARGA: 50 CVs")
    print("=" * 60)
    print()
    
    # Login
    cookies = login()
    if not cookies:
        print("❌ No se pudo iniciar sesión. Abortando prueba.")
        return
    
    print()
    print(f"📤 Subiendo {NUM_CVS} CVs de prueba...")
    print()
    
    # Medir tiempo total
    start_time = time.time()
    
    exitos = 0
    fallos = 0
    
    # Subir CVs uno por uno
    for i in range(1, NUM_CVS + 1):
        # Generar CV falso
        filepath = generar_cv_falso(i)
        
        # Subir CV
        status_code = upload_cv(cookies, filepath)
        
        if status_code == 200:
            exitos += 1
            print(f"  [{i:3d}/{NUM_CVS}] ✅ CV subido exitosamente")
        else:
            fallos += 1
            print(f"  [{i:3d}/{NUM_CVS}] ❌ Error al subir CV ({status_code})")
    
    # Tiempo total
    end_time = time.time()
    total_time = end_time - start_time
    
    print()
    print("=" * 60)
    print("RESULTADOS")
    print("=" * 60)
    print(f"✅ Exitosos:  {exitos}/{NUM_CVS}")
    print(f"❌ Fallidos:  {fallos}/{NUM_CVS}")
    print(f"⏱️  Tiempo total: {total_time:.2f} segundos ({total_time/60:.2f} minutos)")
    print(f"📊 Promedio:    {total_time/NUM_CVS:.2f} segundos por CV")
    print()
    
    # Verificar si cumple la meta
    meta_segundos = 5 * 60  # 5 minutos
    if total_time <= meta_segundos:
        print(f"🎉 ¡META CUMPLIDA! (<{meta_segundos/60:.0f} minutos)")
    else:
        print(f"⚠️  META NO CUMPLIDA (>{meta_segundos/60:.0f} minutos)")
    
    print()
    print("Limpiando archivos de prueba...")
    test_dir = Path(__file__).parent / "test_cvs"
    if test_dir.exists():
        import shutil
        shutil.rmtree(test_dir)
        print("✅ Archivos eliminados")
    
    print()
    print("=" * 60)


if __name__ == "__main__":
    main()
