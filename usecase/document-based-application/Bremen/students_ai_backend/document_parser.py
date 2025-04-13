from flask import Flask, request, jsonify, render_template, send_from_directory
import os
import requests
import json
from dotenv import load_dotenv
from flask_cors import CORS
from bs4 import BeautifulSoup
from flask_cors import cross_origin

# .env 파일에서 API Key 로드
load_dotenv()
API_KEY = os.getenv("UPSTAGE_API_KEY")
API_URL = "https://api.upstage.ai/v1/document-digitization"

# Flask 앱 초기화 및 CORS 설정
# 디렉토리 경로 설정
INPUT_DIR = "input_pdfs"
OUTPUT_DIR = "output_html"
PREVIEW_DATA_DIR = "output_data"
STATIC_PDF_DIR = os.path.join("static", "pdfs")
HIGHLIGHT_DIR = "data"

# 필요한 디렉토리들이 존재하지 않으면 생성
os.makedirs(INPUT_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(PREVIEW_DATA_DIR, exist_ok=True)
os.makedirs(STATIC_PDF_DIR, exist_ok=True)
os.makedirs(HIGHLIGHT_DIR, exist_ok=True)

