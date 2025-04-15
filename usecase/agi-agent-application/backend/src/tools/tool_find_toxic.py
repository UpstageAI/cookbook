from typing import Dict, List, Any
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from src.tools.highlight import ToxicClauseFinder, CaseLawRetriever, DocumentParser
import os
import json
import traceback
import logging
import boto3
from botocore.config import Config
import io
from ..config import CASE_DB_PATH, EMBEDDING_PATH, HIGHLIGHT_PROMPT_PATH, OPENAI_API_KEY, UPSTAGE_API_KEY, FORMAT_PROMPT_PATH

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# S3 configuration
BUCKET_NAME = os.environ.get('BUCKET_NAME', 'wetube-gwanwoo')
s3 = boto3.client('s3',
    aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
    region_name='ap-northeast-2',
    config=Config(signature_version='s3v4')
)

# Define schema for the toxic clause search tool
class ToxicClauseToolSchema(BaseModel):
    query: str = Field(..., description="User query about toxic clauses in contracts")
    file_id: str = Field(..., description="File ID or key to retrieve the contract document from S3")

@tool(args_schema=ToxicClauseToolSchema, description="Identifies and returns potentially toxic, unfair, one-sided, or legally risky clauses within a contract.")
def find_toxic_clauses_tool(query: str, file_id: str) -> Dict[str, Any]:
    """
    Analyzes contract document to find toxic clauses based on user query.
    
    Args:
        query: The user's query about toxic clauses
        file_id: The file ID or key to retrieve the contract document from S3
    
    Returns:
        A dictionary with type, rationale, and highlights of toxic clauses
    """
    try:
        logger.info(f"Finding toxic clauses for query: {query}")
        logger.info(f"File ID: {file_id}")
        
        # Check if file_id is None or invalid
        if file_id is None:
            logger.error("File ID is None")
            return {"error": "계약서 파일 ID가 없습니다. 파일을 먼저 업로드해주세요."}
        
        # Retrieve file from S3
        try:
            logger.info(f"Retrieving file from S3 with key: {file_id}")
            # Add error handling for different key formats
            if not file_id.startswith("pdf/"):
                file_id = f"{file_id}"
                logger.info(f"Adjusted file ID to: {file_id}")
                
            # Use a try-except block to handle potential errors
            try:
                response = s3.get_object(Bucket=BUCKET_NAME, Key=file_id)
                content_type = response.get('ContentType', '')
                logger.info(f"Retrieved file from S3 with content type: {content_type}")
                
                # Read the entire content into memory
                file_content = response['Body'].read()
                logger.info(f"Read {len(file_content)} bytes from S3")
                
                # Create a BytesIO object to ensure seek functionality
                file_obj = io.BytesIO(file_content)
                file_obj.seek(0)
                
                # Check if this looks like a PDF (starts with %PDF-)
                if not file_content.startswith(b'%PDF-'):
                    logger.warning(f"File does not appear to be a PDF. First bytes: {file_content[:20]}")
                    if content_type == 'application/json':
                        logger.info("Retrieved content is JSON, not PDF")
                        return {"error": "S3 객체가 PDF가 아닌 JSON 데이터입니다."}
                
                logger.info("Successfully created file object from S3 content")
            except Exception as e:
                logger.error(f"Error getting object from S3: {e}")
                return {"error": f"S3에서 파일을 검색하는 데 실패했습니다: {str(e)}"}
            
            # Parse document
            logger.info("Parsing document...")
            document_parser = DocumentParser(UPSTAGE_API_KEY)
            parse_result = document_parser.parse(file_obj)
            
            # Check for parsing errors
            if isinstance(parse_result, dict) and "error" in parse_result:
                logger.error(f"Document parsing error: {parse_result['error']}")
                return {"error": f"문서 파싱 오류: {parse_result['error']}"}
            
            document_text = parse_result.get("content", {}).get("text", "")
            
            if not document_text:
                logger.error("Failed to extract text from document")
                if isinstance(parse_result, dict):
                    logger.error(f"Parse result keys: {list(parse_result.keys())}")
                    if "content" in parse_result and isinstance(parse_result["content"], dict):
                        logger.error(f"Content keys: {list(parse_result['content'].keys())}")
                return {"error": "문서에서 텍스트를 추출할 수 없습니다."}
            
            logger.info(f"Successfully extracted {len(document_text)} characters of text from document")
            
            # Initialize the case retriever
            try:
                logger.info("Initializing case retriever...")
                case_retriever = CaseLawRetriever(
                    case_db_path=CASE_DB_PATH,
                    embedding_path=EMBEDDING_PATH
                )
                case_retriever.load_cases()
            except FileNotFoundError as e:
                logger.error(f"Error loading case database or embeddings: {e}")
                return {"error": f"판례 데이터베이스 로딩 오류: {str(e)}"}
            
            # Initialize the toxic clause finder with API key rather than app
            try:
                logger.info("Initializing toxic clause finder...")
                toxic_finder = ToxicClauseFinder(
                    openai_api_key=OPENAI_API_KEY,
                    prompt_path=HIGHLIGHT_PROMPT_PATH,
                    case_retriever=case_retriever
                )
                
                # Find toxic clauses in the document
                logger.info("Finding toxic clauses in document...")
                highlight_result = toxic_finder.find(document_text)
                
                if not highlight_result:
                    logger.info("No toxic clauses found")
                    return {"type": "highlights", "rationale": "", "highlights": []}
                
                # Format the output to match routes.py
                high_json = json.loads(json.dumps(highlight_result, ensure_ascii=False, indent=2))
                
                # 변환 (Same code as in routes.py)
                result_highlight = dict()
                converted = []
                
                logger.info(f"Processing {len(high_json)} toxic clauses...")
                
                rationale = ""
                print("High Json: ", high_json)
                for item in high_json:
                    converted.append(item.get("독소조항", ""))
                    if "친절한_설명" in item:
                        rationale = item["친절한_설명"]
                
                result_highlight["type"] = "highlights"
                result_highlight["rationale"] = rationale
                result_highlight["highlights"] = converted
                
                logger.info(f"Successfully prepared highlights with {len(converted)} toxic clauses")
                return result_highlight
                
            except Exception as e:
                logger.error(f"Error in toxic clause analysis: {e}")
                return {"error": f"독소조항 분석 중 오류 발생: {str(e)}"}
                
        except Exception as e:
            logger.error(f"Error in file processing: {e}")
            return {"error": f"파일 처리 중 오류 발생: {str(e)}"}
            
    except Exception as e:
        logger.error(f"Error in find_toxic_clauses_tool: {str(e)}")
        logger.error(traceback.format_exc())
        return {"error": f"독소조항 분석 도구 오류: {str(e)}"}
