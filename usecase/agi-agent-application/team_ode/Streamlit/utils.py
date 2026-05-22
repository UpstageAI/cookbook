from dotenv import load_dotenv
import json
import os
import tempfile
from datetime import datetime
from openai import OpenAI

load_dotenv()

OPEN_API_KEY = os.getenv("OPEN_API_KEY")

# OpenAI 클라이언트 초기화
client = OpenAI(api_key=OPEN_API_KEY)

def get_conversation_file_path(conversation_type: str):
    """
    대화 유형별 파일 경로를 반환합니다.
    Supported conversation_type:
      - "sidebar_chat": chat_history.json
      - "document_processing": document_memory.json
      - "pdf_validation": form_memory.json
      그 외에는 conversation_memory.json
    """
    current_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "../Chatbot/chat_history"
        )
    file_names = {
        "sidebar_chat": "chat_history.json",
        "document_processing": "document_memory.json",
        "pdf_validation": "form_memory.json"
    }
    return os.path.join(current_dir, file_names.get(conversation_type, "conversation_memory.json"))

def save_conversation(conversation_type: str, chat_data: dict):
    """
    대화 내용을 딕셔너리 형태로 저장합니다.
    예시:
    {
        "chat_20250403_210703": {
            "id": "chat_20250403_210703",
            "messages": [...],
            "title": "Incoterms Explained",
            "timestamp": "20250403_210820"
        }
    }
    """
    try:
        file_path = get_conversation_file_path(conversation_type)
        
        # 기존 데이터를 딕셔너리로 로드 (없으면 빈 딕셔너리)
        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if not isinstance(data, dict):
                    data = {}
            except Exception as e:
                print(f"Error loading existing conversation data: {str(e)}")
                data = {}
        else:
            data = {}
        
        # 현재 대화 데이터를 갱신합니다.
        data[chat_data["id"]] = chat_data
        
        # 임시 파일에 저장 후 원본 파일로 이동하여 데이터 손상 방지
        temp_fd, temp_path = tempfile.mkstemp(dir=os.path.dirname(file_path), suffix='.json')
        with os.fdopen(temp_fd, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(temp_path, file_path)
        print(f"대화가 저장되었습니다: {file_path}")
    except Exception as e:
        print(f"대화 저장 중 오류 발생: {str(e)}")

def load_conversations(conversation_type: str = None):
    """
    저장된 대화 내용을 불러옵니다.
    
    Args:
        conversation_type (str, optional): 특정 대화 유형을 지정할 경우 해당 파일에서 불러옵니다.
    
    Returns:
        list: 저장된 대화 목록 (conversations 키 아래의 리스트)
    """
    try:
        file_path = get_conversation_file_path(conversation_type)
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                memory = json.load(f)
                return memory.get("conversations", [])
        return []
    except Exception as e:
        print(f"대화 불러오기 중 오류 발생: {str(e)}")
        return []

def perform_web_search(query: str):
    """
    웹 검색을 수행하고, 결과를 저장 후 반환합니다.
    
    Args:
        query (str): 검색할 질의 내용
    
    Returns:
        str or None: 웹 검색 결과 요약 (실패 시 None)
    """
    try:
        print("Web searching using GPT-4 search tool")
        response = client.responses.create(
            model="gpt-4o",
            tools=[{"type": "web_search_preview"}],
            input=query
        )
        search_result = response.output_text
        save_search_result(query, search_result)
        return search_result
    except Exception as e:
        print(f"Error performing web search: {str(e)}")
        return None

def enhance_prompt_with_web_search(prompt: str, web_search_enabled: bool = False) -> str:
    """
    프롬프트에 웹 검색 결과를 통합합니다.
    
    Args:
        prompt (str): 원래 프롬프트
        web_search_enabled (bool): 웹 검색 사용 여부
    
    Returns:
        str: 웹 검색 결과가 통합된 프롬프트 (웹 검색이 비활성화면 원본 프롬프트 반환)
    """
    if not web_search_enabled:
        return prompt
    try:
        search_result = perform_web_search(prompt)
        if search_result:
            enhanced_prompt = f"""Based on the following web search results:

{search_result}

Please provide a comprehensive response to this query: {prompt}

Make sure to incorporate relevant information from the web search results while maintaining accuracy and relevance."""
            return prompt, search_result, enhanced_prompt
    except Exception as e:
        print(f"Error enhancing prompt with web search: {str(e)}")
    return prompt, None, None

def save_search_result(query: str, result: str):
    """
    검색 결과를 저장합니다.
    
    Args:
        query (str): 검색 질의
        result (str): 검색 결과 요약
    """
    try:
        chat_history_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../Chatbot/chat_history")
        if not os.path.exists(chat_history_dir):
            os.makedirs(chat_history_dir)
        
        search_file = os.path.join(chat_history_dir, "search_history.json")
        
        # 기존 검색 기록 로드 (없으면 빈 딕셔너리)
        search_history = {}
        if os.path.exists(search_file):
            try:
                with open(search_file, "r", encoding="utf-8") as f:
                    search_history = json.load(f)
            except Exception as e:
                print(f"Error loading search history: {str(e)}")
                search_history = {}
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        search_id = f"search_{timestamp}"
        search_history[search_id] = {
            "query": query,
            "result": result,
            "timestamp": timestamp
        }
        
        with open(search_file, "w", encoding="utf-8") as f:
            json.dump(search_history, f, ensure_ascii=False, indent=2)
        print(f"Successfully saved search result to: {search_file}")
    except Exception as e:
        print(f"Error saving search result: {str(e)}")

def load_search_history():
    """
    저장된 검색 기록을 불러옵니다.
    
    Returns:
        dict: 검색 기록 (검색 ID를 키로 하는 딕셔너리)
    """
    try:
        chat_history_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../Chatbot/chat_history")
        search_file = os.path.join(chat_history_dir, "search_history.json")
        if not os.path.exists(search_file):
            return {}
        with open(search_file, "r", encoding="utf-8") as f:
            history = json.load(f)
            return history
    except Exception as e:
        print(f"Error loading search history: {str(e)}")
        return {}

def load_user_info():
    """
    저장된 사용자 정보를 불러옵니다.
    
    Returns:
        dict or None: 사용자 정보 (없으면 None)
    """
    try:
        chat_history_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../Chatbot/chat_history")
        user_info_file = os.path.join(chat_history_dir, "user_information.json")
        if not os.path.exists(user_info_file):
            return None
        with open(user_info_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("user_information")
    except Exception as e:
        print(f"Error loading user information: {str(e)}")
        return None
