FROM python:3.12-slim

# Install system dependencies including Tesseract OCR and English language model
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-eng \
    libtesseract-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Default port
ENV PORT=8000
EXPOSE 8000

# Start server via root launcher
CMD ["python", "app.py"]
