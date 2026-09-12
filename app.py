"""
Root launcher for PDF-to-Excel Web Application.
Enables running `python app.py` directly from project root.
"""
import os
import sys

project_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pdf-to-excel-web")
sys.path.insert(0, project_dir)
os.chdir(project_dir)

from app import app, get_local_ip
import uvicorn

if __name__ == "__main__":
    ip = get_local_ip()
    port = int(os.environ.get("PORT", 8000))
    print("\n=======================================================")
    print("           PDF TO EXCEL WEB APPLICATION                ")
    print("=======================================================")
    print(f"Local Access:   http://localhost:{port}")
    print(f"Network Access: http://{ip}:{port}")
    print("Binding host:   0.0.0.0")
    print("=======================================================\n")
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=False)
