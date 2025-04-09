from typing import Dict, List, TypedDict, Any
from langgraph.graph import Graph, StateGraph
import numpy as np
from openai import OpenAI
import json
import os
import io  # Add this import
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from src.tools.highlight import CaseLawRetriever, DocumentParser, ToxicClauseFinder
import logging
from langchain_core.tools import tool
from pydantic import BaseModel, Field
import boto3
from botocore.config import Config
import traceback
from ..config import (
    CASE_DB_PATH,
    EMBEDDING_PATH,
    SIMULATION_PROMPT_PATH,
    FORMAT_PROMPT_PATH,
    HIGHLIGHT_PROMPT_PATH
)

BUCKET_NAME = os.environ.get('BUCKET_NAME', 'wetube-gwanwoo')
s3 = boto3.client('s3',
    aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
    region_name='ap-northeast-2',
    config=Config(signature_version='s3v4')
)

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define schema for the simulation tool
class SimulationToolSchema(BaseModel):
    query: str = Field(..., description="User query about contract dispute simulation")
    file_id: str = Field(..., description="File ID or key to retrieve the contract document from S3")

class SimulationState(TypedDict):
    query: str
    document_text: str
    toxic_clauses: List[dict]
    relevant_toxic_clauses: List[dict]  # Selected toxic clauses for simulations
    similar_cases: List[List[dict]]  # List of similar cases for each simulation
    selected_cases: List[dict]  # Selected cases for each simulation
    simulations: List[str]  # Results of each simulation
    error: str

def parse_document(state: SimulationState, document_parser: DocumentParser) -> SimulationState:
    """Parse the input PDF document"""
    try:
        # If document_text is already set, skip parsing
        if state.get("document_text"):
            logger.info("Document already parsed, skipping parse step")
            return state
            
        logger.info("Parsing document...")
        if not state.get("document_file"):
            state["error"] = "No document file provided"
            return state
            
        parse_result = document_parser.parse(state["document_file"])
        state["document_text"] = parse_result.get("content", {}).get("text", "")
        
        if not state["document_text"]:
            state["error"] = "Failed to extract text from document"
        
        return state
    except Exception as e:
        logger.error(f"Error parsing document: {e}")
        state["error"] = f"Document parsing error: {str(e)}"
        return state

def extract_toxic_clauses(state: SimulationState, llm_highlighter: ToxicClauseFinder) -> SimulationState:
    """Extract toxic clauses from the document text"""
    if state.get("error"):
        return state
        
    try:
        logger.info("Extracting toxic clauses...")
        highlight_result = llm_highlighter.find(state["document_text"])
        state["toxic_clauses"] = highlight_result
        
        if not state["toxic_clauses"]:
            state["error"] = "No toxic clauses found"
            
        return state
    except Exception as e:
        logger.error(f"Error extracting toxic clauses: {e}")
        state["error"] = f"Clause extraction error: {str(e)}"
        return state

def select_relevant_toxic_clauses(state: SimulationState, model: SentenceTransformer) -> SimulationState:
    """Select most relevant toxic clauses based on user query"""
    if state.get("error") or not state.get("toxic_clauses"):
        return state
        
    try:
        logger.info(f"Selecting relevant toxic clauses for query: {state['query']}")
        query_embedding = model.encode(state["query"])
        
        clause_similarities = []
        for clause in state["toxic_clauses"]:
            clause_text = clause.get("독소조항", "")
            if not clause_text:
                continue
                
            clause_embedding = model.encode(clause_text)
            similarity = np.dot(clause_embedding, query_embedding) / (
                np.linalg.norm(clause_embedding) * np.linalg.norm(query_embedding)
            )
            clause_similarities.append((clause, similarity))
        
        # Sort by similarity score
        clause_similarities.sort(key=lambda x: x[1], reverse=True)
        
        # Select top 2 most relevant toxic clauses for simulations
        state["relevant_toxic_clauses"] = [item[0] for item in clause_similarities[:2]]
        
        if not state["relevant_toxic_clauses"]:
            state["error"] = "Failed to find relevant toxic clauses"
            
        logger.info(f"Selected {len(state['relevant_toxic_clauses'])} relevant toxic clauses")
        return state
    except Exception as e:
        logger.error(f"Error selecting relevant toxic clauses: {e}")
        state["error"] = f"Clause selection error: {str(e)}"
        return state

