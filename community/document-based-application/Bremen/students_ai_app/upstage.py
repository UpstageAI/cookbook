from flask import Flask, request, jsonify
import os
import requests
import base64
import json
from dotenv import load_dotenv
from flask_cors import CORS

# 환경변수 로드
load_dotenv()
API_KEY = os.getenv("UPSTAGE_API_KEY")

# Upstage API URL
DIGITIZE_URL = "https://api.upstage.ai/v1/document-digitization"
EXTRACT_URL = "https://api.upstage.ai/v1/information-extraction"

# Flask 설정
app = Flask(__name__)
CORS(app)

# 디렉토리
INPUT_DIR = "input_pdfs"
OUTPUT_HTML_DIR = "output_html"
OUTPUT_JSON_DIR = "output_extracted"
os.makedirs(INPUT_DIR, exist_ok=True)
os.makedirs(OUTPUT_HTML_DIR, exist_ok=True)
os.makedirs(OUTPUT_JSON_DIR, exist_ok=True)

# 문서 업로드 후 HTML로 변환
@app.route('/upload-pdf', methods=['POST'])
def upload_pdf():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    save_path = os.path.join(INPUT_DIR, file.filename)
    file.save(save_path)

    with open(save_path, 'rb') as f:
        files = {'document': (file.filename, f, 'application/pdf')}
        data = {
            'ocr': 'force',
            'model': 'document-parse',
            'key_extraction': 'true'
        }
        headers = {'Authorization': f'Bearer {API_KEY}'}
        response = requests.post(DIGITIZE_URL, headers=headers, files=files, data=data)
        response2 = requests.post(EXTRACT_URL, headers=headers, files=files, data=data)

    if response.status_code == 200:
        result = response.json()
        result2 = response2.json()
        html_output = result.get("content", {}).get("html", "")
        html_filename = os.path.splitext(file.filename)[0] + '.html'
        html_path = os.path.join(OUTPUT_HTML_DIR, html_filename)

        key_values = result2.get("key_value", [])
        json_filename = os.path.splitext(file.filename)[0] + '.json'
        json_path = os.path.join(OUTPUT_JSON_DIR, json_filename)

        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_output)
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(key_values, f, ensure_ascii=False, indent=2)

        return jsonify({
            "filename": file.filename,
            "html_file": html_filename,
            "json_file": json_filename,
            "key_value": key_values,
            "status": "success"
        })
    else:
        return jsonify({
            "filename": file.filename,
            "error": response.text,
            "status": "failed"
        })

# 서버 실행
if __name__ == '__main__':
    app.run(debug=True, port=8000, host='0.0.0.0')
