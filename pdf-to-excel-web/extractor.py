import re
import os
import sys
import platform
import shutil
import asyncio
from typing import Dict, Any, List, Optional
import pdfplumber
import pypdfium2 as pdfium
from PIL import Image

try:
    import winocr  # type: ignore
    HAS_WINOCR = True
except ImportError:
    winocr = None  # type: ignore
    HAS_WINOCR = False

try:
    import pytesseract  # type: ignore
    HAS_PYTESSERACT = True
except ImportError:
    pytesseract = None  # type: ignore
    HAS_PYTESSERACT = False


class OCRBoundingRect:
    def __init__(self, x: int = 0, y: int = 0, width: int = 0, height: int = 0):
        self.x = x
        self.y = y
        self.width = width
        self.height = height


class OCRWord:
    def __init__(self, text: str = "", x: int = 0, y: int = 0, width: int = 0, height: int = 0):
        self.text = text
        self.bounding_rect = OCRBoundingRect(x, y, width, height)


class OCRLine:
    def __init__(self, words: Optional[List[OCRWord]] = None):
        self.words = words or []


class OCRResult:
    def __init__(self, text: str = "", lines: Optional[List[OCRLine]] = None):
        self.text = text
        self.lines = lines or []


TARGET_COLUMNS = [
    "Sr No",
    "Doc No",
    "Date",
    "Dest. City",
    "Mode",
    "I",
    "PC",
    "Weight",
    "Amount"
]


def clean_str(val: Any) -> str:
    if val is None:
        return ""
    return re.sub(r'\s+', ' ', str(val)).strip()


def extract_header_from_text(full_text: str) -> Dict[str, str]:
    """
    Extracts invoice header information dynamically using regex patterns.
    """
    header = {
        "Company": "",
        "Address": "",
        "Phone": "",
        "Email": "",
        "SAC Code": "",
        "Type Of Service": "",
        "Invoice No": "",
        "Date": "",
        "Customer": "",
        "PAN": "",
        "CIN": "",
        "Location": "",
        "Bill": ""
    }
    
    lines = [line.strip() for line in full_text.splitlines() if line.strip()]
    if lines:
        # First non-empty line is commonly the company name
        header["Company"] = lines[0]
        
    # Search for specific patterns
    phone_m = re.search(r'(?:Phone|Ph|Mob|Mobile|Tel)[\s:]*([0-9\+\s\-]{8,15})', full_text, re.IGNORECASE)
    if phone_m:
        header["Phone"] = clean_str(phone_m.group(1))
        
    email_m = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', full_text)
    if email_m:
        header["Email"] = clean_str(email_m.group(0))
        
    sac_m = re.search(r'SAC\s*(?:Code)?[\s:]*([A-Za-z0-9]+)', full_text, re.IGNORECASE)
    if sac_m:
        header["SAC Code"] = clean_str(sac_m.group(1))
        
    service_m = re.search(r'Type\s*Of\s*Service[\s:]*([^\n|]+)', full_text, re.IGNORECASE)
    if service_m:
        header["Type Of Service"] = clean_str(service_m.group(1))
        
    inv_m = re.search(r'Invoice\s*No\.?[\s:]*([^\n\s|]+)', full_text, re.IGNORECASE)
    if inv_m:
        header["Invoice No"] = clean_str(inv_m.group(1))
        
    date_m = re.search(r'(?:Invoice\s+Date|Date)[\s:]*([0-9]{1,2}[/-][0-9]{1,2}[/-][0-9]{2,4})', full_text, re.IGNORECASE)
    if date_m:
        header["Date"] = clean_str(date_m.group(1))
        
    cust_m = re.search(r'(?:Customer|Party|Bill\s*To)[\s:]*([^\n|]+)', full_text, re.IGNORECASE)
    if cust_m:
        header["Customer"] = clean_str(cust_m.group(1))
        
    pan_m = re.search(r'PAN[\s:]*([A-Za-z0-9]{10})', full_text, re.IGNORECASE)
    if pan_m:
        header["PAN"] = clean_str(pan_m.group(1)).upper()
        
    cin_m = re.search(r'CIN[\s:]*([^\n|\s]+)', full_text, re.IGNORECASE)
    if cin_m:
        header["CIN"] = clean_str(cin_m.group(1))
        
    loc_m = re.search(r'Location[\s:]*([^\n|]+)', full_text, re.IGNORECASE)
    if loc_m:
        header["Location"] = clean_str(loc_m.group(1))
        
    bill_m = re.search(r'Bill[\s:]*([^\n|]+)', full_text, re.IGNORECASE)
    if bill_m:
        header["Bill"] = clean_str(bill_m.group(1))
        
    # Look for address in top lines (e.g. line containing SHOP NO, APARTMENT, NAGPUR, etc.)
    for line in lines[1:6]:
        if any(keyword in line.upper() for keyword in ["SHOP", "APARTMENT", "STATION", "STREET", "ROAD", "NAGPUR", "MAHARASHTRA", "PIN", "PLOT"]):
            if not header["Address"]:
                header["Address"] = line
            else:
                header["Address"] += ", " + line
                
    return header


