import sys
from pathlib import Path

# Add project root to sys.path so backend imports work seamlessly on Vercel
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from backend.app import app
