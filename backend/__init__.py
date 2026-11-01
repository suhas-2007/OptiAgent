
import os
import sys

# Ensure the backend directory is in sys.path so modules can be imported
# cleanly both as a package (backend.x) and directly within backend scripts.
_backend_dir = os.path.dirname(os.path.abspath(__file__))
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

__version__ = "1.0.0"