def format_case(case_details: str, format_prompt: str, client: OpenAI) -> str:
    """Format case details using LLM"""
    try:
        logger.info("Formatting case details...")
        # Check if input is actually a legal case
        if not case_details or len(case_details.strip()) < 10:  # Arbitrary minimum length for valid legal text
            return "유효한 판례 정보가 필요합니다."
            
        # Check if the input appears to be a non-legal query
        if len(case_details.split()) < 5 and not any(legal_term in case_details for legal_term in ["판례", "법원", "계약", "조항"]):
            return "계약서 분석과 관련된 내용만 처리할 수 있습니다."
            
        messages = [
            {"role": "system", "content": format_prompt},
            {"role": "user", "content": case_details}
        ]
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.1
        )
        
        result = response.choices[0].message.content.strip()
        if not result:
            return "판례 분석 결과가 없습니다."
        return result
    except Exception as e:
        logger.error(f"Case formatting error: {str(e)}")
        return "판례 분석 실패"

def retrieve_cases_for_clauses(state: SimulationState, case_retriever: CaseLawRetriever, format_prompt: str, client: OpenAI) -> SimulationState:
    """Retrieve similar cases for each relevant toxic clause"""
    if state.get("error") or not state.get("relevant_toxic_clauses"):
        return state
        
    try:
        state["similar_cases"] = []
        
        # For each relevant toxic clause, find similar cases
        for toxic_clause in state["relevant_toxic_clauses"]:
            logger.info(f"Retrieving similar cases for toxic clause")
            clause_text = toxic_clause.get("독소조항", "")
            combined_query = f"{state['query']} {clause_text}"
            
            query_embedding = case_retriever.model.encode(combined_query)
            similarities = np.dot(case_retriever.case_embeddings, query_embedding) / (
                np.linalg.norm(case_retriever.case_embeddings, axis=1) * np.linalg.norm(query_embedding)
            )
            
            top_indices = np.argsort(similarities)[-10:][::-1]
            cases_for_clause = []
            
            for idx in top_indices:
                cases_for_clause.append({
                    "case": str(case_retriever.cases[idx]["value"]),
                    "similarity_score": float(similarities[idx]),
                    "index": idx,
                    "formatted_case": None  # We'll format only after selecting the best case
                })
                
            state["similar_cases"].append(cases_for_clause)
            
        logger.info(f"Retrieved similar cases for {len(state['similar_cases'])} toxic clauses")
        return state
    except Exception as e:
        logger.error(f"Error retrieving cases: {e}")
        state["error"] = f"Case retrieval error: {str(e)}"
        state["similar_cases"] = []
        return state

def select_best_cases(state: SimulationState, case_retriever: CaseLawRetriever, format_prompt: str, client: OpenAI) -> SimulationState:
    """Select the most relevant case for each set of similar cases and format them"""
    if state.get("error") or not state.get("similar_cases"):
        return state
        
    try:
        logger.info(f"Selecting best cases for query: {state['query']}")
        query_embedding = case_retriever.model.encode(state['query'])
        
        state["selected_cases"] = []
        
        for similar_cases_set in state["similar_cases"]:
            best_case = None
            highest_similarity = -1
            
            for case_data in similar_cases_set:
                case_text = str(case_data["case"])
                case_embedding = case_retriever.model.encode(case_text[:1024])
                
                similarity = np.dot(case_embedding, query_embedding) / (
                    np.linalg.norm(case_embedding) * np.linalg.norm(query_embedding)
                )
                
                if similarity > highest_similarity:
                    highest_similarity = similarity
                    best_case = case_data
            
            if best_case:
                # Format only the selected case
                formatted_case = format_case(best_case["case"], format_prompt, client)
                best_case["formatted_case"] = formatted_case
                state["selected_cases"].append(best_case)
                logger.info(f"Selected and formatted best case with similarity: {highest_similarity}")
            
        if not state["selected_cases"]:
            state["error"] = "Failed to select relevant cases"
            
        return state
    except Exception as e:
        logger.error(f"Error selecting best cases: {e}")
        state["error"] = f"Case selection error: {str(e)}"
        return state

