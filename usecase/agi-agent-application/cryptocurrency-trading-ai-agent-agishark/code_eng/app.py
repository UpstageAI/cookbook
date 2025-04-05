import streamlit as st
import sys
sys.path.append("tools/upbit")

# Page configuration optimization
st.set_page_config(
    page_title="AI Investment Chatbot",
    page_icon="🦈",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'About': "AI-based Cryptocurrency Trading Bot"
    }
)


# Import required modules
from page.sidebar import show_sidebar
from page.trade_market import show_trade_market
from page.portfolio import show_portfolio
from page.trade_history import show_trade_history
from page.api_setting import show_api_settings, init_api_session_state, reset_api_warning, check_api_keys
from page.trade_strategy import show_trade_strategy
# Clear all cache after API connection success
def refresh_all_data():
    """Initialize all data caches and restart the app."""
    st.cache_data.clear()
    st.rerun()


from init import init_app

init_app()


# Show sidebar
with st.sidebar:
    show_sidebar()

# Tab selection functionality
if 'selected_tab' not in st.session_state:
    st.session_state.selected_tab = "API Settings"  # Change default tab to API Settings

# Check API keys
has_api_keys = check_api_keys()

# Force display API settings tab if no API keys
if not has_api_keys and st.session_state.selected_tab != "API Settings":
    st.session_state.selected_tab = "API Settings"
    st.rerun()

# Create tab buttons - dynamically display based on API key settings
cols = []

# API Settings tab is always displayed
if has_api_keys:
    # Display all tabs if API keys exist
    col1, col2, col3, col4, col5 = st.columns(5)
    cols = [col1, col2, col3, col4, col5]
    
    with col1:
        if st.button("📊 Exchange", use_container_width=True, 
                    type="primary" if st.session_state.selected_tab == "Exchange" else "secondary"):
            st.session_state.selected_tab = "Exchange"
            reset_api_warning()
            st.rerun()

    with col2:
        if st.button("✨ AI Investment Strategy", use_container_width=True,
                    type="primary" if st.session_state.selected_tab == "AI Investment Strategy" else "secondary"):
            st.session_state.selected_tab = "AI Investment Strategy"
            reset_api_warning()
            st.rerun()
    with col3:
        if st.button("📂 Portfolio", use_container_width=True,
                    type="primary" if st.session_state.selected_tab == "Portfolio" else "secondary"):
            st.session_state.selected_tab = "Portfolio"
            reset_api_warning()
            st.rerun()
    with col4:
        if st.button("📝 Transaction History", use_container_width=True,
                    type="primary" if st.session_state.selected_tab == "Transaction History" else "secondary"):
            st.session_state.selected_tab = "Transaction History"
            reset_api_warning()
            st.rerun()
    with col5:
        if st.button("🔑 API Settings", use_container_width=True,
                    type="primary" if st.session_state.selected_tab == "API Settings" else "secondary"):
            st.session_state.selected_tab = "API Settings"
            reset_api_warning()
            st.rerun()
else:
    # Only display API Settings tab if no API keys
    col = st.columns(1)[0]
    with col:
        st.button("🔑 API Settings", use_container_width=True, type="primary")
        st.info("Set up API keys to use Exchange, Portfolio, and Transaction History features.")

st.markdown("---")

# Display tab content
# Render the corresponding page based on the selected tab
if st.session_state.selected_tab == "Exchange":
    show_trade_market()
elif st.session_state.selected_tab == "AI Investment Strategy":
    show_trade_strategy()
elif st.session_state.selected_tab == "Portfolio":
    show_portfolio()
elif st.session_state.selected_tab == "Transaction History":
    show_trade_history()
elif st.session_state.selected_tab == "API Settings":
    show_api_settings()

# Refresh after API connection success
if 'refresh_data' in st.session_state and st.session_state.refresh_data:
    # Initialize refresh state
    st.session_state.refresh_data = False
    # Clear cache and restart app
    refresh_all_data()

    
