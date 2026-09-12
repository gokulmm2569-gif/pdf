import os
import sys

# Ensure pdf-to-excel-web directory is in sys.path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
web_dir = os.path.join(root_dir, "pdf-to-excel-web")
if web_dir not in sys.path:
    sys.path.insert(0, web_dir)

from app import app
