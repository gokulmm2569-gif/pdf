#!/usr/bin/env bash
# Exit on error
set -o errexit

echo "========================================="
echo "   Render Build: PDF-to-Excel Web App    "
echo "========================================="

echo "1. Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "2. Checking Tesseract OCR binary..."
if command -v tesseract &> /dev/null; then
    echo "Tesseract OCR is already installed in system PATH: $(which tesseract)"
else
    echo "Tesseract not found in default PATH. Checking if apt-get can download packages..."
    if command -v apt-get &> /dev/null; then
        mkdir -p .apt
        apt-get update -y || true
        apt-get download tesseract-ocr tesseract-ocr-eng libtesseract5 liblept5 || true
        for deb in *.deb; do
            if [ -f "$deb" ]; then
                dpkg -x "$deb" .apt/
                rm "$deb"
            fi
        done
        echo "Extracted .deb packages into .apt"
    fi
fi

echo "Build complete."
