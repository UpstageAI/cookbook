import streamlit as st
import pyupbit
from typing import Optional, List, Dict
import time
from datetime import datetime
import os
import tweepy
import json
import sys
from UPBIT import Trade

# API key storage file path
API_KEY_STORE_FILE = "data/api_key_store.json"
sys.path.append("tools/upbit")

def test_upbit_api(access_key: str, secret_key: str) -> bool:
    """Test Upbit API keys"""
    try:
        upbit = pyupbit.Upbit(access_key, secret_key)
        # Simple API call test
        balance = upbit.get_balance("KRW")
        if balance is not None:
            st.success("Upbit API connection successful!")
            return True
        else:
            st.error("Upbit API connection failed: Balance retrieval failed")
            return False
    except Exception as e:
        st.error(f"Upbit API connection failed: {e}")
        return False

def load_api_keys() -> Dict:
    """Load saved API keys from file"""
    if not os.path.exists(API_KEY_STORE_FILE):
        return {}
    
    try:
        with open(API_KEY_STORE_FILE, 'r') as f:
            api_keys = json.load(f)
        print("API keys loaded from file.")
        return api_keys
    except Exception as e:
        print(f"API key loading error: {str(e)}")
        return {}

def save_api_keys_to_file(api_keys: Dict) -> bool:
    """Save API keys to file"""
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(API_KEY_STORE_FILE), exist_ok=True)
        
        with open(API_KEY_STORE_FILE, 'w') as f:
            json.dump(api_keys, f, indent=2)
        
        print("API keys saved to file.")
        return True
    except Exception as e:
        print(f"API key saving error: {str(e)}")
        return False

def init_api_session_state():
    """Initialize API key related session state"""
    # Load API keys from file
    stored_keys = load_api_keys()
    
    # Initialize session state and apply stored keys
    if 'openai_key' not in st.session_state:
        st.session_state.openai_key = stored_keys.get('openai_key', "")
    if 'upbit_access_key' not in st.session_state:
        st.session_state.upbit_access_key = stored_keys.get('upbit_access_key', "")
    if 'upbit_secret_key' not in st.session_state:
        st.session_state.upbit_secret_key = stored_keys.get('upbit_secret_key', "")
    if 'upstage_api_key' not in st.session_state:
        st.session_state.upstage_api_key = stored_keys.get('upstage_api_key', "")
    if 'X_bearer_token' not in st.session_state:
        st.session_state.X_bearer_token = stored_keys.get('X_bearer_token', "")
    # Also save X_bearer_token as twitter_bearer_token (for search_X class compatibility)
    if 'twitter_bearer_token' not in st.session_state:
        st.session_state.twitter_bearer_token = stored_keys.get('X_bearer_token', "")
    # Add flag to track if API warning has already been shown
    if 'api_warning_shown' not in st.session_state:
        st.session_state.api_warning_shown = False

def check_api_keys():
    """Check if API keys are set and display warning message if needed"""
    has_keys = st.session_state.upbit_access_key and st.session_state.upbit_secret_key
    
    # Display warning message if API keys are not set (only once)
    if not has_keys and not st.session_state.api_warning_shown:
        # Show only small warning icon in sidebar
        if hasattr(st.sidebar, 'current_key') and st.sidebar.current_key != "":
            st.sidebar.warning("API keys not set")
        else:
            # Show detailed guidance on the actual page
            with st.container():
                st.warning("Upbit API keys are not set. Please enter your keys in the API Settings tab.")
                st.info("Currently running in demo mode. Sample data is being displayed.")
        
        # Set warning message display flag
        st.session_state.api_warning_shown = True
    
    return has_keys

def reset_api_warning():
    """Reset API warning message when changing tabs (display once per tab)"""
    st.session_state.api_warning_shown = False

