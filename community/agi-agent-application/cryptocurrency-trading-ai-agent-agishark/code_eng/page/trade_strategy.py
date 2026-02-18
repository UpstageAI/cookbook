import streamlit as st
import os
import fitz  # PyMuPDF
from PIL import Image
import io
import base64
from tools.rag.document_processor import process_uploaded_file
from tools.rag.rag import delete_from_vector_store, async_process

def get_pdf_display(pdf_path):
    """Convert the first page of a PDF file to an image"""
    try:
        doc = fitz.open(pdf_path)
        first_page = doc[0]
        zoom = 2  # Increase resolution by 2x
        mat = fitz.Matrix(zoom, zoom)
        pix = first_page.get_pixmap(matrix=mat)
        img_data = pix.tobytes("png")
        return img_data
    except Exception as e:
        st.error(f"Error occurred during PDF conversion: {str(e)}")
        return None

def get_pdf_download_link(pdf_path):
    """Generate download link for PDF file"""
    with open(pdf_path, "rb") as file:
        pdf_bytes = file.read()
    b64 = base64.b64encode(pdf_bytes).decode()
    return f'<a href="data:application/pdf;base64,{b64}" download="{os.path.basename(pdf_path)}">Download</a>'

def delete_pdf(file_path, storage_dir):
    """Delete PDF file"""
    try:
        file_name = os.path.basename(file_path)
        
        # Delete file
        os.remove(file_path)
        
        # Save deletion status in session state
        if 'deleted_files' not in st.session_state:
            st.session_state.deleted_files = set()
        st.session_state.deleted_files.add(f"{storage_dir}_{file_name}")
        
        # If RAG storage, also delete from vector store
        if storage_dir == "tools/web2pdf/rag_doc_storage" and 'vector_store_id' in st.session_state:
            # Delete from vector store
            async_process(delete_from_vector_store, file_name)
            print(f"Started request to delete '{file_name}' from vector store")
        
        return True
    except Exception as e:
        st.error(f"Error occurred while deleting file: {str(e)}")
        return False

def display_pdf_section(title, storage_dir):
    """Display PDF section"""
    st.subheader(title)
    
    # File upload
    uploaded_file = st.file_uploader(f"Upload PDF file ({title})", type="pdf", key=f"uploader_{storage_dir}")
    if uploaded_file is not None:
        try:
            file_path = os.path.join(storage_dir, uploaded_file.name)
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getvalue())
                
            # If RAG document storage, process document automatically
            if storage_dir == "tools/web2pdf/rag_doc_storage":
                # Check OpenAI API key
                if not st.session_state.get('openai_key'):
                    st.error("OpenAI API key is not set. Please enter your key in the API Settings tab.")
                else:
                    # Start async processing
                    process_uploaded_file(file_path, uploaded_file.name)
                    message = "Upload complete. The document is being automatically added to the RAG system."
                    if not st.session_state.get('upstage_api_key'):
                        message += " (Direct upload without Upstage parsing)"
                    st.success(message)
            else:
                st.success(f"File '{uploaded_file.name}' has been uploaded.")
        except Exception as e:
            st.error(f"Error occurred during file upload: {str(e)}")
    
    # Display PDF file list
    pdf_files = [f for f in os.listdir(storage_dir) if f.endswith('.pdf')]
    
    if not pdf_files:
        st.info("No PDF files are stored. Please upload a file.")
        return
    
    # Display PDF files
    for idx, pdf_file in enumerate(pdf_files):
        pdf_path = os.path.join(storage_dir, pdf_file)
        file_key = f"{storage_dir}_{pdf_file}"
        
        # Skip deleted files
        if 'deleted_files' in st.session_state and file_key in st.session_state.deleted_files:
            continue
        
        # Display PDF preview image
        pdf_image = get_pdf_display(pdf_path)
        if pdf_image:
            st.image(pdf_image, use_container_width=True)
            st.caption(pdf_file)
            
            # Arrange buttons horizontally
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(get_pdf_download_link(pdf_path), unsafe_allow_html=True)
            with col2:
                if st.button(f"Delete", key=f"delete_{file_key}"):
                    if delete_pdf(pdf_path, storage_dir):
                        st.rerun()

def show_trade_strategy():
    st.title("✨ AI Investment Strategy")
    
    # Set storage directories
    pdf_storage = "tools/web2pdf/always_see_doc_storage"
    rag_storage = "tools/web2pdf/rag_doc_storage"
    os.makedirs(pdf_storage, exist_ok=True)
    os.makedirs(rag_storage, exist_ok=True)
    
    # Check API key status and display warning
    if not st.session_state.get('openai_key'):
        st.warning("OpenAI API key is not set. To use the RAG document processing feature, please enter your key in the API Settings tab.")
    
    # Split into two columns
    col1, col2 = st.columns(2)
    
    # Left column: Always reference documents
    with col1:
        display_pdf_section("Always Reference Documents", pdf_storage)
    
    # Right column: RAG documents
    with col2:
        display_pdf_section("RAG Documents", rag_storage)
