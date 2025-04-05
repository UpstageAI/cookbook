import streamlit as st
from typing import Dict, List, Any
from agents import function_tool, RunContextWrapper
from tools.rag.rag import search_vector_store, get_openai_client

@function_tool
async def search_rag_documents(ctx: RunContextWrapper[Any], query: str, max_results: int = None) -> str:
    """문서 데이터베이스에서 질문과 관련된 정보를 검색합니다.
    
    Args:
        query: 검색할 질문 또는 키워드
        max_results: 반환할 최대 결과 수
    
    Returns:
        검색 결과의 텍스트 내용
    """
    print(f"문서 검색 도구 호출됨: '{query}' (최대 결과: {max_results or 3}개)")
    
    # vector_store_id가 세션에 없으면 오류 반환
    if 'vector_store_id' not in st.session_state:
        error_msg = "벡터 스토어가 초기화되지 않았습니다."
        print(error_msg)
        return error_msg
    
    # OpenAI 클라이언트 확인
    client = get_openai_client()
    if not client:
        error_msg = "OpenAI API 키가 설정되지 않아 검색을 수행할 수 없습니다."
        print(error_msg)
        return error_msg
    
    try:
        # 기본값 설정 (함수 매개변수 대신 여기서 처리)
        if max_results is None:
            max_results = 3
        
        # 벡터 스토어에서 검색 수행
        results = search_vector_store(query, max_results)
        
        if not results:
            return "검색 결과가 없습니다."
        
        # 결과 포맷팅
        formatted_results = "\n\n## 검색 결과\n\n"
        for i, result in enumerate(results, 1):
            formatted_results += f"### 문서 {i}: {result['filename']} (관련도: {result['score']:.2f})\n\n"
            formatted_results += f"{result['content']}\n\n"
        
        print(f"검색 결과 {len(results)}개 반환됨")
        return formatted_results
    
    except Exception as e:
        error_msg = f"문서 검색 중 오류 발생: {str(e)}"
        print(error_msg)
        return error_msg 