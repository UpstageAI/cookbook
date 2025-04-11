import os
import streamlit as st
from openai import OpenAI
import asyncio
import threading
import json
from typing import List, Dict, Any, Optional

# Vector Store ID를 저장할 파일 경로
VECTOR_STORE_ID_FILE = "data/vector_store_id.json"

# 전역 캐시 변수
_OPENAI_API_KEY = None
_VECTOR_STORE_ID = None

def update_global_cache():
    """전역 캐시 변수 업데이트"""
    global _OPENAI_API_KEY, _VECTOR_STORE_ID
    
    # API 키 업데이트
    _OPENAI_API_KEY = st.session_state.get('openai_key', '')
    
    # 벡터 스토어 ID 업데이트
    _VECTOR_STORE_ID = st.session_state.get('vector_store_id', '')
    
    print(f"전역 캐시 변수 업데이트 - API 키: {'설정됨' if _OPENAI_API_KEY else '없음'}, 벡터 스토어 ID: {_VECTOR_STORE_ID or '없음'}")

def get_openai_client():
    """OpenAI 클라이언트 가져오기"""
    global _OPENAI_API_KEY
    
    # API 키 우선순위: 전역 캐시 > 세션 상태
    api_key = _OPENAI_API_KEY or st.session_state.get('openai_key', '')
    
    if not api_key:
        print("OpenAI API 키가 설정되지 않았습니다.")
        return None
    
    try:
        client = OpenAI(api_key=api_key)
        return client
    except Exception as e:
        print(f"OpenAI 클라이언트 초기화 오류: {str(e)}")
        return None

def save_vector_store_id(vector_store_id: str) -> bool:
    """벡터 스토어 ID를 파일에 저장"""
    try:
        # 디렉토리가 없으면 생성
        os.makedirs(os.path.dirname(VECTOR_STORE_ID_FILE), exist_ok=True)
        
        with open(VECTOR_STORE_ID_FILE, 'w') as f:
            json.dump({'vector_store_id': vector_store_id}, f, indent=2)
        
        print(f"벡터 스토어 ID '{vector_store_id}'를 파일에 저장했습니다.")
        return True
    except Exception as e:
        print(f"벡터 스토어 ID 저장 오류: {str(e)}")
        return False

def load_vector_store_id() -> Optional[str]:
    """파일에서 벡터 스토어 ID 불러오기"""
    try:
        if os.path.exists(VECTOR_STORE_ID_FILE):
            with open(VECTOR_STORE_ID_FILE, 'r') as f:
                data = json.load(f)
                vector_store_id = data.get('vector_store_id')
                if vector_store_id:
                    print(f"파일에서 벡터 스토어 ID '{vector_store_id}'를 불러왔습니다.")
                    return vector_store_id
    except Exception as e:
        print(f"벡터 스토어 ID 불러오기 오류: {str(e)}")
    
    return None

def create_vector_store() -> Optional[str]:
    """벡터 스토어 생성 - 앱 시작 시 한 번만 호출"""
    # 이미 세션에 벡터 스토어 ID가 있는지 확인
    if 'vector_store_id' in st.session_state:
        print(f"세션에 저장된 벡터 스토어 사용: {st.session_state.vector_store_id}")
        return st.session_state.vector_store_id
    
    # 파일에서 벡터 스토어 ID 불러오기 시도
    stored_id = load_vector_store_id()
    if stored_id:
        st.session_state.vector_store_id = stored_id
        return stored_id
    
    # OpenAI API 키 확인
    if not st.session_state.openai_key:
        print("OpenAI API 키가 설정되지 않아 벡터 스토어를 생성할 수 없습니다.")
        return None
    
    # OpenAI 클라이언트 가져오기
    client = get_openai_client()
    if not client:
        return None
    
    try:
        # 벡터 스토어 생성
        vector_store = client.vector_stores.create(
            name="AI Trading Agent"
        )
        
        # 세션에 저장
        vector_store_id = vector_store.id
        st.session_state.vector_store_id = vector_store_id
        
        # 파일에 저장
        save_vector_store_id(vector_store_id)
        
        print(f"새 벡터 스토어 생성 완료: {vector_store_id}")
        return vector_store_id
    except Exception as e:
        print(f"벡터 스토어 생성 오류: {str(e)}")
        return None

