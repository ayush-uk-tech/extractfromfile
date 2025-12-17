from flask import Flask, request, jsonify
import requests
import os
import mimetypes
from io import BytesIO
from docx import Document
from pypdf import PdfReader

app = Flask(__name__)

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
    headers = {'User-Agent': 'Mozilla/5.0'}
    r = requests.get(file_url, headers=headers, timeout=30)
    r.raise_for_status()
    content = r.content

    filename = os.path.basename(file_url.split("?")[0])
    ext = os.path.splitext(filename)[1].lower()

    if not ext:
        mime = r.headers.get("Content-Type")
        ext = mimetypes.guess_extension(mime or "")

    if ext == ".docx":
        return extract_docx(content)
    elif ext == ".pdf":
        return extract_pdf(content)
    elif ext == ".txt":
        return content.decode("utf-8", errors="ignore")
    elif ext == ".doc":
        return "ERROR: Legacy .doc files cannot be processed on Vercel. Convert to .docx."
    else:
        return f"Unsupported file type: {ext}"

@app.route('/', methods=['GET'])
def home():
    return "API is Running"

@app.route('/extract', methods=['POST'])
def extract_endpoint():
    try:
        data = request.get_json()
        if not data or 'url' not in data:
            return jsonify({"error": "Missing 'url'"}), 400
        
        text = extract_text_from_url(data['url'])
        return jsonify({"text": text})

    except Exception as e:
        return jsonify({"error": str(e)}), 500
