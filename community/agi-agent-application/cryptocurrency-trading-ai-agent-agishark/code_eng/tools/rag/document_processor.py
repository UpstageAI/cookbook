import os
import streamlit as st
from tools.document_parser.document_parser import DocumentParser
from tools.rag.rag import upload_to_vector_store, upload_file_to_vector_store, async_process

# Global variables
_UPSTAGE_API_KEY = None

def update_upstage_api_key():
    """Update global Upstage API key"""
    global _UPSTAGE_API_KEY
    _UPSTAGE_API_KEY = st.session_state.get('upstage_api_key', '')
    print(f"Document processor - Upstage API key updated: {'set' if _UPSTAGE_API_KEY else 'none'}")

def process_file(file_path: str, file_name: str = None, vector_store_id: str = None) -> dict:
    """Process document file by parsing and uploading to vector store"""
    if file_name is None:
        file_name = os.path.basename(file_path)
    
    try:
        # Try document parsing if Upstage API key is available
        if _UPSTAGE_API_KEY:
            try:
                # Read file content
                with open(file_path, "rb") as f:
                    file_content = f.read()
                
                # Parse document (directly pass API key)
                parser = DocumentParser(api_key=_UPSTAGE_API_KEY)
                parse_result = parser.parse_document(file_content, file_name)
                
                if parse_result['success']:
                    # Output parsing results
                    print(f"File '{file_name}' Upstage parsing completed:")
                    print(f"Metadata: {parse_result['metadata']}")
                    print(f"Text content (first 100 chars): {parse_result['text'][:100]}...")
                    
                    # Upload using text content if parsing successful
                    upload_success = upload_to_vector_store(
                        text_content=parse_result['text'],
                        file_name=file_name,
                        attributes={
                            'source': 'rag_storage',
                            'file_name': file_name,
                            'original_path': file_path,
                            'parse_method': 'upstage',
                            'vector_store_id': vector_store_id
                        },
                        vector_store_id=vector_store_id
                    )
                    
                    if upload_success:
                        print(f"File '{file_name}' vector store upload successful (Upstage parsing)")
                        return {
                            'success': True,
                            'vector_store_upload': True,
                            'text': parse_result['text'][:500] + "..." if len(parse_result['text']) > 500 else parse_result['text'],
                            'metadata': parse_result['metadata']
                        }
                else:
                    print(f"Upstage parsing failed: {parse_result.get('error', 'Unknown error')}")
            except Exception as e:
                print(f"Error during Upstage parsing: {str(e)}")
        else:
            print("Upstage API key is not set, trying direct upload.")
        
        # Direct file upload if Upstage parsing fails or API key is missing
        print(f"Starting direct file upload (without Upstage parsing)")
        try:
            upload_result, error_message = upload_file_to_vector_store(
                file_path=file_path,
                file_name=file_name,
                attributes={
                    'source': 'rag_storage',
                    'file_name': file_name,
                    'original_path': file_path,
                    'parse_method': 'direct',
                    'vector_store_id': vector_store_id
                },
                vector_store_id=vector_store_id
            )
            
            if upload_result:
                print(f"File '{file_name}' direct upload to vector store successful")
                return {
                    'success': True,
                    'vector_store_upload': True,
                    'text': f"File '{file_name}' was directly uploaded to the vector store.",
                    'metadata': {
                        'file_name': file_name,
                        'parse_method': 'direct'
                    }
                }
            else:
                error_msg = f"Vector store upload failed: {error_message or 'Unknown reason'}"
                print(f"File '{file_name}' {error_msg}")
                return {
                    'success': False,
                    'error': error_msg,
                    'vector_store_upload': False
                }
        except Exception as e:
            error_msg = f"Error during vector store upload processing: {str(e)}"
            print(f"File '{file_name}' {error_msg}")
            return {
                'success': False,
                'error': error_msg,
                'vector_store_upload': False
            }
    
    except Exception as e:
        error_msg = f"File processing error: {str(e)}"
        print(f"File '{file_name}' processing error: {str(e)}")
        return {
            'success': False,
            'error': error_msg,
            'vector_store_upload': False
        }

def process_all_rag_documents():
    """Process all documents in RAG storage and upload to vector store"""
    rag_storage_path = "tools/web2pdf/rag_doc_storage"
    
    if not os.path.exists(rag_storage_path):
        print(f"RAG storage path not found: {rag_storage_path}")
        return False
    
    pdf_files = [f for f in os.listdir(rag_storage_path) if f.endswith('.pdf')]
    
    if not pdf_files:
        print("No PDF files in RAG storage.")
        return True
    
    print(f"Starting processing of {len(pdf_files)} PDF files from RAG storage")
    
    # Save necessary values before session state is initialized in other files
    from tools.rag.rag import update_global_cache
    update_global_cache()
    
    # Get vector store ID from session state
    vector_store_id = ""
    try:
        vector_store_id = st.session_state.get('vector_store_id', '')
        print(f"process_all_rag_documents: vector_store_id = {vector_store_id}")
    except Exception as e:
        print(f"Session state access error (ignored): {str(e)}")
    
    for pdf_file in pdf_files:
        file_path = os.path.join(rag_storage_path, pdf_file)
        # Process asynchronously while directly passing vector store ID
        async_process(process_file, file_path, pdf_file, vector_store_id=vector_store_id)
    
    return True

def process_uploaded_file(file_path: str, file_name: str = None):
    """Process uploaded file asynchronously"""
    # Update global cache variables
    from tools.rag.rag import update_global_cache
    from tools.document_parser.document_parser import update_upstage_api_key
    
    update_global_cache()
    update_upstage_api_key()
    update_upstage_api_key()  # Update API key in Document processor as well
    
    # Get vector store ID from session state
    vector_store_id = st.session_state.get('vector_store_id', '')
    
    # Directly pass vector store ID
    return async_process(process_file, file_path, file_name, vector_store_id=vector_store_id)