import os
import streamlit as st
from openai import OpenAI
import asyncio
import threading
import json
from typing import List, Dict, Any, Optional

# File path to store Vector Store ID
VECTOR_STORE_ID_FILE = "data/vector_store_id.json"

# Global cache variables
_OPENAI_API_KEY = None
_VECTOR_STORE_ID = None

def update_global_cache():
    """Update global cache variables"""
    global _OPENAI_API_KEY, _VECTOR_STORE_ID
    
    # Update API key
    _OPENAI_API_KEY = st.session_state.get('openai_key', '')
    
    # Update vector store ID
    _VECTOR_STORE_ID = st.session_state.get('vector_store_id', '')
    
    print(f"Global cache variables updated - API key: {'set' if _OPENAI_API_KEY else 'none'}, Vector store ID: {_VECTOR_STORE_ID or 'none'}")

def get_openai_client():
    """Get OpenAI client"""
    global _OPENAI_API_KEY
    
    # API key priority: global cache > session state
    api_key = _OPENAI_API_KEY or st.session_state.get('openai_key', '')
    
    if not api_key:
        print("OpenAI API key is not set.")
        return None
    
    try:
        client = OpenAI(api_key=api_key)
        return client
    except Exception as e:
        print(f"OpenAI client initialization error: {str(e)}")
        return None

def save_vector_store_id(vector_store_id: str) -> bool:
    """Save vector store ID to file"""
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(VECTOR_STORE_ID_FILE), exist_ok=True)
        
        with open(VECTOR_STORE_ID_FILE, 'w') as f:
            json.dump({'vector_store_id': vector_store_id}, f, indent=2)
        
        print(f"Vector store ID '{vector_store_id}' saved to file.")
        return True
    except Exception as e:
        print(f"Error saving vector store ID: {str(e)}")
        return False

def load_vector_store_id() -> Optional[str]:
    """Load vector store ID from file"""
    try:
        if os.path.exists(VECTOR_STORE_ID_FILE):
            with open(VECTOR_STORE_ID_FILE, 'r') as f:
                data = json.load(f)
                vector_store_id = data.get('vector_store_id')
                if vector_store_id:
                    print(f"Vector store ID '{vector_store_id}' loaded from file.")
                    return vector_store_id
    except Exception as e:
        print(f"Error loading vector store ID: {str(e)}")
    
    return None

def create_vector_store() -> Optional[str]:
    """Create vector store - called once at app startup"""
    # Check if vector store ID already exists in session
    if 'vector_store_id' in st.session_state:
        print(f"Using vector store from session: {st.session_state.vector_store_id}")
        return st.session_state.vector_store_id
    
    # Try to load vector store ID from file
    stored_id = load_vector_store_id()
    if stored_id:
        st.session_state.vector_store_id = stored_id
        return stored_id
    
    # Check OpenAI API key
    if not st.session_state.openai_key:
        print("OpenAI API key is not set, cannot create vector store.")
        return None
    
    # Get OpenAI client
    client = get_openai_client()
    if not client:
        return None
    
    try:
        # Create vector store
        vector_store = client.vector_stores.create(
            name="AI Trading Agent"
        )
        
        # Save to session
        vector_store_id = vector_store.id
        st.session_state.vector_store_id = vector_store_id
        
        # Save to file
        save_vector_store_id(vector_store_id)
        
        print(f"New vector store created: {vector_store_id}")
        return vector_store_id
    except Exception as e:
        print(f"Error creating vector store: {str(e)}")
        return None

def upload_to_vector_store(text_content: str, file_name: str, attributes: Dict = None, 
                          openai_api_key=None, vector_store_id=None) -> bool:
    # Use provided vector_store_id before accessing session_state
    if vector_store_id is None:
        if 'vector_store_id' not in st.session_state:
            print("Vector store is not initialized.")
            return False
        vector_store_id = st.session_state.vector_store_id
    
    client = get_openai_client()
    if not client:
        return False
    
    try:
        # Create temporary file
        temp_file_path = f"temp_{file_name}.txt"
        with open(temp_file_path, "w", encoding="utf-8") as f:
            f.write(text_content)
        
        # Upload file
        with open(temp_file_path, "rb") as f:
            print(f"Starting upload of file '{file_name}' to vector store...")
            upload_result = client.vector_stores.files.upload_and_poll(
                vector_store_id=vector_store_id,
                file=f,
                attributes=attributes or {}
            )
        
        # Delete temporary file
        os.remove(temp_file_path)
        print(f"File '{file_name}' upload completed: {upload_result.id}")
        return True
    except Exception as e:
        print(f"Vector store upload error: {str(e)}")
        return False

