import base64
import json
import os
import streamlit as st
from openai import OpenAI
from typing import Dict, Any, List, Optional

# 전역 변수
_UPSTAGE_API_KEY = None

def update_upstage_api_key():
    """전역 Upstage API 키 업데이트"""
    global _UPSTAGE_API_KEY
    _UPSTAGE_API_KEY = st.session_state.get('upstage_api_key', '')
    print(f"Upstage API 키 업데이트: {'설정됨' if _UPSTAGE_API_KEY else '없음'}")

class InformationExtractor:
    def __init__(self, api_key=None):
        # API 키 우선순위: 생성자 파라미터 > 전역 변수 > 세션 상태
        self.api_key = api_key if api_key is not None else (_UPSTAGE_API_KEY or st.session_state.get('upstage_api_key', ''))
        self.base_url = "https://api.upstage.ai/v1/information-extraction"
        
    def encode_img_to_base64(self, img_path: str) -> str:
        """이미지 파일을 base64로 인코딩"""
        try:
            with open(img_path, 'rb') as img_file:
                img_bytes = img_file.read()
                base64_data = base64.b64encode(img_bytes).decode('utf-8')
                return base64_data
        except Exception as e:
            raise ValueError(f"이미지 인코딩 오류: {str(e)}")
    
    def extract_information(self, img_path: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        이미지에서 정보 추출하는 메소드
        
        Args:
            img_path: 이미지 파일 경로
            schema: 추출할 정보의 스키마 정의
            
        Returns:
            Dict: 추출된 정보 결과
        """
        if not self.api_key:
            return {
                'success': False,
                'error': 'Upstage API 키가 설정되지 않았습니다. API 설정 탭에서 API 키를 입력해주세요.'
            }
            
        # 이미지 파일 존재 여부 확인
        if not os.path.exists(img_path):
            return {
                'success': False,
                'error': f'이미지 파일을 찾을 수 없습니다: {img_path}'
            }
            
        try:
            # 이미지를 base64로 인코딩
            base64_data = self.encode_img_to_base64(img_path)
            
            # API 클라이언트 초기화
            client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url
            )
            
            # Information Extraction API 호출
            extraction_response = client.chat.completions.create(
                model="information-extract",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/png;base64,{base64_data}"}
                            }
                        ]
                    }
                ],
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "document_schema",
                        "schema": schema
                    }
                }
            )
            
            # 응답 결과 파싱
            extracted_content = json.loads(extraction_response.choices[0].message.content)
            return {
                'success': True,
                'data': extracted_content,
                'metadata': {
                    'file_name': os.path.basename(img_path),
                }
            }
            
        except ValueError as e:
            return {
                'success': False,
                'error': str(e)
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'정보 추출 API 오류: {str(e)}'
            }


def information_extract(img_path: str, schema_properties: Dict[str, Dict[str, Any]], required_fields: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    이미지에서 지정된 스키마에 따라 정보를 추출합니다.
    
    Args:
        img_path: 정보를 추출할 이미지 파일 경로
        schema_properties: 추출할 정보의 속성 정의 (JSON 스키마 형식)
        required_fields: 필수로 추출해야 하는 필드 목록 (선택 사항)
        
    Returns:
        Dict: 추출된 정보 또는 오류
    """
    extractor = InformationExtractor()
    
    # 스키마 구성
    schema = {
        "type": "object",
        "properties": schema_properties
    }
    
    # 필수 필드가 있는 경우 추가
    if required_fields:
        schema["required"] = required_fields
    
    # 정보 추출 실행
    return extractor.extract_information(img_path, schema) 