def map_headers_to_target(headers: List[str]) -> Dict[int, str]:
    """
    Maps detected table column headers to the standardized 9 columns.
    """
    mapping = {}
    cleaned = [clean_str(h).lower() for h in headers]
    
    for idx, h in enumerate(cleaned):
        if re.search(r'sr\.?\s*no|s\.?\s*no|serial', h):
            mapping[idx] = "Sr No"
        elif re.search(r'doc\.?\s*no|docket|awb|cn\s*no', h):
            mapping[idx] = "Doc No"
        elif 'date' in h:
            mapping[idx] = "Date"
        elif re.search(r'dest|city|destination', h):
            mapping[idx] = "Dest. City"
        elif 'mode' in h:
            mapping[idx] = "Mode"
        elif h == 'i' or 'ind' in h or 'indicator' in h:
            mapping[idx] = "I"
        elif re.search(r'pc|pcs|pieces|pkg|pkgs', h):
            mapping[idx] = "PC"
        elif re.search(r'wt|weight', h):
            mapping[idx] = "Weight"
        elif re.search(r'amt|amount|total', h):
            mapping[idx] = "Amount"
            
    return mapping


def parse_text_table_row(row_cells: List[str], mapping: Dict[int, str]) -> Optional[Dict[str, str]]:
    """
    Parses a single row of cells into the target columns schema using column mapping.
    """
    rec = {col: "" for col in TARGET_COLUMNS}
    non_empty = 0
    
    for idx, val in enumerate(row_cells):
        val_str = clean_str(val)
        if val_str:
            non_empty += 1
        col_name = mapping.get(idx)
        if col_name:
            rec[col_name] = val_str
            
    if non_empty < 2:
        return None
        
    # Check if row is another header repetition
    if rec.get("Sr No", "").lower() in ["sr no", "srno", "s.no", "serial"] or \
       rec.get("Doc No", "").lower() in ["doc no", "docno", "docket"]:
        return None
        
    return rec


def extract_from_pdfplumber(pdf_path: str) -> Dict[str, Any]:
    """
    Extracts table and header from vector/selectable-text PDF.
    """
    all_rows = []
    full_text_pages = []
    
    with pdfplumber.open(pdf_path) as pdf:
        for page_idx, page in enumerate(pdf.pages):
            page_text = page.extract_text() or ""
            full_text_pages.append(page_text)
            
            # Try default extraction first
            tables = page.extract_tables()
            if not tables:
                # Try table settings with explicit strategies
                tables = page.extract_tables({
                    "vertical_strategy": "lines",
                    "horizontal_strategy": "lines",
                    "snap_tolerance": 3
                }) or page.extract_tables({
                    "vertical_strategy": "text",
                    "horizontal_strategy": "text"
                })
                
            for table in (tables or []):
                if not table or len(table) < 2:
                    continue
                    
                # Identify header row
                header_row_idx = -1
                for r_idx, row in enumerate(table):
                    row_str = " ".join([clean_str(c).lower() for c in row if c])
                    if any(k in row_str for k in ["doc", "dest", "weight", "amount", "mode", "date"]):
                        header_row_idx = r_idx
                        break
                        
                if header_row_idx == -1:
                    continue
                    
                header_cells = [clean_str(c) for c in table[header_row_idx]]
                mapping = map_headers_to_target(header_cells)
                
                # If mapping didn't find all columns, but length is 9, default index map
                if len(mapping) < 5 and len(header_cells) == 9:
                    mapping = {i: TARGET_COLUMNS[i] for i in range(9)}
                    
                for row in table[header_row_idx + 1:]:
                    parsed = parse_text_table_row(row, mapping)
                    if parsed:
                        all_rows.append(parsed)
                        
    combined_text = "\n".join(full_text_pages)
    header_info = extract_header_from_text(combined_text)
    
    return {
        "header": header_info,
        "columns": TARGET_COLUMNS,
        "rows": all_rows,
        "mode": "PDF_TEXT",
        "pages_count": len(full_text_pages)
    }


