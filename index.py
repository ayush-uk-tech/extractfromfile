from flask import Flask, request, jsonify
import requests
import os
import mimetypes
import subprocess
from io import BytesIO
from docx import Document
from pypdf import PdfReader
import tempfile

app = Flask(__name__)

# ==========================================
# YOUR ORIGINAL LOGIC & STRUCTURE
# ==========================================

def extract_text_from_url(file_url: str) -> str:
    # 1️⃣ Download file
    # (Added User-Agent to prevent 403 errors from some servers)
    headers = {'User-Agent': 'Mozilla/5.0'} 
    r = requests.get(file_url, headers=headers, timeout=30)
    r.raise_for_status()
    content = r.content

    # 2️⃣ Detect extension
    filename = os.path.basename(file_url.split("?")[0])
    ext = os.path.splitext(filename)[1].lower()

    if not ext:
        mime = r.headers.get("Content-Type")
        ext = mimetypes.guess_extension(mime or "")

    # 3️⃣ Route to extractors (Exactly as your script)
    if ext == ".docx":
        return extract_docx(content)

    elif ext == ".doc":
        return extract_doc_with_libreoffice(content)

    elif ext == ".pdf":
        return extract_pdf(content)

    elif ext == ".txt":
        return content.decode("utf-8", errors="ignore")

    else:
        raise ValueError(f"Unsupported file type: {ext}")


# -------- Extractors --------

def extract_docx(content: bytes) -> str:
    doc = Document(BytesIO(content))
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())


def extract_pdf(content: bytes) -> str:
    reader = PdfReader(BytesIO(content))
    text = []
    for page in reader.pages:
        text.append(page.extract_text() or "")
    return "\n".join(text)


def extract_doc_with_libreoffice(content: bytes) -> str:
    # NOTE: This function structure is kept, but 'soffice' cannot run on Vercel.
    # If you deploy this to a Docker container (like Render/Railway), uncomment the original code below.
    return "ERROR: Legacy .doc files require LibreOffice (soffice), which is not available on Vercel environment."

    # --- Original Code (Works on Local/Docker, not Vercel) ---
    # with tempfile.TemporaryDirectory() as tmp:
    #     doc_path = os.path.join(tmp, "input.doc")
    #     txt_path = os.path.join(tmp, "input.txt")
    #     with open(doc_path, "wb") as f:
    #         f.write(content)
    #     subprocess.run(["soffice", "--headless", "--convert-to", "txt", doc_path, "--outdir", tmp], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    #     with open(txt_path, "r", encoding="utf-8", errors="ignore") as f:
    #         return f.read()


# ==========================================
# FLASK API WRAPPER
# ==========================================

@app.route('/', methods=['GET'])
def home():
    return "Python Extractor API is Running"

@app.route('/extract', methods=['POST'])
def extract_endpoint():
    try:
        # Get JSON data
        data = request.get_json()
        
        # Check if URL exists
        if not data or 'url' not in data:
            return jsonify({"error": "Please provide a 'url' in the JSON body"}), 400
            
        # Call your original function
        url = data['url']
        result_text = extract_text_from_url(url)
        
        # Return result
        return jsonify({
            "success": True,
            "url": url,
            "text": result_text
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
