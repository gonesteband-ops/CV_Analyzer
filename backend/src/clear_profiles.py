"""
Script para eliminar todos los perfiles de cargo de la base de datos.
"""
import sys
from sqlalchemy import delete

# Agregar el path correcto
sys.path.insert(0, '.')

from core.database import SessionLocal
from models.perfil_cargo import PerfilCargo
from models.analisis import Analisis


def clear_profiles():
    """Elimina todos los perfiles y sus análisis asociados."""
    db = SessionLocal()
    try:
        # Primero eliminar todos los análisis asociados a perfiles
        db.execute(delete(Analisis))
        db.commit()
        print("✓ Análisis eliminados")
        
        # Luego eliminar todos los perfiles
        result = db.execute(delete(PerfilCargo))
        db.commit()
        
        print("✓ Todos los perfiles han sido eliminados de la base de datos")
        
    except Exception as e:
        db.rollback()
        print(f"✗ Error: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    clear_profiles()
