from flask import Flask, request, jsonify
import requests
import os
import mimetypes
from io import BytesIO
from docx import Document
from pypdf import PdfReader

app = Flask(__name__)

# -------- Core Logic --------

def extract_docx(content: bytes) -> str:
    try:
        doc = Document(BytesIO(content))
        return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
    except Exception as e:
        return f"Error reading DOCX: {str(e)}"

def extract_pdf(content: bytes) -> str:
    try:
        reader = PdfReader(BytesIO(content))
        text = []
        for page in reader.pages:
            text.append(page.extract_text() or "")
        return "\n".join(text)
    except Exception as e:
        return f"Error reading PDF: {str(e)}"

def extract_text_from_url(file_url: str) -> str:
    # 1. Download file
    headers = {'User-Agent': 'Mozilla/5.0'}
    r = requests.get(file_url, headers=headers, timeout=30)
    r.raise_for_status()
    content = r.content

    # 2. Detect extension
    filename = os.path.basename(file_url.split("?")[0])
    ext = os.path.splitext(filename)[1].lower()

    if not ext:
        mime = r.headers.get("Content-Type")
        ext = mimetypes.guess_extension(mime or "")

    # 3. Route to extractor
    if ext == ".docx":
        return extract_docx(content)

    elif ext == ".pdf":
        return extract_pdf(content)

    elif ext == ".txt":
        return content.decode("utf-8", errors="ignore")
        
    elif ext == ".doc":
        return "ERROR: Legacy .doc files require LibreOffice and cannot be processed on Vercel Serverless. Please convert to .docx or .pdf."

    else:
        raise ValueError(f"Unsupported file type: {ext}")

# -------- API Route --------

@app.route('/', methods=['GET'])
def home():
    return jsonify({"status": "running", "message": "Send a POST request to /extract with a 'url' field."})

@app.route('/extract', methods=['POST'])
def extract_endpoint():
    try:
        data = request.get_json()
        
        if not data or 'url' not in data:
            return jsonify({"error": "Missing 'url' in JSON body"}), 400
            
        file_url = data['url']
        extracted_text = extract_text_from_url(file_url)
        
        return jsonify({
            "success": True,
            "url": file_url,
            "text": extracted_text
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# For local testing
if __name__ == "__main__":
    app.run(debug=True, port=5000)
