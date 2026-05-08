import os
from sqlalchemy import create_engine, text
from core.config import settings


def migrate_analisis_fields():
    """
    Script de migración para añadir las columnas 'fortalezas' y 'debilidades'
    a la tabla 'analisis'.
    """
    # Crear el engine
    engine = create_engine(settings.database_url)

    # Sentencias SQL para añadir las columnas
    add_fortalezas_sql = "ALTER TABLE analisis ADD COLUMN fortalezas TEXT;"
    add_debilidades_sql = "ALTER TABLE analisis ADD COLUMN debilidades TEXT;"

    try:
        with engine.connect() as conn:
            # Ejecutar las sentencias
            conn.execute(text(add_fortalezas_sql))
            conn.execute(text(add_debilidades_sql))
            conn.commit()
            print("✅ Migración completada: Columnas 'fortalezas' y 'debilidades' añadidas a la tabla 'analisis'.")
    except Exception as e:
        print(f"❌ Error al ejecutar la migración: {e}")
        raise


if __name__ == "__main__":
    migrate_analisis_fields()