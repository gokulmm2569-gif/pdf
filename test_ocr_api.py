import urllib.request
import json

def test_ocr_api():
    boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
    with open('sample_invoices/imran_air_express_scanned.pdf', 'rb') as f:
        pdf_data = f.read()

    headers = {
        'Content-Type': f'multipart/form-data; boundary={boundary}'
    }

    body = (
        f'--{boundary}\r\n'
        f'Content-Disposition: form-data; name="file"; filename="imran_air_express_scanned.pdf"\r\n'
        f'Content-Type: application/pdf\r\n\r\n'
    ).encode('utf-8') + pdf_data + f'\r\n--{boundary}--\r\n'.encode('utf-8')

    req = urllib.request.Request('http://127.0.0.1:8000/api/process', data=body, headers=headers)
    with urllib.request.urlopen(req) as resp:
        print("OCR API STATUS:", resp.status)
        data = json.loads(resp.read().decode('utf-8'))
        print("EXTRACTION SUCCESS:", data.get("success"))
        print("EXTRACTION ENGINE:", data.get("mode"))
        print("ROW COUNT:", data.get("row_count"))
        print("DOWNLOAD URL:", data.get("download_url"))
        print("SAMPLE ROW 0:", data.get("rows")[0] if data.get("rows") else None)
        
        # Test download
        dl_url = f"http://127.0.0.1:8000{data.get('download_url')}"
        with urllib.request.urlopen(dl_url) as dl_resp:
            excel_bytes = dl_resp.read()
            print("OCR EXCEL DOWNLOAD STATUS:", dl_resp.status)
            print("OCR EXCEL BYTES RECEIVED:", len(excel_bytes))

if __name__ == "__main__":
    test_ocr_api()
