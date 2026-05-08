"""Test extractor con archivo real."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from services.cv_extractor import ExtractorCV
import asyncio

async def main():
    file_path = Path(__file__).parent.parent.parent / "uploads" / "3feb2e77-f3d3-4358-a6a4-822adc51012e_test_cv.pdf"
    print(f"File: {file_path}", flush=True)
    print(f"Exists: {file_path.exists()}", flush=True)
    
    extractor = ExtractorCV()
    try:
        info = await extractor.extraer_informacion(str(file_path))
        print(f"Nombre: {info.nombre}", flush=True)
        print(f"Email: {info.email}", flush=True)
        print(f"Resumen: {info.resumen}", flush=True)
        print(f"Telefono: {info.telefono}", flush=True)
    except Exception as e:
        print(f"ERROR: {e}", flush=True)
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