def parse_ocr_line_items(ocr_lines: List[Any], image_width: int, image_height: int) -> List[Dict[str, str]]:
    """
    Intelligently groups OCR word tokens into structured table rows.
    """
    words = []
    for line in ocr_lines:
        if hasattr(line, 'words') and line.words:
            for w in line.words:
                words.append({
                    "text": clean_str(w.text),
                    "x": w.bounding_rect.x,
                    "y": w.bounding_rect.y,
                    "w": w.bounding_rect.width,
                    "h": w.bounding_rect.height
                })
        else:
            # Simple text line
            pass
            
    if not words:
        return []
        
    # Find table header by detecting header keywords
    header_y = -1
    for w in words:
        if w["text"].lower() in ["sr", "doc", "dest.", "dest", "mode", "weight", "amount"]:
            # Check if other header words are near the same y
            same_y = [ow for ow in words if abs(ow["y"] - w["y"]) < 20 and ow["text"].lower() in ["no", "doc", "date", "city", "mode", "weight", "amount"]]
            if len(same_y) >= 3:
                header_y = w["y"]
                break
                
    if header_y == -1:
        # Fallback: look for data rows directly
        data_words = words
    else:
        # Keep words below header row
        data_words = [w for w in words if w["y"] > header_y + 25]
        
    # Group words into horizontal lines based on y coordinate threshold
    # Sort primarily by y
    data_words.sort(key=lambda w: (w["y"], w["x"]))
    
    row_clusters = []
    for w in data_words:
        # Discard footer notes or summary totals if needed
        if any(term in w["text"].upper() for term in ["TOTAL", "PAGE", "SIGNATURE", "TERMS"]):
            continue
        placed = False
        for cluster in row_clusters:
            avg_y = sum(item["y"] for item in cluster) / len(cluster)
            if abs(w["y"] - avg_y) <= 15: # Line height tolerance
                cluster.append(w)
                placed = True
                break
        if not placed:
            row_clusters.append([w])
            
    extracted_rows = []
    for cluster in row_clusters:
        # Sort words in row from left to right
        cluster.sort(key=lambda item: item["x"])
        
        # We need to map tokens into [Sr No, Doc No, Date, Dest. City, Mode, I, PC, Weight, Amount]
        tokens = [item["text"] for item in cluster if item["text"]]
        if len(tokens) < 3:
            continue
            
        row_dict = {col: "" for col in TARGET_COLUMNS}
        
        # Token pattern matching
        # 1. Sr No: usually first token if integer
        curr_idx = 0
        if curr_idx < len(tokens) and tokens[curr_idx].isdigit() and len(tokens[curr_idx]) <= 4:
            row_dict["Sr No"] = tokens[curr_idx]
            curr_idx += 1
            
        # 2. Doc No: usually 7-12 digits
        if curr_idx < len(tokens) and re.match(r'^[0-9]{6,15}$', tokens[curr_idx]):
            row_dict["Doc No"] = tokens[curr_idx]
            curr_idx += 1
            
        # 3. Date: DD/MM/YY or DD-MM-YYYY
        if curr_idx < len(tokens) and re.match(r'^[0-9]{1,2}[/-][0-9]{1,2}[/-][0-9]{2,4}$', tokens[curr_idx]):
            row_dict["Date"] = tokens[curr_idx]
            curr_idx += 1
            
        # At the end of row: Amount (last decimal), Weight (previous decimal), PC (integer before weight), I (single letter before PC)
        end_idx = len(tokens) - 1
        
        # Amount: last token with decimal or number
        if end_idx >= curr_idx and re.match(r'^[0-9]+\.[0-9]{2}$|^[0-9]+$', tokens[end_idx]):
            row_dict["Amount"] = tokens[end_idx]
            end_idx -= 1
            
        # Weight: token before amount
        if end_idx >= curr_idx and re.match(r'^[0-9]+\.[0-9]{1,3}$|^[0-9]+$', tokens[end_idx]):
            row_dict["Weight"] = tokens[end_idx]
            end_idx -= 1
            
        # PC: small integer
        if end_idx >= curr_idx and tokens[end_idx].isdigit() and len(tokens[end_idx]) <= 3:
            row_dict["PC"] = tokens[end_idx]
            end_idx -= 1
            
        # I: single letter like P or D
        if end_idx >= curr_idx and len(tokens[end_idx]) == 1 and tokens[end_idx].isalpha():
            row_dict["I"] = tokens[end_idx].upper()
            end_idx -= 1
            
        # Mode: word like SURFACE / AIR / EXP
        if end_idx >= curr_idx and tokens[end_idx].upper() in ["SURFACE", "AIR", "EXPRESS", "CARGO", "ROAD"]:
            row_dict["Mode"] = tokens[end_idx].upper()
            end_idx -= 1
            
        # Remaining middle tokens belong to Dest. City
        if curr_idx <= end_idx:
            city_parts = tokens[curr_idx:end_idx + 1]
            row_dict["Dest. City"] = " ".join(city_parts)
            
        # Validate that at least Doc No or Sr No + City is present
        if row_dict["Doc No"] or (row_dict["Sr No"] and row_dict["Dest. City"]):
            extracted_rows.append(row_dict)
            
    return extracted_rows


