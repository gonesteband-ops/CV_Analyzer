"""Debug path."""
from pathlib import Path
import os

cwd = Path.cwd()
print(f'CWD: {cwd}', flush=True)
print(f'Parent 1: {cwd.parent}', flush=True)
print(f'Parent 2: {cwd.parent.parent}', flush=True)
print(f'Uploads dir: {cwd.parent.parent / "uploads"}', flush=True)
print(f'Uploads exists: {(cwd.parent.parent / "uploads").exists()}', flush=True)

# List uploads
uploads = cwd.parent.parent / "uploads"
if uploads.exists():
    print(f'Uploads contents:', list(uploads.iterdir()), flush=True)
