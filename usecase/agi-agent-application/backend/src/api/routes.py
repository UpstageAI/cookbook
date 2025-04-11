"""Flask routes for the legal assistant API"""

import os
import json
import uuid
import logging
from flask import Flask, request, jsonify, Response, session
from werkzeug.utils import secure_filename
import boto3
from botocore.config import Config
import requests
from datetime import datetime
import io

# Local imports
from ..agent.core import process_query
from ..tools.tool_registry import get_registered_tools
from ..imsi.main_one import *
from ..imsi.main_two import *
from ..imsi.basic import *
from ..imsi.model import db, PDFFile
from src.config import UPLOADS_DIR

# Configure logging
logger = logging.getLogger(__name__)

# Create Flask app and configure it
app = Flask(__name__)
app.secret_key = os.urandom(24)  # For session management
pdf_counter = 0

# Register tools
tools = get_registered_tools()

# S3 설정
BUCKET_NAME = os.environ.get('BUCKET_NAME', 'wetube-gwanwoo')
s3 = boto3.client('s3',
    aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
    region_name='ap-northeast-2',
    config=Config(signature_version='s3v4')
)

def user_query():
    # Get the query from JSON request
    if request.is_json:
        data = request.get_json()
        query = data.get("query")
    else:
        query = request.form.get("query")
    
    if not query:
        return jsonify({
            "type": "simple_dialogue", 
            "response": "쿼리가 제공되지 않았습니다.", 
            "status": "error", 
            "message": "Query not provided"
        }), 400
    
    try:
        # Get the file ID from the session
        file_id = session.get('pdf_file_id')
        file_id = "0"
        logger.info(f"Retrieved file ID from session: {file_id}")
        
        # Process the query with the file ID
        response = process_query(query, tools, file_id)
        print(f"Response: {response}")
        response_data = json.dumps(response, ensure_ascii=False)
        return Response(response_data, content_type="application/json; charset=utf-8")
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({
            "type": "simple_dialogue", 
            "response": f"오류: {str(e)}", 
            "status": "error", 
            "message": str(e)
        }), 500

# Keep the original query endpoint for backward compatibility
@app.route('/api/chat', methods=['POST'])
def query_agent():
    return user_query()


@app.route('/api/pdf-upload', methods=['POST'])
def upload_pdf():
    """
    프론트엔드에서 PDF 파일 업로드를 위한 엔드포인트
    """
    global pdf_counter  # 전역 변수 사용
    print("Upload endpoint called")  # 요청이 들어왔는지 확인
    
    if 'file' not in request.files:
        print("No document in request.files")  # 파일이 없는 경우 로깅
        return jsonify({"error": "파일이 전송되지 않았습니다."}), 400
    
    file = request.files['file']
    print(f"Received file: {file.filename}")  # 파일 이름 로깅
    
    if file.filename == '':
        print("No selected file")  # 파일이 선택되지 않은 경우 로깅
        return jsonify({"error": "선택된 파일이 없습니다."}), 400
    
    if not file.filename.lower().endswith('.pdf'):
        print(f"Invalid file type: {file.filename}")  # 잘못된 파일 타입 로깅
        return jsonify({"error": "PDF 파일만 업로드 가능합니다."}), 400
    
    try:
        # 파일 저장
        filename = secure_filename(file.filename)

        # Read the file content
        file_content = file.read()
        file.seek(0)  # Reset position for later use
        
        # Check if it's actually a PDF
        if not file_content.startswith(b'%PDF-'):
            print("Warning: File doesn't look like a valid PDF")
            return jsonify({"error": "업로드된 파일이 유효한 PDF 형식이 아닙니다."}), 400

        # Use a unique file counter for each upload
        s3_path = f"{pdf_counter}"
        
        # Save file to S3 as binary PDF
        s3.put_object(
            Body=file_content,
            Bucket=BUCKET_NAME,
            Key=s3_path,
            ContentType='application/pdf',
            ACL='public-read'
        )
        
        # Sample file url for client
        file_path = f"https://{BUCKET_NAME}.s3.ap-northeast-2.amazonaws.com/{s3_path}"
        
        # Store the S3 path in the session for later use
        session['pdf_file_id'] = s3_path
        logger.info(f"Stored PDF file ID in session: {s3_path}")
        
        # Use the CURRENT uploaded file for processing, not a fixed one
        file_obj = io.BytesIO(file_content)
        file_obj.seek(0)
        
        API_KEY = get_upstage_api_key("backend/conf.d/config.yaml")
        document_parser = DocumentParser(API_KEY)
        llm_summarizer = LLMSummarizer()
        pdf_processor = PDFProcessor(document_parser, llm_summarizer)

        # Extract summary from the CURRENT file
        print(f"Processing file: {s3_path}")
        parse_result, summary = pdf_processor.process_pdf(file_obj)

        # Reset file object for reuse
        file_obj.seek(0)

        PROMPT_PATH = "backend/prompts/find_toxic_clause.txt"
        CASE_DB_PATH = "backend/datasets/case_db.json"

        document_parser = DocumentParser(API_KEY)

        case_retriever = CaseLawRetriever(
            case_db_path=CASE_DB_PATH,
            embedding_path="backend/datasets/precomputed_embeddings.npz"
        )

        llm_highlighter = ToxicClauseFinder(
            app=app,
            prompt_path=PROMPT_PATH,
            case_retriever=case_retriever
        )
        print("Starting document analysis...")

        text = parse_result
        if not text:
            return jsonify({"error": "파싱된 텍스트가 없습니다."}), 400
        
        highlight_result = llm_highlighter.highlight(text)

        if not highlight_result:
            return jsonify({"error": "분석 결과가 없습니다."}), 400
        
        high_json = json.dumps(highlight_result, ensure_ascii=False, indent=2)
        high_json = json.loads(high_json)
        # 변환
        result_highlight=dict()
        converted = []
        
        print(high_json)
        for item in high_json:
            converted.append(item["독소조항"])
            rationale = item["친절한_설명"]
        
        result_highlight["type"] = "highlights"
        result_highlight["rationale"] = rationale
        result_highlight["highlights"] = converted
        
        # Increment counter AFTER successful processing
        
        print(f"Finished processing file. New counter: {pdf_counter}")
        
        response_data = {
            "status": "success",
            "message": "Successfully uploaded file",
            "filename": filename,
            "file_url": file_path,
            "pdf_id": f"{pdf_counter}",
            "summary": summary["summary"],
            "key_values": {
                "annualReturn": summary["annualReturn"],
                "volatility": summary["volatility"],
                "managementFee": summary["managementFee"],
                "minimumInvestment": summary["minimumInvestment"],
                "lockupPeriod": summary["lockupPeriod"],
                "riskLevel": summary["riskLevel"]
            },
            "key_findings": summary["key_findings"],
            "highlights": converted  # 원본 객체를 그대로 사용
        }
        pdf_counter += 1
        return jsonify(response_data), 200

    except Exception as e:
        print(f"Error during file upload: {str(e)}")  # 에러 로깅
        import traceback
        print(traceback.format_exc())  # Add full stack trace
        return jsonify({"error": str(e)}), 500

@app.route('/reset', methods=['POST'])
def reset_session():
    # Remove the stored file if it exists
    if 'pdf_file_path' in session:
        try:
            os.remove(session['pdf_file_path'])
        except:
            pass
    
    # Clear the session
    session.clear()
    return jsonify({"success": True})
