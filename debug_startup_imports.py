
import sys
import os
from pathlib import Path

# Add project root to sys.path
root_dir = str(Path(__file__).parent.absolute())
if root_dir not in sys.path:
    sys.path.append(root_dir)

print(f"Debug: Root dir set to {root_dir}")

try:
    print("Attempting to import shared.config...")
    from shared.config import settings
    print("Success: shared.config imported.")
except Exception as e:
    print(f"Error importing shared.config: {e}")
    sys.exit(1)

try:
    print("Attempting to import backend.models.models...")
    from backend.models.models import Base
    print("Success: backend.models.models imported.")
except Exception as e:
    print(f"Error importing backend.models.models: {e}")
    sys.exit(1)

try:
    print("Attempting to import backend.api.main...")
    from backend.api.main import app
    print("Success: backend.api.main imported.")
except Exception as e:
    print(f"Error importing backend.api.main: {e}")
    sys.exit(1)

print("All imports successful.")
