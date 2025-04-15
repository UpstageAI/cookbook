from page.api_setting import init_api_session_state
from tools.rag.rag import create_vector_store, update_global_cache
from tools.rag.document_processor import process_all_rag_documents, update_upstage_api_key
from tools.document_parser.document_parser import update_upstage_api_key as update_parser_api_key

import streamlit as st


def init_app():
    # Initialize API session state (load saved keys)
    init_api_session_state()
    
    # Initialize chat history
    if 'messages' not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "Hello! How can I help you with your investment today?"}]
    
    # Initialize global cache variables
    update_global_cache()
    update_upstage_api_key()
    update_parser_api_key()
    
    # Check API key status
    if not st.session_state.get('upstage_api_key'):
        print("Upstage API key is not set. Document processing features will be disabled.")
    
    if not st.session_state.get('openai_key'):
        print("OpenAI API key is not set. Vector store and LLM features will be disabled.")
        return

    # Initialize RAG vector store
    vector_store_id = create_vector_store()
    
    if vector_store_id:
        print(f"Vector store initialization complete: {vector_store_id}")
        # Update global cache variables again (including vector store ID)
        update_global_cache()
        # Process all documents in the RAG repository
        process_all_rag_documents()
    else:
        print("Vector store initialization failed. RAG features will be disabled.")