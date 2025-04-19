from fastapi import APIRouter, UploadFile, File, HTTPException
from utils.llm import chat_with_solar, chat_with_context
from utils.parse import parse_pdf
from utils.embedding import embed_text
from utils.retrieve import retrieve_similar_chunks
from langchain_core.documents import Document
import os
import tempfile
import pickle

policy_router = APIRouter()

@policy_router.post("/upload-policy", tags=["Policy"])
async def upload_company_policy(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported for policy.")

    # Create a temporary file to store the uploaded PDF
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
        content = await file.read()
        temp_file.write(content)
        temp_file_path = temp_file.name

    try:
        # Parse the PDF to extract text
        policy_text = parse_pdf(temp_file_path)
        
        # Save the extracted text to a file for reference
        policy_path = "data/company_policy.txt"
        with open(policy_path, "w", encoding="utf-8") as f:
            f.write(policy_text)

        # LLM Prompt
        prompt = (
            "Based on the internal policy document below, create a list of specific, testable conditions "
            "that a contract must meet to be compliant. Format your response ONLY as a bullet-point list "
            "starting each line with '- '. Do not include any other text or explanations.\n\n"
            f"{policy_text}"
        )

        # Get the checklist from the LLM
        checklist_text = chat_with_solar(prompt)
        
        # Process the checklist to ensure it's a proper list
        # Split by newlines and filter out empty lines
        checklist_items = [item.strip() for item in checklist_text.split('\n') if item.strip()]
        
        # Remove bullet points or numbering if present
        checklist_items = [item.lstrip('•-*0123456789. ') for item in checklist_items]
        
        # Save the checklist to a file
        checklist_path = "data/policy_checklist.txt"
        with open(checklist_path, "w", encoding="utf-8") as f:
            for item in checklist_items:
                f.write(f"- {item}\n")
        
        return {
            "status": "success",
            "checklist": checklist_items,
            "message": f"Checklist saved to {checklist_path}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process policy: {str(e)}")
    finally:
        # Clean up the temporary file
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)

@policy_router.post("/compare-policy", tags=["Policy"])
async def compare_policy():
    """
    Compare the latest document against the internal policy checklist.
    This endpoint will:
    1. Read the latest document from /data/latest_document.txt
    2. Embed it and store in a separate pickle file
    3. Read the policy checklist from /data/policy_checklist.txt
    4. For each checklist item, use RAG to check if it's satisfied in the document
    5. Return a formatted checklist with checks/crosses for satisfied/unsatisfied conditions
    """
    try:
        # Check if the latest document exists
        latest_doc_path = "data/latest_document.txt"
        if not os.path.exists(latest_doc_path):
            raise HTTPException(status_code=404, detail="Latest document not found. Please upload a document first.")
        
        # Check if the policy checklist exists
        checklist_path = "data/policy_checklist.txt"
        if not os.path.exists(checklist_path):
            raise HTTPException(status_code=404, detail="Policy checklist not found. Please upload a policy first.")
        
        # Read the latest document
        with open(latest_doc_path, "r", encoding="utf-8") as f:
            document_text = f.read()
        
        # Read the policy checklist
        with open(checklist_path, "r", encoding="utf-8") as f:
            checklist_lines = f.readlines()
        
        # Process checklist items (remove bullet points and empty lines)
        checklist_items = [line.strip().lstrip('- ') for line in checklist_lines if line.strip()]
        
        # Embed the document and store in a separate pickle file
        doc_chunks = [document_text[i:i+1000] for i in range(0, len(document_text), 1000)]
        doc_documents = [Document(page_content=chunk) for chunk in doc_chunks]
        embed_text(doc_documents, embedding_store_path="vector_store/latest_document.pkl")
        
        # For each checklist item, check if it's satisfied in the document
        results = []
        for item in checklist_items:
            # Create a query from the checklist item
            query = f"Does the document satisfy this condition: {item}? Answer with 'Yes' or 'No' and explain why."
            
            # Get the query embedding
            query_doc = Document(page_content=query)
            query_embedding = embed_text([query_doc], is_query=True)
            
            # Retrieve similar chunks from the document
            similar_chunks = retrieve_similar_chunks(query_embedding, embedding_store_path="vector_store/latest_document.pkl")
            
            # Use the LLM to determine if the condition is satisfied
            response = chat_with_context(query, similar_chunks)
            
            # Determine if the condition is satisfied based on the response
            is_satisfied = "yes" in response.lower()[:10]  # Simple heuristic, can be improved
            
            # Add to results
            results.append({
                "condition": item,
                "satisfied": is_satisfied,
                "explanation": response
            })
        
        # Format the results for the chat
        formatted_results = "Here's how the document compares to our internal policy:\n\n"
        for result in results:
            status = "✅" if result["satisfied"] else "❌"
            formatted_results += f"{status} {result['condition']}\n"
            formatted_results += f"   Explanation: {result['explanation']}\n\n"
        
        return {
            "status": "success",
            "results": results,
            "formatted_results": formatted_results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to compare policy: {str(e)}")