def run_winocr_recognize(pil_image, lang: str = "en"):
    """
    Executes winocr.recognize_pil safely whether an asyncio loop is active or not.
    """
    if not HAS_WINOCR or winocr is None:
        raise RuntimeError("Windows Media OCR (winocr) is not available.")
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
        
    if loop and loop.is_running():
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            return executor.submit(lambda: asyncio.run(winocr.recognize_pil(pil_image, lang))).result()
    else:
        return asyncio.run(winocr.recognize_pil(pil_image, lang))


def check_tesseract_available() -> bool:
    """
    Checks if Tesseract OCR binary and pytesseract are available.
    Configures tesseract_cmd and TESSDATA_PREFIX if found in non-standard paths.
    """
    if not HAS_PYTESSERACT or pytesseract is None:
        return False
        
    # 1. If already in PATH
    if shutil.which("tesseract"):
        return True
        
    # 2. Check common Linux and Render paths
    common_linux_paths = [
        "/usr/bin/tesseract",
        "/usr/local/bin/tesseract",
        os.path.expanduser("~/.local/bin/tesseract"),
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".apt", "usr", "bin", "tesseract")),
        os.path.abspath(os.path.join(os.path.dirname(__file__), ".apt", "usr", "bin", "tesseract")),
    ]
    for p in common_linux_paths:
        if os.path.exists(p) and os.path.isfile(p):
            pytesseract.pytesseract.tesseract_cmd = p
            tessdata_candidates = [
                os.path.join(os.path.dirname(os.path.dirname(p)), "share", "tessdata"),
                os.path.join(os.path.dirname(os.path.dirname(p)), "share", "tesseract-ocr", "4.00", "tessdata"),
                os.path.join(os.path.dirname(os.path.dirname(p)), "share", "tesseract-ocr", "5", "tessdata"),
                "/usr/share/tesseract-ocr/4.00/tessdata",
                "/usr/share/tesseract-ocr/5/tessdata",
                "/usr/share/tessdata",
            ]
            for td in tessdata_candidates:
                if os.path.exists(td):
                    os.environ.setdefault("TESSDATA_PREFIX", td)
                    break
            return True

    # 3. Check common Windows paths
    if platform.system() == "Windows":
        common_win_paths = [
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\Programs\Tesseract-OCR\tesseract.exe"),
        ]
        for p in common_win_paths:
            if os.path.exists(p) and os.path.isfile(p):
                pytesseract.pytesseract.tesseract_cmd = p
                return True

    return False


def get_ocr_backend() -> str:
    """
    Selects the optimal OCR backend based on operating system and availability:
    - Windows: Uses winocr if installed; falls back to tesseract if available.
    - Linux / Render: Uses tesseract if available; never requires winocr.
    """
    is_windows = platform.system() == "Windows"
    if is_windows and HAS_WINOCR:
        return "winocr"
    if check_tesseract_available():
        return "tesseract"
    if HAS_WINOCR:
        return "winocr"
    return "none"


