"""
Script para limpiar la base de datos.
Elimina todos los perfiles, CVs, análisis y batches, manteniendo solo los usuarios.
"""
import sys
sys.path.insert(0, '.')

from core.database import SessionLocal
from models import CV, Analisis, PerfilCargo, UploadBatch, AnalysisBatch
from models.usuario import Usuario

def limpiar_base_de_datos():
    """
    Limpia la base de datos eliminando:
    - Todos los CVs
    - Todos los análisis
    - Todos los perfiles de cargo
    - Todos los batches de carga y análisis
    
    Mantiene:
    - Usuarios (incluyendo administrador)
    - Sesiones activas
    """
    db = SessionLocal()
    
    try:
        print("🗑️  Limpiando base de datos...")
        
        # Contar registros antes de limpiar
        count_cvs = db.query(CV).count()
        count_analisis = db.query(Analisis).count()
        count_perfiles = db.query(PerfilCargo).count()
        count_upload_batches = db.query(UploadBatch).count()
        count_analysis_batches = db.query(AnalysisBatch).count()
        count_usuarios = db.query(Usuario).count()
        
        print(f"\n📊 Estado actual:")
        print(f"   - Usuarios: {count_usuarios}")
        print(f"   - Perfiles de cargo: {count_perfiles}")
        print(f"   - CVs: {count_cvs}")
        print(f"   - Análisis: {count_analisis}")
        print(f"   - Upload batches: {count_upload_batches}")
        print(f"   - Analysis batches: {count_analysis_batches}")
        
        # Eliminar en orden correcto (primero los que tienen foreign keys)
        print("\n🗑️  Eliminando análisis...")
        db.query(Analisis).delete()
        
        print("🗑️  Eliminando CVs...")
        db.query(CV).delete()
        
        print("🗑️  Eliminando perfiles de cargo...")
        db.query(PerfilCargo).delete()
        
        print("🗑️  Eliminando upload batches...")
        db.query(UploadBatch).delete()
        
        print("🗑️  Eliminando analysis batches...")
        db.query(AnalysisBatch).delete()
        
        db.commit()
        
        # Verificar usuarios restantes
        usuarios_restantes = db.query(Usuario).all()
        print(f"\n✅ Usuarios mantenidos: {len(usuarios_restantes)}")
        for u in usuarios_restantes:
            print(f"   - {u.email} (rol: {u.rol})")
        
        print("\n✅ ¡Base de datos limpia exitosamente!")
        print("\n📝 Ahora puedes comenzar desde cero con:")
        print("   - Creación de perfiles de cargo")
        print("   - Carga de CVs")
        print("   - Análisis de candidatos")
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ Error al limpiar la base de datos: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 60)
    print("LIMPIEZA DE BASE DE DATOS - AI-Recruiter Pro")
    print("=" * 60)
    print("\n⚠️  ADVERTENCIA: Esta operación eliminará:")
    print("   - Todos los perfiles de cargo")
    print("   - Todos los CVs cargados")
    print("   - Todos los análisis realizados")
    print("   - Todos los batches de carga y análisis")
    print("\n   Se mantendrán los usuarios (incluyendo administrador).")
    print("\n" + "=" * 60)
    
    confirm = input("\n¿Estás seguro de que quieres continuar? (escribe 'SI' para confirmar): ")
    
    if confirm.strip().upper() == 'SI':
        limpiar_base_de_datos()
    else:
        print("\n❌ Operación cancelada. La base de datos no fue modificada.")
