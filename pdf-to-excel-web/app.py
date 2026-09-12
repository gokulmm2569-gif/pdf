import os
import uuid
import socket
import uvicorn
from fastapi import FastAPI, File, UploadFile, HTTPException, Request
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from extractor import process_pdf
from excel_builder import create_excel_workbook

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
STATIC_DIR = os.path.join(BASE_DIR, "static")

os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(TEMPLATES_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)

app = FastAPI(title="PDF to Excel Converter", version="1.0.0")

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)


def get_local_ip() -> str:
    """Returns the primary non-loopback IPv4 address of the local machine."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Doesn't need to be reachable, purely for route selection
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        try:
            return socket.gethostbyname(socket.gethostname())
        except Exception:
            return "127.0.0.1"


@app.get("/", response_class=HTMLResponse)
@app.get("/index.html", response_class=HTMLResponse)
async def index(request: Request):
    local_ip = get_local_ip()
    port = 8000
    lan_url = f"http://{local_ip}:{port}"
    localhost_url = f"http://localhost:{port}"
    template = templates.env.get_template("index.html")
    content = template.render(
        request=request,
        local_ip=local_ip,
        port=port,
        lan_url=lan_url,
        localhost_url=localhost_url
    )
    return HTMLResponse(content=content)


@app.post("/api/process")
async def process_pdf_endpoint(file: UploadFile = File(...)):
    # 1. Validation
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file selected.")
        
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Invalid file type. Only PDF files are permitted.")
        
    # Read first 1024 bytes to check magic header
    file_bytes = await file.read()
    if len(file_bytes) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")
        
    if not file_bytes.startswith(b"%PDF-"):
        raise HTTPException(status_code=400, detail="The uploaded file does not have a valid PDF signature.")
        
    # 2. Save file safely
    file_id = f"{uuid.uuid4().hex[:10]}"
    safe_filename = f"{file_id}_{file.filename}"
    saved_pdf_path = os.path.join(UPLOADS_DIR, safe_filename)
    
    with open(saved_pdf_path, "wb") as f:
        f.write(file_bytes)
        
    # 3. Dynamic Extraction
    try:
        extraction_result = process_pdf(saved_pdf_path)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process PDF: {str(e)}")
        
    rows = extraction_result.get("rows", [])
    if not rows:
        raise HTTPException(
            status_code=422,
            detail="No tabular data could be detected in the uploaded PDF. Please verify that the PDF contains an invoice table."
        )
        
    # 4. Generate Excel file
    excel_filename = f"Invoice_Data_{file_id}.xlsx"
    excel_filepath = os.path.join(OUTPUT_DIR, excel_filename)
    try:
        create_excel_workbook(rows, excel_filepath)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate Excel file: {str(e)}")
        
    return JSONResponse({
        "success": True,
        "file_id": file_id,
        "original_filename": file.filename,
        "mode": extraction_result.get("mode"),
        "pages_count": extraction_result.get("pages_count", 1),
        "row_count": len(rows),
        "header": extraction_result.get("header", {}),
        "columns": extraction_result.get("columns", []),
        "rows": rows,
        "download_url": f"/api/download/{excel_filename}"
    })


@app.get("/api/download/{filename}")
async def download_excel(filename: str):
    # Sanitize filename
    safe_name = os.path.basename(filename)
    filepath = os.path.join(OUTPUT_DIR, safe_name)
    
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Requested Excel file was not found.")
        
    return FileResponse(
        path=filepath,
        filename=safe_name,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


if __name__ == "__main__":
    ip = get_local_ip()
    port = 8000
    print("\n=======================================================")
    print("           PDF TO EXCEL WEB APPLICATION                ")
    print("=======================================================")
    print(f"Local Access:   http://localhost:{port}")
    print(f"Network Access: http://{ip}:{port}")
    print("Binding host:   0.0.0.0")
    print("=======================================================\n")
    uvicorn.run(app, host="0.0.0.0", port=port)
