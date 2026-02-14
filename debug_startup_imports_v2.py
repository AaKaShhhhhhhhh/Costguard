
import sys
import os
from pathlib import Path
import logging

# Add project root to sys.path
root_dir = str(Path(__file__).parent.absolute())
if root_dir not in sys.path:
    sys.path.append(root_dir)

print(f"Debug: Root dir set to {root_dir}")

# Attempt imports
modules_to_check = [
    "shared.config",
    "shared.types",
    "backend.models.models",
    "backend.services.slack",
    "backend.api.v1.endpoints",
    "backend.api.main"
]

for module in modules_to_check:
    print(f"Attempting to import {module}...")
    try:
        __import__(module)
        print(f"Success: {module} imported.")
    except Exception as e:
        print(f"Error importing {module}: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

print("All imports successful.")