def upload_to_vector_store(text_content: str, file_name: str, attributes: Dict = None, 
                          openai_api_key=None, vector_store_id=None) -> bool:
    # session_state 접근 전에 전달받은 vector_store_id 사용
    if vector_store_id is None:
        if 'vector_store_id' not in st.session_state:
            print("벡터 스토어가 초기화되지 않았습니다.")
            return False
        vector_store_id = st.session_state.vector_store_id
    
    client = get_openai_client()
    if not client:
        return False
    
    try:
        # 임시 파일 생성
        temp_file_path = f"temp_{file_name}.txt"
        with open(temp_file_path, "w", encoding="utf-8") as f:
            f.write(text_content)
        
        # 파일 업로드
        with open(temp_file_path, "rb") as f:
            print(f"파일 '{file_name}' 벡터 스토어에 업로드 시작...")
            upload_result = client.vector_stores.files.upload_and_poll(
                vector_store_id=vector_store_id,
                file=f,
                attributes=attributes or {}
            )
        
        # 임시 파일 삭제
        os.remove(temp_file_path)
        print(f"파일 '{file_name}' 업로드 완료: {upload_result.id}")
        return True
    except Exception as e:
        print(f"벡터 스토어 업로드 오류: {str(e)}")
        return False

def upload_file_to_vector_store(file_path: str, file_name: str, attributes: Dict = None, 
                               openai_api_key=None, vector_store_id=None) -> tuple:
    """파일을 직접 벡터 스토어에 업로드"""
    global _VECTOR_STORE_ID
    
    actual_vector_store_id = vector_store_id or _VECTOR_STORE_ID
    
    print(f"upload_file_to_vector_store 실행: ID={actual_vector_store_id}, 파일={file_name}")
    
    if not actual_vector_store_id:
        try:
            if 'vector_store_id' in st.session_state:
                actual_vector_store_id = st.session_state.vector_store_id
                print(f"세션에서 vector_store_id 가져옴: {actual_vector_store_id}")
            else:
                return False, "벡터 스토어 ID를 찾을 수 없습니다"
        except Exception as e:
            print(f"세션 상태 접근 오류: {str(e)}")
            return False, f"세션 상태 접근 오류: {str(e)}"
    
    client = get_openai_client()
    if not client:
        return False, "OpenAI 클라이언트를 초기화할 수 없습니다"
    
    try:
        # 파일 직접 업로드 - 'attributes' 인자 제거
        with open(file_path, "rb") as f:
            print(f"파일 '{file_name}' 벡터 스토어({actual_vector_store_id})에 직접 업로드 시작...")
            # 먼저 파일 업로드
            file_upload = client.vector_stores.files.upload(
                vector_store_id=actual_vector_store_id,
                file=f
            )
            
            # 속성 설정은 별도로 필요하다면 여기에 추가
            # attributes가 있으면 나중에 파일 메타데이터에 설정할 수 있음
            
            # 업로드 상태 확인
            file_status = client.vector_stores.files.retrieve(
                vector_store_id=actual_vector_store_id,
                file_id=file_upload.id
            )
        
        print(f"파일 '{file_name}' 직접 업로드 완료: {file_upload.id}")
        return True, None
    except Exception as e:
        error_msg = f"벡터 스토어 직접 업로드 오류: {str(e)}"
        print(error_msg)
        return False, error_msg