def run_simulations(state: SimulationState, simulation_prompt: str, client: OpenAI) -> SimulationState:
    """Run dispute simulations for each toxic clause and selected case"""
    if state.get("error") or not state.get("selected_cases") or not state.get("relevant_toxic_clauses"):
        return state
        
    try:
        logger.info("Running dispute simulations...")
        state["simulations"] = []
        
        # Run a simulation for each toxic clause + case pair
        for i, (toxic_clause, selected_case) in enumerate(zip(
            state["relevant_toxic_clauses"][:len(state["selected_cases"])], 
            state["selected_cases"]
        )):
            toxic_clause_text = f"""
            독소조항:
            - 조항: {toxic_clause.get('독소조항', '')}
            - 이유: {toxic_clause.get('이유', '')}
            """
            
            # Use formatted case summary instead of raw case text
            case_summary = selected_case.get("formatted_case", "판례 분석 실패")
            
            context = f"""
                        1. 독소조항:
                        {toxic_clause_text}

                        2. 관련 판례:
                        {case_summary}
                      """
            
            messages = [
                {"role": "system", "content": simulation_prompt},
                {"role": "user", "content": context}
            ]
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",  
                messages=messages,
                temperature=0.1,
            )
            
            state["simulations"].append(response.choices[0].message.content.strip())
            logger.info(f"Completed simulation {i+1}")
        
        return state
    except Exception as e:
        logger.error(f"Error in simulations: {e}")
        state["error"] = f"Simulation error: {str(e)}"
        state["simulations"] = ["시뮬레이션을 실행하지 못했습니다."] * len(state.get("selected_cases", []))
        return state

def create_simulation_workflow(
    case_db_path: str,
    embedding_path: str,
    simulation_prompt_path: str,
    format_prompt_path: str,
    openai_api_key: str,
    upstage_api_key: str,
    highlight_prompt_path: str
) -> Graph:
    """Create the Langgraph workflow for dispute simulation"""
    
    # Load prompts
    with open(simulation_prompt_path, 'r', encoding='utf-8') as f:
        simulation_prompt = f.read()
    with open(format_prompt_path, 'r', encoding='utf-8') as f:
        format_prompt = f.read()
    
    # Initialize components
    case_retriever = CaseLawRetriever(case_db_path, embedding_path)
    case_retriever.load_cases()
    
    document_parser = DocumentParser(upstage_api_key)
    
    client = OpenAI(api_key=openai_api_key)
    
    llm_highlighter = ToxicClauseFinder(
        openai_api_key=openai_api_key,
        prompt_path=highlight_prompt_path,
        case_retriever=case_retriever
    )
    
    # Create the StateGraph
    workflow = StateGraph(SimulationState)
    
    # Add nodes
    workflow.add_node("parse", lambda state: parse_document(state, document_parser))
    workflow.add_node("extract", lambda state: extract_toxic_clauses(state, llm_highlighter))
    workflow.add_node("select_clauses", lambda state: select_relevant_toxic_clauses(state, case_retriever.model))
    workflow.add_node("retrieve", lambda state: retrieve_cases_for_clauses(state, case_retriever, format_prompt, client))
    workflow.add_node("select_cases", lambda state: select_best_cases(state, case_retriever, format_prompt, client))
    workflow.add_node("simulate", lambda state: run_simulations(state, simulation_prompt, client))
    
    # Add edges
    workflow.add_edge("parse", "extract")
    workflow.add_edge("extract", "select_clauses")
    workflow.add_edge("select_clauses", "retrieve")
    workflow.add_edge("retrieve", "select_cases")
    workflow.add_edge("select_cases", "simulate")
    
    # Set entry point
    workflow.set_entry_point("parse")
    
    return workflow.compile()