def upload_file_to_vector_store(file_path: str, file_name: str, attributes: Dict = None, 
                               openai_api_key=None, vector_store_id=None) -> tuple:
    """Directly upload file to vector store"""
    global _VECTOR_STORE_ID
    
    actual_vector_store_id = vector_store_id or _VECTOR_STORE_ID
    
    print(f"Running upload_file_to_vector_store: ID={actual_vector_store_id}, file={file_name}")
    
    if not actual_vector_store_id:
        try:
            if 'vector_store_id' in st.session_state:
                actual_vector_store_id = st.session_state.vector_store_id
                print(f"Retrieved vector_store_id from session: {actual_vector_store_id}")
            else:
                return False, "Could not find vector store ID"
        except Exception as e:
            print(f"Session state access error: {str(e)}")
            return False, f"Session state access error: {str(e)}"
    
    client = get_openai_client()
    if not client:
        return False, "Could not initialize OpenAI client"
    
    try:
        # Direct file upload - removed 'attributes' argument
        with open(file_path, "rb") as f:
            print(f"Starting direct upload of file '{file_name}' to vector store ({actual_vector_store_id})...")
            # First upload the file
            file_upload = client.vector_stores.files.upload(
                vector_store_id=actual_vector_store_id,
                file=f
            )
            
            # Attributes can be set separately if needed
            # If attributes exist, they can be set in file metadata later
            
            # Check upload status
            file_status = client.vector_stores.files.retrieve(
                vector_store_id=actual_vector_store_id,
                file_id=file_upload.id
            )
        
        print(f"Direct upload of file '{file_name}' completed: {file_upload.id}")
        return True, None
    except Exception as e:
        error_msg = f"Direct vector store upload error: {str(e)}"
        print(error_msg)
        return False, error_msg

def search_vector_store(query: str, max_results: int = 5) -> List[Dict]:
    """Perform search in vector store"""
    if 'vector_store_id' not in st.session_state:
        print("Vector store is not initialized.")
        return []
    
    client = get_openai_client()
    if not client:
        return []
    
    vector_store_id = st.session_state.vector_store_id
    
    try:
        results = client.vector_stores.search(
            vector_store_id=vector_store_id,
            query=query,
            max_num_results=max_results,
            rewrite_query=True
        )
        
        # Format results
        formatted_results = []
        for result in results.data:
            content_text = '\n'.join([c.text for c in result.content])
            formatted_results.append({
                'file_id': result.file_id,
                'filename': result.filename,
                'score': result.score,
                'content': content_text
            })
        
        return formatted_results
    except Exception as e:
        print(f"Vector store search error: {str(e)}")
        return []

def delete_from_vector_store(file_name: str) -> bool:
    """Delete file from vector store by file name"""
    if 'vector_store_id' not in st.session_state:
        print("Vector store is not initialized.")
        return False
    
    client = get_openai_client()
    if not client:
        return False
    
    vector_store_id = st.session_state.vector_store_id
    
    try:
        # Get file list from vector store
        files = client.vector_stores.files.list(
            vector_store_id=vector_store_id
        )
        
        # Find file by name
        target_file = None
        for file in files.data:
            # Check file name in file attributes
            attributes = client.vector_stores.files.retrieve(
                vector_store_id=vector_store_id,
                file_id=file.id
            ).attributes
            
            if attributes and attributes.get('file_name') == file_name:
                target_file = file
                break
        
        if not target_file:
            print(f"Could not find file '{file_name}' in vector store.")
            return False
        
        # Delete file
        client.vector_stores.files.delete(
            vector_store_id=vector_store_id,
            file_id=target_file.id
        )
        
        print(f"File '{file_name}' deleted from vector store")
        return True
    except Exception as e:
        print(f"Error deleting file from vector store: {str(e)}")
        return False

def async_process(func, *args, **kwargs):
    """Helper function to run a function asynchronously"""
    def run_in_thread(func, *args, **kwargs):
        result = func(*args, **kwargs)
        return result
    
    thread = threading.Thread(target=run_in_thread, args=(func, *args), kwargs=kwargs)
    thread.daemon = True
    thread.start()
    return thread

def format_results_for_llm(search_results: List[Dict]) -> str:
    """Format search results for LLM"""
    if not search_results:
        return "No search results found."
    
    formatted_text = "<sources>\n"
    for result in search_results:
        formatted_text += f"<result file_name='{result['filename']}' score='{result['score']:.2f}'>\n"
        formatted_text += f"<content>{result['content']}</content>\n"
        formatted_text += "</result>\n"
    formatted_text += "</sources>"
    
    return formatted_text

def synthesize_response(query: str, search_results: List[Dict]) -> str:
    """Generate response based on search results"""
    client = get_openai_client()
    if not client:
        return "Cannot generate response because OpenAI API key is not set."
    
    formatted_results = format_results_for_llm(search_results)
    
    try:
        completion = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "Please answer questions about investment strategies and cryptocurrency trading accurately and concisely based on the provided sources."
                },
                {
                    "role": "user",
                    "content": f"Source: {formatted_results}\n\nQuestion: '{query}'"
                }
            ],
        )
        
        return completion.choices[0].message.content
    except Exception as e:
        print(f"Error generating response: {str(e)}")
        return f"An error occurred while generating response: {str(e)}"