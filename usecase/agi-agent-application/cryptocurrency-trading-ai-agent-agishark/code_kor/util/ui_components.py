import streamlit as st
from util.cache_utils import clear_all_caches

def refresh_button(label="새로고침", key=None):
    """
    캐시를 비우고 앱을 다시 실행하는 리프레시 버튼 컴포넌트를 제공합니다.
    
    Args:
        label: 버튼에 표시할 텍스트
        key: 버튼의 고유 키
        
    Returns:
        버튼이 클릭되었는지 여부
    """
    if key is None:
        key = f"refresh_btn_{label}"
        
    col1, col2 = st.columns([1, 10])
    with col1:
        clicked = st.button("🔄", key=key)
        
    with col2:
        st.markdown(f"<p style='margin-top:8px;'>{label}</p>", unsafe_allow_html=True)
        
    if clicked:
        clear_all_caches()
        st.rerun()
        
    return clicked

def loading_spinner(loading_text="데이터를 불러오는 중..."):
    """
    데이터 로딩 중 표시할 스피너 컴포넌트를 제공합니다.
    
    Args:
        loading_text: 스피너와 함께 표시할 텍스트
    
    Returns:
        spinner 컨텍스트 매니저
    """
    return st.spinner(loading_text)

def create_pagination(items, items_per_page=10, key_prefix="pagination"):
    """
    항목 목록에 대한 페이지네이션 기능을 제공합니다.
    
    Args:
        items: 페이지네이션할 항목 리스트
        items_per_page: 페이지당 표시할 항목 수
        key_prefix: 페이지네이션 컴포넌트의 고유 키 프리픽스
        
    Returns:
        현재 페이지에 표시할 항목 목록
    """
    # 페이지네이션 상태 초기화
    page_key = f"{key_prefix}_page"
    if page_key not in st.session_state:
        st.session_state[page_key] = 0
        
    # 전체 페이지 수 계산
    total_items = len(items)
    total_pages = (total_items + items_per_page - 1) // items_per_page
    
    if total_pages <= 0:
        total_pages = 1
        
    # 현재 페이지가 유효한지 확인
    if st.session_state[page_key] >= total_pages:
        st.session_state[page_key] = total_pages - 1
    
    # 현재 페이지의 항목 계산
    start_idx = st.session_state[page_key] * items_per_page
    end_idx = min(start_idx + items_per_page, total_items)
    current_items = items[start_idx:end_idx]
    
    # 페이지네이션 컨트롤 렌더링
    if total_pages > 1:
        cols = st.columns([1, 3, 1])
        
        with cols[0]:
            if st.button("◀️ 이전", key=f"{key_prefix}_prev", 
                       disabled=st.session_state[page_key] <= 0):
                st.session_state[page_key] -= 1
                st.rerun()
                
        with cols[1]:
            st.markdown(f"<div style='text-align:center; margin-top:8px;'>{st.session_state[page_key] + 1} / {total_pages}</div>", 
                      unsafe_allow_html=True)
            
        with cols[2]:
            if st.button("다음 ▶️", key=f"{key_prefix}_next", 
                       disabled=st.session_state[page_key] >= total_pages - 1):
                st.session_state[page_key] += 1
                st.rerun()
    
    return current_items

def status_indicator(status, custom_css=None):
    """
    상태 표시 아이콘을 생성합니다.
    
    Args:
        status: 'success', 'warning', 'error' 중 하나
        custom_css: 추가적인 CSS 스타일 문자열
        
    Returns:
        HTML 마크업 문자열
    """
    colors = {
        'success': '#28a745',
        'warning': '#ffc107',
        'error': '#dc3545'
    }
    
    icons = {
        'success': '✓',
        'warning': '⚠',
        'error': '✗'
    }
    
    if status not in colors:
        status = 'warning'
        
    base_css = f"""
        display: inline-block;
        color: white;
        background-color: {colors[status]};
        border-radius: 50%;
        width: 20px;
        height: 20px;
        text-align: center;
        line-height: 20px;
        font-weight: bold;
    """
    
    css = base_css
    if custom_css:
        css += custom_css
        
    return f"<span style='{css}'>{icons[status]}</span>"

def filter_dropdown(items, label, key, default_all=True):
    """
    항목 목록에 대한 필터링 드롭다운을 생성합니다.
    
    Args:
        items: 드롭다운에 표시할 항목 목록
        label: 드롭다운 레이블
        key: 컴포넌트의 고유 키
        default_all: 기본적으로 '전체' 옵션을 포함할지 여부
        
    Returns:
        선택된 항목
    """
    options = list(items)
    if default_all:
        options = ["전체"] + options
        
    return st.selectbox(label, options, key=key) 