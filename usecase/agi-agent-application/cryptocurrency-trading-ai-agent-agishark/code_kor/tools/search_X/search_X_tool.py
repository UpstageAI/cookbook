from tools.search_X.search_X import search_X
from agents import function_tool
from typing import Optional, Dict, List, Any

"""
Twitter/X API 검색 도구

이 도구를 사용하려면 Twitter/X API의 Bearer 토큰이 필요합니다.
토큰은 다음 단계를 통해 설정할 수 있습니다:

1. Streamlit 앱에서 API 설정 페이지로 이동
2. Twitter Bearer Token 필드에 유효한 토큰 입력
3. 저장 버튼 클릭

토큰은 st.session_state.twitter_bearer_token에 저장됩니다.

Bearer 토큰 획득 방법:
1. Twitter 개발자 계정 생성 및 로그인 (developer.twitter.com)
2. 프로젝트 및 앱 생성
3. Essential Access 레벨 획득
4. 프로젝트 설정에서 Bearer Token 복사
"""

@function_tool
def search_x_tool(keywords: str, max_results: int) -> Dict[str, Any]:
    """
    X(Twitter)에서 특정 키워드를 검색하여 최신 트윗을 가져옵니다.
    암호화폐 시장 동향, 관련 뉴스, 트레이더들의 의견 등을 파악하는 데 유용합니다.
    
    Args:
        keywords: 검색할 키워드 (예: "bitcoin price", "ethereum news", "crypto market")
        max_results: 가져올 최대 트윗 수 (기본값: 10)
    
    Returns:
        Dict: 검색 결과를 담은 딕셔너리. 다음과 같은 구조를 가집니다:
            - success (bool): 검색 성공 여부
            - data (List): 성공 시, 트윗 목록
            - query (str): 성공 시, 사용된 검색 쿼리
            - timestamp (str): 성공 시, 검색 시간
            - error (str): 실패 시, 오류 메시지
    """
    import traceback
    
    try:
        print(f"search_x_tool 호출: keywords='{keywords}', max_results={max_results}")
        
        # max_results 기본값 적용
        if max_results is None or max_results <= 0:
            print(f"유효하지 않은 max_results 값({max_results}), 기본값 10으로 설정")
            max_results = 10
            
        # 최대값 제한 (Twitter API 제한)
        if max_results > 100:
            print(f"max_results가 너무 큼({max_results}), 100으로 제한")
            max_results = 100
        
        # search_X 클래스 인스턴스 생성
        x_searcher = search_X()
        
        # 검색 실행
        result = x_searcher.search(keywords, max_results)
        
        # 결과 로깅
        if result['success']:
            print(f"search_x_tool 성공: {len(result.get('data', []))}개 결과")
        else:
            print(f"search_x_tool 실패: {result.get('error', '알 수 없는 오류')}")
            
        return result
        
    except Exception as e:
        error_detail = traceback.format_exc()
        print(f"search_x_tool 예외 발생: {str(e)}\n{error_detail}")
        return {
            'success': False,
            'error': f"search_x_tool 예외: {str(e)}"
        } 