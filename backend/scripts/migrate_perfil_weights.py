"""
Migración: Agregar columnas de pesos y penalizaciones a perfil_cargo
"""
import sys
from pathlib import Path

# Agregar backend/src al path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.database import engine
from sqlalchemy import text, inspect

def upgrade():
    """Agrega columnas de pesos y penalizaciones a la tabla perfil_cargo."""
    inspector = inspect(engine)
    columns = [c['name'] for c in inspector.get_columns('perfil_cargo')]
    
    nuevas_columnas = [
        ('peso_tecnico', 'INTEGER DEFAULT 50'),
        ('peso_experiencia', 'INTEGER DEFAULT 30'),
        ('peso_soft_skills', 'INTEGER DEFAULT 20'),
        ('penalizacion_sobrecalificado', 'INTEGER DEFAULT 25'),
        ('penalizacion_cambio_rubro', 'INTEGER DEFAULT 15'),
    ]
    
    with engine.connect() as conn:
        for col_name, col_def in nuevas_columnas:
            if col_name not in columns:
                try:
                    conn.execute(text(f'ALTER TABLE perfil_cargo ADD COLUMN {col_name} {col_def}'))
                    print(f'✅ Columna {col_name} agregada')
                except Exception as e:
                    print(f'⚠️ Error en {col_name}: {e}')
            else:
                print(f'⏭️ Columna {col_name} ya existe')
        conn.commit()
        print('\n✅ Migración completada')

if __name__ == '__main__':
    upgrade()