def search_vector_store(query: str, max_results: int = 5) -> List[Dict]:
    """벡터 스토어에서 검색 수행"""
    if 'vector_store_id' not in st.session_state:
        print("벡터 스토어가 초기화되지 않았습니다.")
        return []
    
    client = get_openai_client()
    if not client:
        return []
    
    vector_store_id = st.session_state.vector_store_id
    
    try:
        results = client.vector_stores.search(
            vector_store_id=vector_store_id,
            query=query,
            max_num_results=max_results,
            rewrite_query=True
        )
        
        # 결과 형식화
        formatted_results = []
        for result in results.data:
            content_text = '\n'.join([c.text for c in result.content])
            formatted_results.append({
                'file_id': result.file_id,
                'filename': result.filename,
                'score': result.score,
                'content': content_text
            })
        
        return formatted_results
    except Exception as e:
        print(f"벡터 스토어 검색 오류: {str(e)}")
        return []

def delete_from_vector_store(file_name: str) -> bool:
    """파일 이름으로 벡터 스토어에서 파일 삭제"""
    if 'vector_store_id' not in st.session_state:
        print("벡터 스토어가 초기화되지 않았습니다.")
        return False
    
    client = get_openai_client()
    if not client:
        return False
    
    vector_store_id = st.session_state.vector_store_id
    
    try:
        # 벡터 스토어에서 파일 목록 가져오기
        files = client.vector_stores.files.list(
            vector_store_id=vector_store_id
        )
        
        # 파일 이름으로 파일 찾기
        target_file = None
        for file in files.data:
            # 파일 속성에서 파일 이름 확인
            attributes = client.vector_stores.files.retrieve(
                vector_store_id=vector_store_id,
                file_id=file.id
            ).attributes
            
            if attributes and attributes.get('file_name') == file_name:
                target_file = file
                break
        
        if not target_file:
            print(f"벡터 스토어에서 파일 '{file_name}'을 찾을 수 없습니다.")
            return False
        
        # 파일 삭제
        client.vector_stores.files.delete(
            vector_store_id=vector_store_id,
            file_id=target_file.id
        )
        
        print(f"벡터 스토어에서 파일 '{file_name}' 삭제 완료")
        return True
    except Exception as e:
        print(f"벡터 스토어에서 파일 삭제 오류: {str(e)}")
        return False

def async_process(func, *args, **kwargs):
    """함수를 비동기적으로 실행하는 헬퍼 함수"""
    def run_in_thread(func, *args, **kwargs):
        result = func(*args, **kwargs)
        return result
    
    thread = threading.Thread(target=run_in_thread, args=(func, *args), kwargs=kwargs)
    thread.daemon = True
    thread.start()
    return thread

def format_results_for_llm(search_results: List[Dict]) -> str:
    """LLM을 위한 검색 결과 포맷팅"""
    if not search_results:
        return "검색 결과가 없습니다."
    
    formatted_text = "<sources>\n"
    for result in search_results:
        formatted_text += f"<result file_name='{result['filename']}' score='{result['score']:.2f}'>\n"
        formatted_text += f"<content>{result['content']}</content>\n"
        formatted_text += "</result>\n"
    formatted_text += "</sources>"
    
    return formatted_text

def synthesize_response(query: str, search_results: List[Dict]) -> str:
    """검색 결과를 바탕으로 응답 생성"""
    client = get_openai_client()
    if not client:
        return "OpenAI API 키가 설정되지 않아 응답을 생성할 수 없습니다."
    
    formatted_results = format_results_for_llm(search_results)
    
    try:
        completion = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "투자 전략과 암호화폐 거래에 관한 질문에 주어진 소스를 기반으로 정확하고 간결하게 답변해주세요."
                },
                {
                    "role": "user",
                    "content": f"소스: {formatted_results}\n\n질문: '{query}'"
                }
            ],
        )
        
        return completion.choices[0].message.content
    except Exception as e:
        print(f"응답 생성 오류: {str(e)}")
        return f"응답 생성 중 오류가 발생했습니다: {str(e)}"