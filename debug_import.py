import sys
import os
import traceback

sys.path.append(os.getcwd())

try:
    from backend.app.main import app
    print("Import successful!")
except Exception:
    traceback.print_exc()
