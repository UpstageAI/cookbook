import streamlit as st
import sys
sys.path.append("tools/upbit")

# 페이지 설정 최적화
st.set_page_config(
    page_title="AI 투자 채팅봇",
    page_icon="🦈",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'About': "AI 기반 암호화폐 트레이딩 봇"
    }
)


# 필요한 모듈 가져오기
from page.sidebar import show_sidebar
from page.trade_market import show_trade_market
from page.portfolio import show_portfolio
from page.trade_history import show_trade_history
from page.api_setting import show_api_settings, init_api_session_state, reset_api_warning, check_api_keys
from page.trade_strategy import show_trade_strategy
# API 연동 성공 후 모든 캐시 초기화
def refresh_all_data():
    """모든 데이터 캐시를 초기화하고 앱을 재실행합니다."""
    st.cache_data.clear()
    st.rerun()


from init import init_app

init_app()


# 사이드바 표시
with st.sidebar:
    show_sidebar()

# 탭 선택 기능 추가
if 'selected_tab' not in st.session_state:
    st.session_state.selected_tab = "API 설정"  # 기본 탭을 API 설정으로 변경

# API 키 확인
has_api_keys = check_api_keys()

# API 키가 없는 경우 강제로 API 설정 탭 표시
if not has_api_keys and st.session_state.selected_tab != "API 설정":
    st.session_state.selected_tab = "API 설정"
    st.rerun()

# 탭 버튼 생성 - API 키 설정에 따라 동적으로 표시
cols = []

# API 설정 탭은 항상 표시
if has_api_keys:
    # API 키가 있으면 모든 탭 표시
    col1, col2, col3, col4, col5 = st.columns(5)
    cols = [col1, col2, col3, col4, col5]
    
    with col1:
        if st.button("📊 거래소", use_container_width=True, 
                    type="primary" if st.session_state.selected_tab == "거래소" else "secondary"):
            st.session_state.selected_tab = "거래소"
            reset_api_warning()
            st.rerun()

    with col2:
        if st.button("✨ AI 투자 전략", use_container_width=True,
                    type="primary" if st.session_state.selected_tab == "AI 투자 전략" else "secondary"):
            st.session_state.selected_tab = "AI 투자 전략"
            reset_api_warning()
            st.rerun()
    with col3:
        if st.button("📂 포트폴리오", use_container_width=True,
                    type="primary" if st.session_state.selected_tab == "포트폴리오" else "secondary"):
            st.session_state.selected_tab = "포트폴리오"
            reset_api_warning()
            st.rerun()
    with col4:
        if st.button("📝 거래 내역", use_container_width=True,
                    type="primary" if st.session_state.selected_tab == "거래 내역" else "secondary"):
            st.session_state.selected_tab = "거래 내역"
            reset_api_warning()
            st.rerun()
    with col5:
        if st.button("🔑 API 설정", use_container_width=True,
                    type="primary" if st.session_state.selected_tab == "API 설정" else "secondary"):
            st.session_state.selected_tab = "API 설정"
            reset_api_warning()
            st.rerun()
else:
    # API 키가 없으면 API 설정 탭만 표시
    col = st.columns(1)[0]
    with col:
        st.button("🔑 API 설정", use_container_width=True, type="primary")
        st.info("API 키를 설정하면 거래소, 포트폴리오, 거래 내역 기능을 사용할 수 있습니다.")

st.markdown("---")

# 탭 내용 표시
# 선택된 탭에 따라 해당 페이지 렌더링
if st.session_state.selected_tab == "거래소":
    show_trade_market()
elif st.session_state.selected_tab == "AI 투자 전략":
    show_trade_strategy()
elif st.session_state.selected_tab == "포트폴리오":
    show_portfolio()
elif st.session_state.selected_tab == "거래 내역":
    show_trade_history()
elif st.session_state.selected_tab == "API 설정":
    show_api_settings()

# API 연동 성공 후 새로고침 수행 
if 'refresh_data' in st.session_state and st.session_state.refresh_data:
    # 새로고침 상태 초기화
    st.session_state.refresh_data = False
    # 캐시 초기화 및 앱 재실행
    refresh_all_data()

    
