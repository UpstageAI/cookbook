import functools
import time
import threading
import streamlit as st

# 캐시 비우기 기능 - 앱 전체 캐시를 초기화할 때 사용
def clear_all_caches():
    """모든 캐시를 초기화합니다. 리프레시 버튼에 연결하는 데 사용할 수 있습니다."""
    st.cache_data.clear()
    if hasattr(st, 'session_state') and 'cache_timestamps' in st.session_state:
        st.session_state.cache_timestamps = {}

# TTL 캐시 데코레이터 - 성능 최적화
def ttl_cache(ttl=60):
    """
    지정된 TTL(Time To Live)을 가진 캐시 데코레이터입니다.
    
    Args:
        ttl: 캐시 항목의 수명(초)
        
    Returns:
        캐시된 함수 또는 새로 계산된 값
    """
    def decorator(func):
        # 캐시 타임스탬프 초기화
        if 'cache_timestamps' not in st.session_state:
            st.session_state.cache_timestamps = {}
            
        cache_key = func.__name__
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 캐시 키 생성 (함수명 + 인수)
            key = f"{cache_key}:{str(args)}:{str(kwargs)}"
            current_time = time.time()
            
            # 캐시에 저장된 타임스탬프 확인
            timestamps = st.session_state.cache_timestamps
            if key in timestamps:
                if current_time - timestamps[key] < ttl:
                    # TTL이 만료되지 않았으면 캐시된 값 반환
                    cache_key_session = f"cache_{key}"
                    if cache_key_session in st.session_state:
                        return st.session_state[cache_key_session]
            
            # 함수 실행하고 결과 캐싱
            result = func(*args, **kwargs)
            st.session_state[f"cache_{key}"] = result
            timestamps[key] = current_time
            return result
        
        # 캐시 강제 무효화 메서드 추가
        def invalidate_cache(*args, **kwargs):
            """특정 함수 호출에 대한 캐시를 강제로 무효화합니다."""
            key = f"{cache_key}:{str(args)}:{str(kwargs)}"
            if key in st.session_state.cache_timestamps:
                del st.session_state.cache_timestamps[key]
                if f"cache_{key}" in st.session_state:
                    del st.session_state[f"cache_{key}"]
        
        # 래퍼 함수에 무효화 메서드 추가
        wrapper.invalidate_cache = invalidate_cache
        return wrapper
    
    return decorator

# 백그라운드 캐싱 데코레이터 - 사용자 경험 향상
def background_cache(ttl=300):
    """
    백그라운드에서 결과를 캐시하는 데코레이터입니다.
    기존 캐시가 있으면 즉시 반환하고, 백그라운드에서 새로 가져옵니다.
    
    Args:
        ttl: 캐시 수명(초)
        
    Returns:
        캐시된 결과를 반환하는 함수
    """
    def decorator(func):
        cached_func = ttl_cache(ttl)(func)
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 캐시 키 생성
            cache_key = func.__name__
            key = f"{cache_key}:{str(args)}:{str(kwargs)}"
            cache_key_session = f"cache_{key}"
            
            # 백그라운드 업데이트 필요 여부 확인
            current_time = time.time()
            timestamps = st.session_state.get('cache_timestamps', {})
            
            # 캐시가 있고 TTL의 80% 이상 경과했으면 백그라운드에서 업데이트
            if (key in timestamps and 
                cache_key_session in st.session_state and 
                current_time - timestamps[key] > ttl * 0.8):
                
                def update_cache_background():
                    try:
                        result = func(*args, **kwargs)
                        st.session_state[cache_key_session] = result
                        st.session_state.cache_timestamps[key] = time.time()
                    except Exception as e:
                        print(f"백그라운드 캐시 업데이트 실패: {e}")
                
                # 백그라운드 스레드 시작
                thread = threading.Thread(target=update_cache_background)
                thread.daemon = True
                thread.start()
                
                # 기존 캐시된 값 반환
                return st.session_state[cache_key_session]
            
            # 캐시가 없거나 TTL이 만료되었으면 동기적으로 실행
            return cached_func(*args, **kwargs)
        
        # 무효화 메서드 추가
        wrapper.invalidate_cache = cached_func.invalidate_cache
        return wrapper
    
    return decorator 