def save_api_keys(openai_key, upbit_access_key, upbit_secret_key, upstage_api_key, X_bearer_token):
    """Save API keys to session state and file"""
    # Compare existing API keys with new ones
    api_changed = (st.session_state.upbit_access_key != upbit_access_key or 
                  st.session_state.upbit_secret_key != upbit_secret_key)
    
    # Save to session state
    st.session_state.openai_key = openai_key
    st.session_state.upbit_access_key = upbit_access_key
    st.session_state.upbit_secret_key = upbit_secret_key
    st.session_state.upstage_api_key = upstage_api_key
    st.session_state.X_bearer_token = X_bearer_token
    # Also save X_bearer_token as twitter_bearer_token (for search_X class compatibility)
    st.session_state.twitter_bearer_token = X_bearer_token
    
    # Save to file
    api_keys = {
        'openai_key': openai_key,
        'upbit_access_key': upbit_access_key,
        'upbit_secret_key': upbit_secret_key,
        'upstage_api_key': upstage_api_key,
        'X_bearer_token': X_bearer_token
    }
    
    save_success = save_api_keys_to_file(api_keys)
    # Set cache reset flag if API keys have changed
    if api_changed and upbit_access_key and upbit_secret_key:
        st.session_state.refresh_data = True
    
    if save_success:
        st.success("API keys have been saved!")
    else:
        st.warning("API keys were saved to the session but failed to save to file.")

def get_upbit_instance():
    """Create pyupbit instance"""
    try:
        access_key = st.session_state.get("upbit_access_key")
        secret_key = st.session_state.get("upbit_secret_key")
        if not access_key or not secret_key:
            return None
        return pyupbit.Upbit(access_key, secret_key)
    except Exception as e:
        st.error(f"Error creating Upbit instance: {str(e)}")
        return None

def get_upbit_trade_instance():
    """Create UPBIT.Trade class instance"""
    try:
        access_key = st.session_state.get("upbit_access_key")
        secret_key = st.session_state.get("upbit_secret_key")
        if not access_key or not secret_key:
            return None
        return Trade(access_key, secret_key)
    except Exception as e:
        st.error(f"Error creating Upbit Trade instance: {str(e)}")
        return None

def show_api_settings():
    
    st.title("🔑 API Settings")
    
    # Show warning if required API keys are not set
    if not st.session_state.upstage_api_key:
        st.warning("⚠️ Upstage API key is not set. Please enter the key to use document processing features.")
    
    if not st.session_state.openai_key:
        st.warning("⚠️ OpenAI API key is not set. Please enter the key to use RAG and LLM features.")
    
    st.header("upstage")
    upstage_api_key = st.text_input("upstage API Key (required)", value=st.session_state.upstage_api_key, type="password")
    st.divider()

    st.header("LLM")
    openai_key = st.text_input("OpenAI API Key (required)", value=st.session_state.openai_key, type="password")
    st.divider()

    st.header("Upbit")
    upbit_access_key = st.text_input("Upbit Access API Key (required)", value=st.session_state.upbit_access_key, type="password")
    upbit_secret_key = st.text_input("Upbit Secret API Key (required)", value=st.session_state.upbit_secret_key, type="password")
    st.divider()

    st.header("X")
    X_bearer_token = st.text_input("X bearer Token Key (optional)", value=st.session_state.X_bearer_token, type="password")

    if st.button("Save", type="primary"):
        save_api_keys(openai_key, upbit_access_key, upbit_secret_key, upstage_api_key, X_bearer_token)
        
        # Test API keys
        if upbit_access_key and upbit_secret_key:
            st.info("Testing Upbit API keys...")
            api_success = test_upbit_api(upbit_access_key, upbit_secret_key)
            
            # Clear cache immediately upon successful API connection
            if api_success:
                st.info("Refreshing all data...")
                # Clear cache
                st.cache_data.clear()
                # Show connection complete status
                st.success("API connection completed. Real data will be displayed on all pages.")
                st.balloons()  # Celebration effect
                
                # Automatically navigate to another page
                st.info("Refreshing the page to fetch real data...")
                time.sleep(2)  # Give users time to read the message
                st.session_state.selected_tab = "Portfolio"  # Navigate to Portfolio page by default
                st.rerun()