import functools
import time
import threading
import streamlit as st

# Cache clearing functionality - used to initialize the entire app cache
def clear_all_caches():
    """Clears all caches. Can be used to connect to a refresh button."""
    st.cache_data.clear()
    if hasattr(st, 'session_state') and 'cache_timestamps' in st.session_state:
        st.session_state.cache_timestamps = {}

# TTL cache decorator - performance optimization
def ttl_cache(ttl=60):
    """
    Cache decorator with a specified TTL (Time To Live).
    
    Args:
        ttl: Lifetime of the cache item (seconds)
        
    Returns:
        Cached function or newly calculated value
    """
    def decorator(func):
        # Initialize cache timestamps
        if 'cache_timestamps' not in st.session_state:
            st.session_state.cache_timestamps = {}
            
        cache_key = func.__name__
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key (function name + arguments)
            key = f"{cache_key}:{str(args)}:{str(kwargs)}"
            current_time = time.time()
            
            # Check timestamp stored in cache
            timestamps = st.session_state.cache_timestamps
            if key in timestamps:
                if current_time - timestamps[key] < ttl:
                    # Return cached value if TTL has not expired
                    cache_key_session = f"cache_{key}"
                    if cache_key_session in st.session_state:
                        return st.session_state[cache_key_session]
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            st.session_state[f"cache_{key}"] = result
            timestamps[key] = current_time
            return result
        
        # Add method for forced cache invalidation
        def invalidate_cache(*args, **kwargs):
            """Force invalidation of cache for a specific function call."""
            key = f"{cache_key}:{str(args)}:{str(kwargs)}"
            if key in st.session_state.cache_timestamps:
                del st.session_state.cache_timestamps[key]
                if f"cache_{key}" in st.session_state:
                    del st.session_state[f"cache_{key}"]
        
        # Add invalidation method to wrapper function
        wrapper.invalidate_cache = invalidate_cache
        return wrapper
    
    return decorator

# Background caching decorator - improved user experience
def background_cache(ttl=300):
    """
    Decorator that caches results in the background.
    Returns existing cache immediately and fetches new data in the background.
    
    Args:
        ttl: Cache lifetime (seconds)
        
    Returns:
        Function that returns cached results
    """
    def decorator(func):
        cached_func = ttl_cache(ttl)(func)
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key
            cache_key = func.__name__
            key = f"{cache_key}:{str(args)}:{str(kwargs)}"
            cache_key_session = f"cache_{key}"
            
            # Check if background update is needed
            current_time = time.time()
            timestamps = st.session_state.get('cache_timestamps', {})
            
            # Update in background if cache exists and 80% of TTL has elapsed
            if (key in timestamps and 
                cache_key_session in st.session_state and 
                current_time - timestamps[key] > ttl * 0.8):
                
                def update_cache_background():
                    try:
                        result = func(*args, **kwargs)
                        st.session_state[cache_key_session] = result
                        st.session_state.cache_timestamps[key] = time.time()
                    except Exception as e:
                        print(f"Background cache update failed: {e}")
                
                # Start background thread
                thread = threading.Thread(target=update_cache_background)
                thread.daemon = True
                thread.start()
                
                # Return existing cached value
                return st.session_state[cache_key_session]
            
            # Execute synchronously if cache doesn't exist or TTL has expired
            return cached_func(*args, **kwargs)
        
        # Add invalidation method
        wrapper.invalidate_cache = cached_func.invalidate_cache
        return wrapper
    
    return decorator 