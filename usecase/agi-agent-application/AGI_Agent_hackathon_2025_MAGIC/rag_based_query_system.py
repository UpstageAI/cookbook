from openai import OpenAI
import numpy as np
from typing import List, Dict
import json
import faiss
import pandas as pd

class HealthRAGSystem:
    def __init__(self, api_key: str, faiss_index_path: str, metadata_csv: str):
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.upstage.ai/v1"
        )        
        
        self.health_status = None
        # Load the FAISS index
        self.index = faiss.read_index(faiss_index_path)
        # Load guideline metadata with chunk texts and other details
        self.guidelines_df = pd.read_csv(metadata_csv)

    def load_health_status(self, health_status: Dict):
        """Load the patient's health status"""
        self.health_status = health_status

    def preprocess_query(self, query: str) -> str:
        """Optional query preprocessing"""
        # For now, just return the original query
        # You can add keyword extraction or other preprocessing here
        return query

    def get_embeddings(self, text: str) -> np.ndarray:
        """Get embeddings using Solar API"""
        response = self.client.embeddings.create(
            model="embedding-query",  # Use appropriate embedding model
            input=text
        )
        return np.array(response.data[0].embedding)

    def retrieve_relevant_snippets(self, query: str, top_k: int = 3) -> List[str]:
        # Compute the query embedding
        query_embedding = self.get_embeddings(query)
        # FAISS expects a 2D array of type float32
        query_embedding = np.array([query_embedding]).astype("float32")
        # Query the FAISS index for top k results
        distances, indices = self.index.search(query_embedding, top_k)
        
        relevant_snippets = []
        for idx in indices[0]:
            snippet = self.guidelines_df.iloc[idx]['chunk_text']
            relevant_snippets.append(snippet)
        
        return relevant_snippets


    def construct_prompt(self, query: str, relevant_snippets: List[str]) -> str:
        """Construct the prompt for the LLM"""
        prompt = f"""[사용자의 건강 검진 결과]를 염두에 두면서 [관련 의료 지침]을 바탕으로 [사용자 질문]에 대한 상세하고 이해하기 쉬운 설명을 제공해주세요. 지침의 범위를 벗어난 질문에는 답변하지 마세요. 
        #사용자의 건강 검진 결과:{json.dumps(self.health_status, indent=2, ensure_ascii=False)}

        #관련 의료 지침:
        """
        for i, snippet in enumerate(relevant_snippets, 1):
            prompt += f"{i}. {snippet}\n"

        prompt += f"\n#사용자 질문: {query}\n"
        
        return prompt

    def generate_response(self, query: str) -> str:
        """Generate final response using Solar LLM"""
        # Preprocess query
        processed_query = self.preprocess_query(query)
        
        # Retrieve relevant snippets
        relevant_snippets = self.retrieve_relevant_snippets(processed_query)
        
        # Construct prompt
        prompt = self.construct_prompt(processed_query, relevant_snippets)
        
        # Generate response using Solar
        response = self.client.chat.completions.create(
            model="solar-pro",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        return response.choices[0].message.content

# Example usage
def main(api_key: str, health_status: Dict, user_query: str):
    """
    Main function to run the HealthRAGSystem with provided parameters
    
    Args:
        api_key: API key for the OpenAI client
        health_status: Dictionary containing patient health data
        user_query: User's health-related question
    
    Returns:
        Response from the RAG system
    """
    # Initialize the RAG system
    rag_system = HealthRAGSystem(
        api_key=api_key,
        faiss_index_path="data/every_faiss_index.bin",
        metadata_csv="data/RAG_every.csv"
    )
    
    # Load health status
    rag_system.load_health_status(health_status)
    
    # Generate and return response
    response = rag_system.generate_response(user_query)
    print("Response:", response)
    return response

if __name__ == "__main__":
    # Example parameters (commented out - would be provided as actual parameters)
    """
    Example health_status:
    {
        "생년월일": "780203-3",
        "검진일": "2025년 5월 5일",
        "검진종합소견": "고혈압 및 당뇨병 전단계 소견",
        "키": 175,
        "몸무게": 86.2,
        "체질량지수": 28.2,
        "허리둘레": 92.0,
        "혈압": "145/95 mmHg",
        "혈색소": "14.2",
        "빈혈 소견": "정상",
        "공복혈당": "128",
        "당뇨병 소견": "공복혈당장애 의심",
        "총콜레스테롤": "220",
        "고밀도콜레스테롤": "38",
        "중성지방": "180",
        "저밀도콜레스테롤": "148",
        "이상지질혈증 소견": "이상지질혈증 의심",
        "혈청크레아티닌": "1.1",
        "eGFR": "79",
        "신장질환 소견": "정상",
        "AST": "35",
        "ALT": "38",
        "감마지티피": "60",
        "간장질환": "경계성 간기능 이상",
        "요단백": "미량",
        "흉부촬영": "정상"
    }
    
    Example user_query: "고혈압에 좋은 음식이 따로 있나요?"
    """
    
    # Sample usage - uncomment and modify as needed
    # health_data = {...}  # Replace with actual health data
    # api_key = "your_api_key"
    # question = "your health question"
    # main(api_key, health_data, question) 