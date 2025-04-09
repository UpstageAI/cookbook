import os
import yaml
import json
from numpy import dot
from numpy.linalg import norm
import requests
from werkzeug.utils import secure_filename


def get_openai_api_key(api_key_path):
    with open(api_key_path, 'r') as f:
        config = yaml.safe_load(f)
    os.environ['OPENAI_API_KEY'] = config['openai']['key']

def get_upstage_api_key(api_key_path):
    with open(api_key_path, 'r') as f:
        config = yaml.safe_load(f)
    return config['upstage']['key']

def get_tavily_api_key(api_key_path):
    with open(api_key_path, 'r') as f:
        config = yaml.safe_load(f)
    return config['tavily']['key']

def load_prompt(args):
	with open(args, "r", encoding="UTF-8") as f:
		prompt = yaml.load(f, Loader=yaml.FullLoader)["prompt"]
	return prompt

def load_data(arg):
    with open(arg, 'r',encoding='utf-8') as json_file:
        data = json.load(json_file)

    return data

def cos_sim(a, b):
    return dot(a, b) / (norm(a) * norm(b))

def load_prefix(args):
	with open(args, "r", encoding="UTF-8") as f:
		prefix = yaml.load(f, Loader=yaml.FullLoader)["prefix"]
	return prefix

def load_message(args):
	with open(args, "r", encoding="UTF-8") as f:
		prefix = yaml.load(f, Loader=yaml.FullLoader)["message"]
	return prefix

# PDF 파일을 외부 파싱 API를 통해 처리하는 클래스
class DocumentParser:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.url = "https://api.upstage.ai/v1/document-digitization"
    
    def parse(self, file_obj) -> dict:
        """
        file_obj: 파일 객체 (예: Flask의 request.files['document'])
        반환: API 응답 JSON을 dict로 반환
        """
        headers = {"Authorization": f"Bearer {self.api_key}"}
        # API에서는 파일 객체를 그대로 받을 수 있음.
        files = {"document": file_obj}
        # 필요에 따라 추가 옵션 지정 (예: OCR 강제 적용, base64 인코딩 옵션, 모델 선택 등)
        data = {"ocr": "force", "base64_encoding": "[]", "model": "document-parse", "output_formats" : "['text']"}
        
        response = requests.post(self.url, headers=headers, files=files, data=data)
        
        return response.text
    
