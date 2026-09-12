import os
import sys

# Ensure pdf-to-excel-web directory is in sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
app_dir = os.path.dirname(current_dir)
if app_dir not in sys.path:
    sys.path.insert(0, app_dir)

from app import app
