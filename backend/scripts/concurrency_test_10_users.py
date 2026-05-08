"""
Prueba de Concurrencia: 10 usuarios analizando CVs simultáneamente.
Meta: Medir latencia promedio con carga concurrente.

Uso:
    cd backend/scripts
    python concurrency_test_10_users.py
    
Requisitos:
    - Servidor corriendo en http://localhost:8000
    - Al menos 1 perfil de cargo creado
    - Al menos 10 CVs subidos
"""
import requests
import time
import concurrent.futures
from pathlib import Path

# Configuración
BASE_URL = "http://localhost:8000"
LOGIN_URL = f"{BASE_URL}/api/auth/login"
PROFILE_URL = f"{BASE_URL}/api/profiles"
BATCH_URL = f"{BASE_URL}/api/cvs/analysis/batch"

# Credenciales de test (mismo usuario para simplificar)
EMAIL = "admin@test.com"
PASSWORD = "admin123"

# Cantidad de usuarios concurrentes
NUM_USERS = 10


def login():
    """Inicia sesión y retorna cookie de sesión."""
    response = requests.post(LOGIN_URL, data={
        "email": EMAIL,
        "password": PASSWORD
    }, allow_redirects=False)
    
    if response.status_code == 303:
        return response.cookies
    return None


def get_profile_id(cookies):
    """Obtiene el ID del primer perfil activo."""
    response = requests.get(PROFILE_URL, cookies=cookies)
    if response.status_code == 200:
        profiles = response.json()
        if profiles:
            return profiles[0]["id"]
    return None


def get_cv_ids(cookies):
    """Obtiene IDs de los primeros 10 CVs."""
    # Simplemente retornamos IDs ficticios para la prueba
    # En producción, deberías hacer GET /api/cvs
    return list(range(1, 11))  # IDs 1-10


def analizar_cv(usuario_num, perfil_id, cv_ids):
    """Simula un usuario analizando CVs."""
    cookies = login()
    if not cookies:
        return {"usuario": usuario_num, "success": False, "time": 0, "error": "Login failed"}
    
    start_time = time.time()
    
    # Enviar request de análisis batch
    response = requests.post(BATCH_URL, json={
        "perfil_id": perfil_id,
        "cv_ids": cv_ids
    }, cookies=cookies)
    
    end_time = time.time()
    
    if response.status_code == 200:
        return {
            "usuario": usuario_num,
            "success": True,
            "time": end_time - start_time,
            "data": response.json()
        }
    else:
        return {
            "usuario": usuario_num,
            "success": False,
            "time": end_time - start_time,
            "error": f"HTTP {response.status_code}",
            "response": response.text[:200]
        }


def main():
    print("=" * 60)
    print("PRUEBA DE CONCURRENCIA: 10 Usuarios Simultáneos")
    print("=" * 60)
    print()
    
    # Login inicial para obtener perfil y CV IDs
    print("🔐 Iniciando sesión para obtener datos...")
    cookies = login()
    if not cookies:
        print("❌ No se pudo iniciar sesión. Abortando prueba.")
        return
    
    perfil_id = get_profile_id(cookies)
    if not perfil_id:
        print("❌ No se encontró ningún perfil de cargo. Abortando prueba.")
        print("   Por favor crea al menos 1 perfil primero.")
        return
    
    cv_ids = get_cv_ids(cookies)
    print(f"✅ Perfil ID: {perfil_id}")
    print(f"✅ CV IDs: {cv_ids}")
    print()
    
    print(f"🚀 Iniciando {NUM_USERS} usuarios concurrentes...")
    print()
    
    # Medir tiempo total
    start_time = time.time()
    
    # Ejecutar concurrentemente
    resultados = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=NUM_USERS) as executor:
        futures = [
            executor.submit(analizar_cv, i+1, perfil_id, cv_ids)
            for i in range(NUM_USERS)
        ]
        
        for future in concurrent.futures.as_completed(futures):
            resultado = future.result()
            resultados.append(resultado)
            
            status = "✅" if resultado["success"] else "❌"
            tiempo = resultado.get("time", 0)
            print(f"  {status} Usuario {resultado['usuario']}: {tiempo:.2f}s")
    
    # Tiempo total
    end_time = time.time()
    total_time = end_time - start_time
    
    print()
    print("=" * 60)
    print("RESULTADOS")
    print("=" * 60)
    
    # Calcular estadísticas
    exitos = sum(1 for r in resultados if r.get("success", False))
    fallos = NUM_USERS - exitos
    tiempos = [r.get("time", 0) for r in resultados if r.get("success", False)]
    
    if tiempos:
        avg_time = sum(tiempos) / len(tiempos)
        min_time = min(tiempos)
        max_time = max(tiempos)
    else:
        avg_time = min_time = max_time = 0
    
    print(f"✅ Exitosos:  {exitos}/{NUM_USERS}")
    print(f"❌ Fallidos:  {fallos}/{NUM_USERS}")
    print(f"⏱️  Tiempo total: {total_time:.2f} segundos")
    print()
    print("📊 LATENCIA POR USUARIO:")
    print(f"   Promedio: {avg_time:.2f}s")
    print(f"   Mínimo:   {min_time:.2f}s")
    print(f"   Máximo:   {max_time:.2f}s")
    print()
    
    # Verificar rendimiento
    if avg_time < 5:
        print(f"🎉 ¡RENDIMIENTO EXCELENTE! (<5s promedio)")
    elif avg_time < 10:
        print(f"✅ Rendimiento aceptable (<10s promedio)")
    else:
        print(f"⚠️  Rendimiento bajo (>{avg_time:.0f}s promedio)")
    
    print()
    print("=" * 60)


if __name__ == "__main__":
    main()
