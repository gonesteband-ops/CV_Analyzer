"""
Script de migración para agregar campos de datos extraídos al modelo CV.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from core.database import engine
from sqlalchemy import text

def migrate():
    """Agrega las columnas de datos extraídos a la tabla cv."""
    
    with engine.connect() as conn:
        # Verificar si las columnas ya existen
        from sqlalchemy import inspect
        inspector = inspect(engine)
        columns = [col['name'] for col in inspector.get_columns('cv')]
        
        print("Columnas actuales en cv:", columns)
        
        # Agregar columnas si no existen
        if 'candidate_name' not in columns:
            print("Agregando candidate_name...")
            conn.execute(text("ALTER TABLE cv ADD COLUMN candidate_name VARCHAR(255)"))
            
        if 'candidate_email' not in columns:
            print("Agregando candidate_email...")
            conn.execute(text("ALTER TABLE cv ADD COLUMN candidate_email VARCHAR(255)"))
            
        if 'candidate_phone' not in columns:
            print("Agregando candidate_phone...")
            conn.execute(text("ALTER TABLE cv ADD COLUMN candidate_phone VARCHAR(50)"))
            
        if 'candidate_summary' not in columns:
            print("Agregando candidate_summary...")
            conn.execute(text("ALTER TABLE cv ADD COLUMN candidate_summary TEXT"))
        
        conn.commit()
        print("¡Migración completada!")

if __name__ == "__main__":
    migrate()