def run_tesseract_recognize(pil_image: Image.Image, lang: str = "eng") -> OCRResult:
    """
    Executes Tesseract OCR via pytesseract and formats output into line/word tokens
    matching the winocr structure for table grouping and column parsing.
    """
    if not HAS_PYTESSERACT or pytesseract is None:
        raise RuntimeError("Tesseract OCR (pytesseract) is not available.")
    data = pytesseract.image_to_data(pil_image, lang=lang, output_type=pytesseract.Output.DICT)
    full_text = pytesseract.image_to_string(pil_image, lang=lang)
    
    lines_map: Dict[Any, List[OCRWord]] = {}
    n_boxes = len(data["text"])
    for i in range(n_boxes):
        text = clean_str(data["text"][i])
        if not text:
            continue
        try:
            conf = float(data["conf"][i])
            if conf < 15:
                continue
        except (ValueError, TypeError):
            pass
            
        x = int(data["left"][i])
        y = int(data["top"][i])
        w = int(data["width"][i])
        h = int(data["height"][i])
        
        line_key = (data.get("block_num", [0])[i], data.get("par_num", [0])[i], data.get("line_num", [0])[i])
        if line_key not in lines_map:
            lines_map[line_key] = []
        lines_map[line_key].append(OCRWord(text, x, y, w, h))
        
    ocr_lines = [OCRLine(words) for words in lines_map.values()]
    return OCRResult(full_text, ocr_lines)


def extract_from_ocr(pdf_path: str) -> Dict[str, Any]:
    """
    Extracts table and header from scanned/image-based PDF using cross-platform OCR:
    - Windows: Windows Media OCR (winocr) or Tesseract OCR
    - Linux / Render: Tesseract OCR (pytesseract)
    """
    backend = get_ocr_backend()
    if backend == "none":
        if platform.system() == "Windows":
            raise RuntimeError("No OCR backend is available. Please ensure winocr or Tesseract OCR is installed.")
        else:
            raise RuntimeError("Tesseract OCR is not installed on this server. Please install tesseract-ocr system package and pytesseract.")
            
    doc = pdfium.PdfDocument(pdf_path)
    all_rows = []
    full_text_pages = []
    
    for page_idx in range(len(doc)):
        page = doc[page_idx]
        # Render high-resolution image (scale=3.0 -> 300 DPI)
        pil_image = page.render(scale=3.0).to_pil()
        
        # Run OCR with selected backend
        if backend == "winocr":
            ocr_result = run_winocr_recognize(pil_image, 'en')
        elif backend == "tesseract":
            ocr_result = run_tesseract_recognize(pil_image, 'eng')
        else:
            raise RuntimeError(f"Unsupported OCR backend: {backend}")
            
        page_text = ocr_result.text or ""
        full_text_pages.append(page_text)
        
        # Parse table line items
        rows = parse_ocr_line_items(ocr_result.lines, pil_image.width, pil_image.height)
        all_rows.extend(rows)
        
    combined_text = "\n".join(full_text_pages)
    header_info = extract_header_from_text(combined_text)
    
    return {
        "header": header_info,
        "columns": TARGET_COLUMNS,
        "rows": all_rows,
        "mode": "OCR",
        "pages_count": len(doc)
    }


def process_pdf(pdf_path: str) -> Dict[str, Any]:
    """
    Main entry point for PDF processing:
    1. Validates the PDF file.
    2. Inspects text density to choose between Vector PDF extraction and OCR extraction.
    3. Guarantees structured return format.
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"File not found: {pdf_path}")
        
    if os.path.getsize(pdf_path) == 0:
        raise ValueError("Uploaded PDF file is empty.")
        
    # Check if text extraction is viable
    try:
        with pdfplumber.open(pdf_path) as pdf:
            if len(pdf.pages) == 0:
                raise ValueError("PDF contains 0 pages.")
                
            total_chars = sum(len((p.extract_text() or "").strip()) for p in pdf.pages)
            pages_count = len(pdf.pages)
            avg_chars_per_page = total_chars / max(pages_count, 1)
            
    except Exception as e:
        if "password" in str(e).lower():
            raise ValueError("PDF is password-protected. Please upload an unprotected file.")
        raise ValueError(f"Unable to read PDF file: {str(e)}")
        
    # If text is present, extract via pdfplumber
    if avg_chars_per_page > 35:
        result = extract_from_pdfplumber(pdf_path)
        # If pdfplumber didn't detect rows (e.g. text without clear table grid), fallback to OCR
        if len(result.get("rows", [])) > 0:
            return result
            
    # Scanned or image-based PDF -> OCR
    return extract_from_ocr(pdf_path)
