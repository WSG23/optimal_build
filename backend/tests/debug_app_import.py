import sys
import os

# Add backend to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

print("Attempting to import app.main...")
try:
    from app.main import app  # noqa: F401

    print("SUCCESS: Imported app.main")
except Exception as e:
    print(f"FAILURE: {type(e).__name__}: {e}")
    import traceback

    traceback.print_exc()
