from typing import Dict, List, TypedDict, Any
from langgraph.graph import Graph, StateGraph
import numpy as np
from openai import OpenAI
import os
from dotenv import load_dotenv
from src.tools.highlight import CaseLawRetriever
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from src.config import CASE_DB_PATH, EMBEDDING_PATH, FORMAT_PROMPT_PATH

load_dotenv()

# Define schema for the case search tool
class CaseSearchToolSchema(BaseModel):
    query: str = Field(..., description="User query to find relevant legal cases")

class QueryState(TypedDict):
    query: str
    similar_cases: List[dict]
    formatted_results: List[str]
    error: str

def retrieve_cases(state: QueryState, case_retriever: CaseLawRetriever) -> QueryState:
    """검색 노드: 유사 판례 찾기"""
    try:
        print(f"Retrieving similar cases for query: {state['query']}")
        query_embedding = case_retriever.model.encode(state["query"])
        similarities = np.dot(case_retriever.case_embeddings, query_embedding) / (
            np.linalg.norm(case_retriever.case_embeddings, axis=1) * np.linalg.norm(query_embedding)
        )
        
        # Top 1 similar case
        top_index = np.argmax(similarities)
        state["similar_cases"] = [
            {
                "case": case_retriever.cases[top_index]["value"],
                "similarity_score": float(similarities[top_index])
            }
        ]
        print(f"Found most similar case")
        return state
    except Exception as e:
        print(f"Error in retrieve_cases: {e}")
        state["error"] = f"검색 오류: {str(e)}"
        state["similar_cases"] = []
        return state

def format_cases(state: QueryState, format_prompt: str, client: OpenAI) -> QueryState:
    """포맷팅 노드: 판례 포맷팅"""
    if state.get("error"):
        return state
        
    try:
        print("Formatting case results...")
        formatted_results = []
        for case in state["similar_cases"]:
            case_content = str(case["case"])
            messages = [
                {"role": "system", "content": format_prompt},
                {"role": "user", "content": case_content}
            ]
            
            try:
                response = client.chat.completions.create(
                    model="gpt-4o-mini",  # gpt-4o-mini 대신 더 안정적인 모델 사용
                    messages=messages,
                    temperature=0.1
                )
                formatted_results.append(response.choices[0].message.content.strip())
                print(f"Successfully formatted case result")
            except Exception as e:
                print(f"Error formatting individual case: {e}")
                formatted_results.append(f"판례 분석 실패: {str(e)}")
        
        state["formatted_results"] = formatted_results[0]
        return state
    except Exception as e:
        print(f"Error in format_cases: {e}")
        state["error"] = f"포맷팅 오류: {str(e)}"
        state["formatted_results"] = ["판례 분석 실패"]
        return state

def create_case_query_workflow(
    case_db_path: str,
    embedding_path: str,
    format_prompt_path: str
) -> Graph:
    """최신 StateGraph API를 사용한 워크플로우 생성"""
    
    # 필요한 리소스 로드
    case_retriever = CaseLawRetriever(case_db_path, embedding_path)
    case_retriever.load_cases()
    
    with open(format_prompt_path, 'r', encoding='utf-8') as f:
        format_prompt = f.read()
    
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    
    # StateGraph 생성
    workflow = StateGraph(QueryState)
    
    # 노드 정의 (클로저를 사용하여 외부 의존성 주입)
    workflow.add_node("retrieve", lambda state: retrieve_cases(state, case_retriever))
    workflow.add_node("format", lambda state: format_cases(state, format_prompt, client))
    
    # 에지 정의
    workflow.add_edge("retrieve", "format")
    
    # 시작점 설정
    workflow.set_entry_point("retrieve")
    
    return workflow.compile()

def query_cases(query: str, graph: Graph) -> List[str]:
    """그래프 실행 함수"""
    try:
        print(f"Starting query execution for: '{query}'")
        
        # 초기 상태 설정
        initial_state = {
            "query": query,
            "similar_cases": [],
            "formatted_results": [],
            "error": ""
        }
        
        # 그래프 실행
        result = graph.invoke(initial_state)
        
        # 결과 확인 (오류가 있으면 오류 메시지 반환)
        if result.get("error"):
            print(f"Graph execution completed with error: {result['error']}")
            return [f"오류: {result['error']}"]
            
        # 결과 반환
        if result.get("formatted_results"):
            print(f"Graph execution completed successfully")
            return result["formatted_results"]
            
        # 기본 메시지
        return ["판례 분석 결과를 찾을 수 없습니다."]
        
    except Exception as e:
        print(f"Uncaught error during graph execution: {e}")
        return [f"실행 오류: {str(e)}"]

# Tool decorator for direct usage from other modules
@tool(args_schema=CaseSearchToolSchema, description="Retrieves cases that best match the user's query, helping to identify precedents directly relevant to the user's legal intent or question.")
def find_case_tool(query: str) -> List[str]:
    """Finds relevant legal cases based on user query."""
    try:
        print(f"Finding cases for query: {query}")
        
        # Create the case query workflow using paths from config
        graph = create_case_query_workflow(
            case_db_path=CASE_DB_PATH,
            embedding_path=EMBEDDING_PATH,
            format_prompt_path=FORMAT_PROMPT_PATH
        )
        
        # Query cases
        results = query_cases(query, graph)
        return results
    except Exception as e:
        print(f"Error in case search tool: {e}")
        return [f"Case search error: {str(e)}"]

# Usage example
# if __name__ == "__main__":
#     print("Creating case query workflow...")
#     graph = create_case_query_workflow(
#         case_db_path=CASE_DB_PATH,
#         embedding_path=EMBEDDING_PATH,
#         format_prompt_path=FORMAT_PROMPT_PATH
#     )
    
#     # 예제 쿼리
#     query = "집에 강도가 들어왔어"
#     print(f"\nProcessing query: '{query}'")
#     results = query_cases(query, graph)
    
#     print("Given query:", query)
#     for idx, result in enumerate(results, 1):
#         print(f"\nCase {idx}:")
#         print(result)
#         print("-" * 50)