def run_simulation_from_file(
    file_obj,
    query: str,
    case_db_path: str,
    embedding_path: str,
    simulation_prompt_path: str,
    format_prompt_path: str,
    highlight_prompt_path: str
) -> Dict[str, Any]:
    """Run the simulation from a file object and query"""
    try:
        logger.info(f"Starting simulation for query: '{query}'")
        
        # Create workflow
        graph = create_simulation_workflow(
            case_db_path=case_db_path,
            embedding_path=embedding_path,
            simulation_prompt_path=simulation_prompt_path,
            format_prompt_path=format_prompt_path,
            openai_api_key=os.getenv('OPENAI_API_KEY'),
            upstage_api_key=os.getenv('UPSTAGE_API_KEY'),
            highlight_prompt_path=highlight_prompt_path
        )
        
        # Parse document first (outside the graph for simplicity with file handling)
        document_parser = DocumentParser(os.getenv('UPSTAGE_API_KEY'))
        
        # Reset file position and log details for debugging
        if hasattr(file_obj, 'seek'):
            file_obj.seek(0)
            logger.info("Reset file position to beginning")
        
        # Get some information about the file object
        if hasattr(file_obj, 'read'):
            sample = file_obj.read(100)
            file_obj.seek(0)
            logger.info(f"File object sample: {sample[:20]}... (showing first 20 bytes)")
        
        logger.info("Parsing document...")
        parse_result = document_parser.parse(file_obj)
        
        # Enhanced error logging
        if "error" in parse_result:
            logger.error(f"Document parser returned error: {parse_result['error']}")
            return {"error": f"문서 파싱 오류: {parse_result.get('error', '알 수 없는 오류')}"}
        
        document_text = parse_result.get("content", {}).get("text", "")
        
        if not document_text:
            logger.error("Failed to extract text from document")
            logger.error(f"Parse result keys: {list(parse_result.keys())}")
            if "content" in parse_result:
                logger.error(f"Content keys: {list(parse_result['content'].keys())}")
            return {"error": "Failed to extract text from document"}
        
        logger.info(f"Successfully extracted {len(document_text)} characters of text from document")
        
        # Initial state
        initial_state = {
            "query": query,
            "document_text": document_text,
            "document_file": None,  # Not needed since we've already parsed
            "toxic_clauses": [],
            "relevant_toxic_clauses": [],
            "similar_cases": [],
            "selected_cases": [],
            "simulations": [],
            "error": ""
        }
        
        # Run graph
        result = graph.invoke(initial_state)
        
        # Check for errors
        if result.get("error"):
            logger.error(f"Graph execution completed with error: {result['error']}")
            return {"error": result["error"]}
        
        # Return results
        return {
            "simulations": result.get("simulations", []),
            "relevant_toxic_clauses": result.get("relevant_toxic_clauses", []),
            "selected_cases": result.get("selected_cases", [])
        }
        
    except Exception as e:
        logger.error(f"Uncaught error during graph execution: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {"error": f"실행 오류: {str(e)}"}
    
def convert_numpy_types(obj):
    """
    Recursively convert numpy types to native Python types for JSON serialization
    """
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    elif isinstance(obj, tuple):
        return tuple(convert_numpy_types(item) for item in obj)
    else:
        return obj

# Tool decorator for direct usage from other modules
@tool(args_schema=SimulationToolSchema, description="Simulates potential contract disputes and outcomes based on the user's query and the provided contract document, especially when legal interpretation or clause-related conflicts are involved.")
def simulate_dispute_tool(query: str, file_id: str) -> Dict[str, Any]:
    """Simulates a contract dispute scenario based on a contract document and user query."""
    try:
        logger.info(f"Running simulation for query: {query}")
        logger.info(f"File ID: {file_id}")
        
        if not file_id:
            logger.error("No file ID provided")
            return {"error": "계약서 파일 ID가 제공되지 않았습니다."}
        
        # Retrieve file from S3
        try:
            logger.info(f"Retrieving file from S3 with key: {file_id}")
            # Add error handling for different key formats
            if not file_id.startswith("pdf/"):
                file_id = f"{file_id}"
                logger.info(f"Adjusted file ID to: {file_id}")
            
            # Get the document from S3
            try:
                response = s3.get_object(Bucket=BUCKET_NAME, Key=file_id)
                content_type = response.get('ContentType', '')
                logger.info(f"Retrieved file from S3 with content type: {content_type}")
                
                # Read the entire content into memory
                file_content = response['Body'].read()
                logger.info(f"Read {len(file_content)} bytes from S3")
                
                # Create a BytesIO object to use as a file-like object
                file_obj = io.BytesIO(file_content)
                file_obj.seek(0)
                
                # Check if this looks like a PDF (starts with %PDF-)
                if not file_content.startswith(b'%PDF-'):
                    logger.warning(f"File does not appear to be a PDF. First bytes: {file_content[:20]}")
                
                logger.info("Successfully created file object from S3 content")
            except Exception as e:
                logger.error(f"Error getting object from S3: {e}")
                return {"error": f"S3에서 파일을 검색하는 데 실패했습니다: {str(e)}"}
            
            # Use the provided document parser with our file object
            result = run_simulation_from_file(
                file_obj,
                query,
                CASE_DB_PATH,
                EMBEDDING_PATH,
                SIMULATION_PROMPT_PATH, 
                FORMAT_PROMPT_PATH,
                HIGHLIGHT_PROMPT_PATH
            )
            
            if "error" in result and result["error"]:
                logger.error(f"Simulation error: {result['error']}")
            else:
                logger.info("Simulation completed successfully")
                
            # Convert NumPy types to Python native types before returning
            return convert_numpy_types(result)
            
        except Exception as e:
            logger.error(f"Error in file processing: {e}")
            return {"error": f"파일 처리 중 오류 발생: {str(e)}"}
            
    except Exception as e:
        logger.error(f"Error in simulation tool: {e}")
        logger.error(traceback.format_exc())
        return {"error": f"시뮬레이션 실행 중 오류 발생: {str(e)}"}

# if __name__ == "__main__":
    # Configuration
    # CASE_DB_PATH = "../datasets/case_db.json"
    # EMBEDDING_PATH = "../datasets/precomputed_embeddings.npz"
    # SIMULATION_PROMPT_PATH = "../prompts/simulate_dispute.txt"
    # FORMAT_PROMPT_PATH = "../prompts/format_output.txt"
    # HIGHLIGHT_PROMPT_PATH = "../prompts/highlight_prompt.txt"
    # TEST_PDF_PATH = "/Users/limdongha/workspace/LegalFore/input_ex.pdf"  # 테스트용 PDF 파일 경로
    
    # def run_test_simulation():
    #     logger.info("Starting test simulation...")
        
    #     # 테스트 쿼리
    #     test_query = "계약 해지 상황을 시뮬레이션해줘"
        
    #     try:
    #         # PDF 파일 열기
    #         with open(TEST_PDF_PATH, 'rb') as file_obj:
    #             # 시뮬레이션 실행
    #             result = run_simulation_from_file(
    #                 file_obj,
    #                 test_query,
    #                 CASE_DB_PATH,
    #                 EMBEDDING_PATH,
    #                 SIMULATION_PROMPT_PATH,
    #                 FORMAT_PROMPT_PATH,
    #                 HIGHLIGHT_PROMPT_PATH
    #             )
                
    #             # 결과 출력
    #             logger.info("\n=== Simulation Test Results ===")
    #             logger.info(f"Query: {test_query}")
                
    #             if "error" in result:
    #                 logger.error(f"Error: {result['error']}")
    #                 return
                
    #             # 관련 독소조항 출력
    #             logger.info("\n--- Relevant Toxic Clauses ---")
    #             for idx, clause in enumerate(result.get("relevant_toxic_clauses", []), 1):
    #                 logger.info(f"\nClause {idx}:")
    #                 logger.info(f"독소조항: {clause.get('독소조항', 'N/A')}")
    #                 logger.info(f"이유: {clause.get('이유', 'N/A')}")
                
    #             # 선택된 판례 출력
    #             logger.info("\n--- Selected Cases ---")
    #             for idx, case in enumerate(result.get("selected_cases", []), 1):
    #                 logger.info(f"\nCase {idx}:")
    #                 logger.info(f"Similarity Score: {case.get('similarity_score', 'N/A')}")
    #                 logger.info(f"Formatted Case: {case.get('formatted_case', 'N/A')}")
                
    #             # 시뮬레이션 결과 출력
    #             logger.info("\n--- Simulation Results ---")
    #             for idx, simulation in enumerate(result.get("simulations", []), 1):
    #                 logger.info(f"\nSimulation {idx}:")
    #                 logger.info(simulation)
                
    #     except FileNotFoundError:
    #         logger.error(f"Test PDF file not found at {TEST_PDF_PATH}")
    #     except Exception as e:
    #         logger.error(f"Test failed with error: {str(e)}")
    #         logger.error(traceback.format_exc())
    
    # # 테스트 실행
    # logger.info("=== Starting Langgraph Simulation Test ===")
    # run_test_simulation()
    # logger.info("=== Test Complete ===")
