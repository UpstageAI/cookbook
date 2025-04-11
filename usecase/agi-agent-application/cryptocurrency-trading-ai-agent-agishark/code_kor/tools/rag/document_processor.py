import os
import streamlit as st
from tools.document_parser.document_parser import DocumentParser
from tools.rag.rag import upload_to_vector_store, upload_file_to_vector_store, async_process

# 전역 변수
_UPSTAGE_API_KEY = None

def update_upstage_api_key():
    """전역 Upstage API 키 업데이트"""
    global _UPSTAGE_API_KEY
    _UPSTAGE_API_KEY = st.session_state.get('upstage_api_key', '')
    print(f"Document processor - Upstage API 키 업데이트: {'설정됨' if _UPSTAGE_API_KEY else '없음'}")

def process_file(file_path: str, file_name: str = None, vector_store_id: str = None) -> dict:
    """문서 파일을 처리하여 파싱하고 벡터 스토어에 업로드"""
    if file_name is None:
        file_name = os.path.basename(file_path)
    
    try:
        # Upstage API 키가 있는 경우 문서 파싱 시도
        if _UPSTAGE_API_KEY:
            try:
                # 파일 내용 읽기
                with open(file_path, "rb") as f:
                    file_content = f.read()
                
                # 문서 파싱 (API 키 직접 전달)
                parser = DocumentParser(api_key=_UPSTAGE_API_KEY)
                parse_result = parser.parse_document(file_content, file_name)
                
                if parse_result['success']:
                    # 파싱 결과 출력
                    print(f"파일 '{file_name}' Upstage 파싱 완료:")
                    print(f"메타데이터: {parse_result['metadata']}")
                    print(f"텍스트 내용 (처음 100자): {parse_result['text'][:100]}...")
                    
                    # 파싱 성공시 텍스트 콘텐츠 사용하여 업로드
                    upload_success = upload_to_vector_store(
                        text_content=parse_result['text'],
                        file_name=file_name,
                        attributes={
                            'source': 'rag_storage',
                            'file_name': file_name,
                            'original_path': file_path,
                            'parse_method': 'upstage',
                            'vector_store_id': vector_store_id
                        },
                        vector_store_id=vector_store_id
                    )
                    
                    if upload_success:
                        print(f"파일 '{file_name}' 벡터 스토어 업로드 성공 (Upstage 파싱)")
                        return {
                            'success': True,
                            'vector_store_upload': True,
                            'text': parse_result['text'][:500] + "..." if len(parse_result['text']) > 500 else parse_result['text'],
                            'metadata': parse_result['metadata']
                        }
                else:
                    print(f"Upstage 파싱 실패: {parse_result.get('error', '알 수 없는 오류')}")
            except Exception as e:
                print(f"Upstage 파싱 중 오류 발생: {str(e)}")
        else:
            print("Upstage API 키가 설정되지 않아 직접 업로드를 시도합니다.")
        
        # Upstage 파싱 실패 또는 API 키가 없는 경우 직접 파일 업로드
        print(f"파일 직접 업로드 시작 (Upstage 파싱 없이)")
        try:
            upload_result, error_message = upload_file_to_vector_store(
                file_path=file_path,
                file_name=file_name,
                attributes={
                    'source': 'rag_storage',
                    'file_name': file_name,
                    'original_path': file_path,
                    'parse_method': 'direct',
                    'vector_store_id': vector_store_id
                },
                vector_store_id=vector_store_id
            )
            
            if upload_result:
                print(f"파일 '{file_name}' 벡터 스토어 직접 업로드 성공")
                return {
                    'success': True,
                    'vector_store_upload': True,
                    'text': f"파일 '{file_name}'이 벡터 스토어에 직접 업로드되었습니다.",
                    'metadata': {
                        'file_name': file_name,
                        'parse_method': 'direct'
                    }
                }
            else:
                error_msg = f"벡터 스토어 업로드 실패: {error_message or '알 수 없는 이유'}"
                print(f"파일 '{file_name}' {error_msg}")
                return {
                    'success': False,
                    'error': error_msg,
                    'vector_store_upload': False
                }
        except Exception as e:
            error_msg = f"벡터 스토어 업로드 처리 중 오류 발생: {str(e)}"
            print(f"파일 '{file_name}' {error_msg}")
            return {
                'success': False,
                'error': error_msg,
                'vector_store_upload': False
            }
    
    except Exception as e:
        error_msg = f"파일 처리 오류: {str(e)}"
        print(f"파일 '{file_name}' 처리 오류: {str(e)}")
        return {
            'success': False,
            'error': error_msg,
            'vector_store_upload': False
        }

def process_all_rag_documents():
    """RAG 저장소의 모든 문서를 처리하여 벡터 스토어에 업로드"""
    rag_storage_path = "tools/web2pdf/rag_doc_storage"
    
    if not os.path.exists(rag_storage_path):
        print(f"RAG 저장소 경로 없음: {rag_storage_path}")
        return False
    
    pdf_files = [f for f in os.listdir(rag_storage_path) if f.endswith('.pdf')]
    
    if not pdf_files:
        print("RAG 저장소에 PDF 파일이 없습니다.")
        return True
    
    print(f"RAG 저장소에서 {len(pdf_files)}개의 PDF 파일 처리 시작")
    
    # 다른 파일과 세션 상태가 초기화되기 전에 필요한 값을 미리 저장
    from tools.rag.rag import update_global_cache
    update_global_cache()
    
    # 세션 상태에서 벡터 스토어 ID 가져오기
    vector_store_id = ""
    try:
        vector_store_id = st.session_state.get('vector_store_id', '')
        print(f"process_all_rag_documents: vector_store_id = {vector_store_id}")
    except Exception as e:
        print(f"세션 상태 접근 오류(무시됨): {str(e)}")
    
    for pdf_file in pdf_files:
        file_path = os.path.join(rag_storage_path, pdf_file)
        # 비동기적으로 처리하면서 벡터 스토어 ID 직접 전달
        async_process(process_file, file_path, pdf_file, vector_store_id=vector_store_id)
    
    return True

def process_uploaded_file(file_path: str, file_name: str = None):
    """업로드된 파일을 비동기적으로 처리"""
    # 전역 캐시 변수 업데이트
    from tools.rag.rag import update_global_cache
    from tools.document_parser.document_parser import update_upstage_api_key
    
    update_global_cache()
    update_upstage_api_key()
    update_upstage_api_key()  # Document processor에도 API 키 업데이트
    
    # 세션 상태에서 벡터 스토어 ID 가져오기
    vector_store_id = st.session_state.get('vector_store_id', '')
    
    # 벡터 스토어 ID를 직접 전달
    return async_process(process_file, file_path, file_name, vector_store_id=vector_store_id)