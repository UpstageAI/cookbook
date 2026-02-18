import streamlit as st
from typing import Dict, List, Any
from agents import function_tool, RunContextWrapper
from tools.rag.rag import search_vector_store, get_openai_client

@function_tool
async def search_rag_documents(ctx: RunContextWrapper[Any], query: str, max_results: int = None) -> str:
    """Search for information related to the query in the document database.
    
    Args:
        query: Question or keywords to search for
        max_results: Maximum number of results to return
    
    Returns:
        Text content of search results
    """
    print(f"Document search tool called: '{query}' (max results: {max_results or 3})")
    
    # Return error if vector_store_id is not in session
    if 'vector_store_id' not in st.session_state:
        error_msg = "Vector store has not been initialized."
        print(error_msg)
        return error_msg
    
    # Check OpenAI client
    client = get_openai_client()
    if not client:
        error_msg = "OpenAI API key is not set, cannot perform search."
        print(error_msg)
        return error_msg
    
    try:
        # Set default value (handled here instead of in function parameters)
        if max_results is None:
            max_results = 3
        
        # Perform search in vector store
        results = search_vector_store(query, max_results)
        
        if not results:
            return "No search results found."
        
        # Format results
        formatted_results = "\n\n## Search Results\n\n"
        for i, result in enumerate(results, 1):
            formatted_results += f"### Document {i}: {result['filename']} (Relevance: {result['score']:.2f})\n\n"
            formatted_results += f"{result['content']}\n\n"
        
        print(f"Returned {len(results)} search results")
        return formatted_results
    
    except Exception as e:
        error_msg = f"Error occurred during document search: {str(e)}"
        print(error_msg)
        return error_msg 