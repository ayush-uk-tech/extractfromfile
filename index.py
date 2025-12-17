from flask import Flask, request, jsonify
import requests
import os
import io
from io import BytesIO
from docx import Document
from pypdf import PdfReader

app = Flask(__name__)

# ==========================================
#  ROBUST FILE TYPE DETECTION
# ==========================================

def detect_file_type(content: bytes) -> str:
    """
    Detects file type by reading the first few 'magic bytes' of the file.
    This works even if the URL has no extension.
    """
    # Check for PDF signature (%PDF)
    if content.startswith(b'%PDF'):
        return ".pdf"
    
    # Check for ZIP signature (PK..). DOCX files are actually ZIP files.
    # almost all modern Office files (docx, xlsx, pptx) start with PK.
    if content.startswith(b'PK\x03\x04'):
        return ".docx"
        
    # Check for Legacy DOC signature (D0 CF 11 E0)
    if content.startswith(b'\xD0\xCF\x11\xE0'):
        return ".doc"
        
    return "unknown"

# ==========================================
#  EXTRACTORS
# ==========================================

def extract_docx(content: bytes) -> str:
    try:
        doc = Document(BytesIO(content))
        return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
    except Exception as e:
        return f"Error processing DOCX: {str(e)}"

def extract_pdf(content: bytes) -> str:
    try:
        reader = PdfReader(BytesIO(content))
        text = []
        for page in reader.pages:
            text.append(page.extract_text() or "")
        return "\n".join(text)
    except Exception as e:
        return f"Error processing PDF: {str(e)}"

def extract_text_from_url(file_url: str) -> str:
    # 1. Download the file
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        r = requests.get(file_url, headers=headers, timeout=30)
        r.raise_for_status()
        content = r.content
    except Exception as e:
        return f"Failed to download file: {str(e)}"

    # 2. Detect Type using Magic Bytes (Ignore URL)
    ext = detect_file_type(content)

    # 3. Route to Extractor
    if ext == ".pdf":
        return extract_pdf(content)
        
    elif ext == ".docx":
        # Additional safety: Try to open as DOCX. If it fails, it might be an XLSX or just a ZIP.
        try:
            return extract_docx(content)
        except:
            return "Error: File detected as ZIP format but is not a valid DOCX."
            
    elif ext == ".doc":
        return "ERROR: This is a legacy .doc file. Vercel cannot process these. Please convert to .docx or .pdf."
        
    elif ext == "unknown":
        # Last Resort: Try to decode as plain text
        try:
            return content.decode("utf-8")
        except:
            return "Error: Unknown file type and not valid text."
            
    return "Error: Unhandled file type."

# ==========================================
#  API ROUTES
# ==========================================

@app.route('/', methods=['GET'])
def home():
    return "Magic-Byte Extractor API is Running"

@app.route('/extract', methods=['POST'])
def extract_endpoint():
    try:
        data = request.get_json()
        if not data or 'url' not in data:
            return jsonify({"error": "Missing 'url' in JSON body"}), 400
            
        url = data['url']
        extracted_text = extract_text_from_url(url)
        
        return jsonify({
            "success": True,
            "detected_type": "Auto-Detected via Magic Bytes", 
            "url": url,
            "text": extracted_text
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
