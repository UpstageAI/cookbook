import streamlit as st
from util.cache_utils import clear_all_caches

def refresh_button(label="Refresh", key=None):
    """
    Provides a refresh button component that clears cache and restarts the app.
    
    Args:
        label: Text to display on the button
        key: Unique key for the button
        
    Returns:
        Whether the button was clicked
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

def loading_spinner(loading_text="Loading data..."):
    """
    Provides a spinner component to display while loading data.
    
    Args:
        loading_text: Text to display with the spinner
    
    Returns:
        spinner context manager
    """
    return st.spinner(loading_text)

def create_pagination(items, items_per_page=10, key_prefix="pagination"):
    """
    Provides pagination functionality for a list of items.
    
    Args:
        items: List of items to paginate
        items_per_page: Number of items to display per page
        key_prefix: Unique key prefix for pagination components
        
    Returns:
        List of items to display on the current page
    """
    # Initialize pagination state
    page_key = f"{key_prefix}_page"
    if page_key not in st.session_state:
        st.session_state[page_key] = 0
        
    # Calculate total number of pages
    total_items = len(items)
    total_pages = (total_items + items_per_page - 1) // items_per_page
    
    if total_pages <= 0:
        total_pages = 1
        
    # Check if current page is valid
    if st.session_state[page_key] >= total_pages:
        st.session_state[page_key] = total_pages - 1
    
    # Calculate items for the current page
    start_idx = st.session_state[page_key] * items_per_page
    end_idx = min(start_idx + items_per_page, total_items)
    current_items = items[start_idx:end_idx]
    
    # Render pagination controls
    if total_pages > 1:
        cols = st.columns([1, 3, 1])
        
        with cols[0]:
            if st.button("◀️ Previous", key=f"{key_prefix}_prev", 
                       disabled=st.session_state[page_key] <= 0):
                st.session_state[page_key] -= 1
                st.rerun()
                
        with cols[1]:
            st.markdown(f"<div style='text-align:center; margin-top:8px;'>{st.session_state[page_key] + 1} / {total_pages}</div>", 
                      unsafe_allow_html=True)
            
        with cols[2]:
            if st.button("Next ▶️", key=f"{key_prefix}_next", 
                       disabled=st.session_state[page_key] >= total_pages - 1):
                st.session_state[page_key] += 1
                st.rerun()
    
    return current_items

def status_indicator(status, custom_css=None):
    """
    Creates a status indicator icon.
    
    Args:
        status: One of 'success', 'warning', 'error'
        custom_css: Additional CSS style string
        
    Returns:
        HTML markup string
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
    Creates a filtering dropdown for a list of items.
    
    Args:
        items: List of items to display in the dropdown
        label: Dropdown label
        key: Unique key for the component
        default_all: Whether to include an 'All' option by default
        
    Returns:
        Selected item
    """
    options = list(items)
    if default_all:
        options = ["All"] + options
        
    return st.selectbox(label, options, key=key) 