"""Test script para CV extractor."""
import sys
from pathlib import Path

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent))

from services.cv_parser import CVParser

print("=== Test CV Parser ===", flush=True)

parser = CVParser()
# Los archivos se guardan en la raiz del proyecto, no en backend/src/uploads
file_path = Path(__file__).parent.parent.parent.parent / "uploads" / "33b939a5-dbed-46b5-9600-179338868930_test_cv.pdf"
print(f"File: {file_path}", flush=True)
print(f"Exists: {file_path.exists()}", flush=True)

try:
    texto, tipo = parser.extraer_texto(str(file_path))
    print(f"SUCCESS! Type: {tipo}, Length: {len(texto)}", flush=True)
    print(f"Text: {texto[:200]}", flush=True)
except Exception as e:
    print(f"ERROR: {e}", flush=True)
    import traceback
    traceback.print_exc()
