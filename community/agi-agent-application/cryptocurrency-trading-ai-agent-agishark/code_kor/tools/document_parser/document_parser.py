import requests
import streamlit as st
import os
from typing import List, Dict, Any

# 전역 변수
_UPSTAGE_API_KEY = None

def update_upstage_api_key():
    """전역 Upstage API 키 업데이트"""
    global _UPSTAGE_API_KEY
    _UPSTAGE_API_KEY = st.session_state.get('upstage_api_key', '')
    print(f"Upstage API 키 업데이트: {'설정됨' if _UPSTAGE_API_KEY else '없음'}")

class DocumentParser:
    def __init__(self, api_key=None):
        # API 키 우선순위: 생성자 파라미터 > 전역 변수 > 세션 상태
        self.api_key = api_key if api_key is not None else (_UPSTAGE_API_KEY or st.session_state.get('upstage_api_key', ''))
        self.url = "https://api.upstage.ai/v1/document-ai/document-parse"
        self.base_path = "tools/web2pdf/always_see_doc_storage/"
    
    def __call__(self, file_names: List[str]) -> Dict[str, Any]:
        """Tool interface required for agents library"""
        return self.parse_document(file_names)
        
    def parse_document(self, file_names: List[str]) -> Dict[str, Any]:
        """
        문서 파싱을 수행하는 메서드 - 파일명 리스트를 처리
        
        Args:
            file_names: 파싱할 PDF 파일 이름 목록 (확장자 없이)
            
        Returns:
            Dict: 파싱 결과를 담은 딕셔너리
        """
        if not self.api_key:
            return {
                'success': False,
                'error': 'Upstage API 키가 설정되지 않았습니다. API 설정 탭에서 API 키를 입력해주세요.'
            }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }
        
        data = {
            "ocr": "force",
            "coordinates": True,
            "chart_recognition": True,
            "output_formats": "['text']",
            "base64_encoding": "['table']",
            "model": "document-parse"
        }

        # 입력이 리스트가 아닌 경우 리스트로 변환
        if not isinstance(file_names, list):
            if isinstance(file_names, str):
                file_names = [file_names]
            else:
                return {
                    'success': False,
                    'error': '파일명 리스트를 제공해주세요.'
                }

        all_results = []
        for file_name in file_names:
            # 리스트에 None이나 빈 문자열이 있는 경우 건너뛰기
            if not file_name:
                continue
                
            # 확장자 처리 (.pdf가 이미 있는지 확인)
            if not file_name.lower().endswith('.pdf'):
                file_path = os.path.join(self.base_path, f"{file_name}.pdf")
            else:
                file_path = os.path.join(self.base_path, file_name)
            
            # 파일 존재 여부 확인
            if not os.path.exists(file_path):
                all_results.append({
                    'success': False,
                    'error': f'파일을 찾을 수 없습니다: {file_path}',
                    'file_name': file_name
                })
                continue
            
            # 파일 읽기
            try:
                with open(file_path, 'rb') as f:
                    file_content = f.read()
            except Exception as e:
                all_results.append({
                    'success': False,
                    'error': f'파일 읽기 오류: {str(e)}',
                    'file_name': file_name
                })
                continue

            # API 요청
            files = {
                "document": (os.path.basename(file_path), file_content)
            }
            
            try:
                response = requests.post(self.url, headers=headers, files=files, data=data)
                response.raise_for_status()
                
                result = response.json()
                if 'content' in result and 'text' in result['content']:
                    all_results.append({
                        'success': True,
                        'text': result['content']['text'],
                        'metadata': {
                            'file_name': os.path.basename(file_path),
                            'parse_time': result.get('parse_time', 0)
                        }
                    })
                else:
                    all_results.append({
                        'success': False,
                        'error': '문서 파싱 결과가 예상된 형식이 아닙니다.',
                        'file_name': file_name
                    })
                    
            except requests.exceptions.RequestException as e:
                all_results.append({
                    'success': False,
                    'error': f'API 요청 오류: {str(e)}',
                    'file_name': file_name
                })
        
        return {
            'success': True,
            'results': all_results,
            'count': len(all_results),
            'successful_count': sum(1 for r in all_results if r.get('success', False))
        }

# 사용 예시:
# parser = DocumentParser()
# file_list = ["bitcoin_report", "bitcoin_report2"]  # .pdf 확장자는 자동으로 추가됨
# results = parser.parse_document(file_list)
# if results['success']:
#     for result in results['results']:
#         if result['success']:
#             print(f"File: {result['metadata']['file_name']}")
#             print(f"Text: {result['text'][:100]}...")  # 첫 100자만 출력
#         else:
#             print(f"Error in {result.get('file_name', 'unknown')}: {result['error']}")
# else:
#     print(f"Error: {results['error']}")