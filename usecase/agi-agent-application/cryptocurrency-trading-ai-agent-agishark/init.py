from page.api_setting import init_api_session_state
from tools.rag.rag import create_vector_store, update_global_cache
from tools.rag.document_processor import process_all_rag_documents, update_upstage_api_key
from tools.document_parser.document_parser import update_upstage_api_key as update_parser_api_key

import streamlit as st


def init_app():
    # API 세션 상태 초기화 (저장된 키 불러오기)
    init_api_session_state()
    
    # 채팅 기록 초기화
    if 'messages' not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "안녕하세요! 투자에 관해 무엇을 도와드릴까요?"}]
    
    # 전역 캐시 변수 초기화
    update_global_cache()
    update_upstage_api_key()
    update_parser_api_key()
    
    # API 키 상태 확인
    if not st.session_state.get('upstage_api_key'):
        print("Upstage API 키가 설정되지 않았습니다. 문서 처리 기능이 비활성화됩니다.")
    
    if not st.session_state.get('openai_key'):
        print("OpenAI API 키가 설정되지 않았습니다. 벡터 스토어 및 LLM 기능이 비활성화됩니다.")
        return

    # RAG 벡터 스토어 초기화
    vector_store_id = create_vector_store()
    
    if vector_store_id:
        print(f"벡터 스토어 초기화 완료: {vector_store_id}")
        # 전역 캐시 변수 다시 업데이트 (벡터 스토어 ID 포함)
        update_global_cache()
        # RAG 저장소의 모든 문서 처리
        process_all_rag_documents()
    else:
        print("벡터 스토어 초기화 실패. RAG 기능이 비활성화됩니다.")