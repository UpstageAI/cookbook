import requests
from flask import Flask, request, jsonify
from openai import OpenAI
import json
import os
from src.imsi.basic import *
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
import numpy as np
from tqdm import tqdm
from collections import OrderedDict


load_dotenv()

class CaseLawRetriever:
    def __init__(self, case_db_path: str, embedding_path: str = None):
        self.case_db_path = case_db_path
        self.embedding_path = embedding_path or case_db_path.replace('.json', '_embeddings.npz')
        self.model = None
        self.cases = None
        self.case_embeddings = None
        self.case_texts = None
        
    def _init_model(self):
        if self.model is None:
            print("Loading sentence transformer model...")
            self.model = SentenceTransformer("nlpai-lab/KURE-v1")
    
    def load_cases(self):
        print("Loading case database...")
        with open(self.case_db_path, 'r', encoding='utf-8') as f:
            self.cases = json.load(f)
            
        # 미리 계산된 임베딩이 있는지 확인
        if os.path.exists(self.embedding_path):
            print("Loading pre-computed embeddings...")
            loaded = np.load(self.embedding_path, allow_pickle=True)
            self.case_texts = loaded['texts']
            self.case_embeddings = loaded['embeddings']
            self._init_model()  # 모델 초기화 추가
        else:
            # 기존 방식대로 실시간 계산
            self._init_model()
            print("Computing embeddings...")
            self.case_embeddings = []
            self.case_texts = []
            for case in tqdm(self.cases, desc="Processing cases"):
                self.case_texts.append(case['key'])
                self.case_embeddings.append(self.model.encode(case['key']))
            self.case_embeddings = np.array(self.case_embeddings)
            
            # Save embeddings for future use
            print("Saving embeddings for future use...")
            np.savez(
                self.embedding_path,
                texts=np.array(self.case_texts, dtype=object),
                embeddings=self.case_embeddings
            )
        
        print(f"Loaded {len(self.cases)} cases successfully")
    
    def find_similar_case(self, toxic_clause: str) -> dict:
        if self.model is None or self.cases is None:
            self.load_cases()
            
        if not isinstance(toxic_clause, str):
            raise ValueError(f"toxic_clause must be a string, got {type(toxic_clause)}")
            
        query_embedding = self.model.encode(toxic_clause)
        similarities = np.dot(self.case_embeddings, query_embedding) / (
            np.linalg.norm(self.case_embeddings, axis=1) * np.linalg.norm(query_embedding)
        )
        most_similar_idx = np.argmax(similarities)
        return {
            'case': self.cases[most_similar_idx]['value'],
            'similarity_score': float(similarities[most_similar_idx])
        }

class ToxicClauseFinder:
    def __init__(self, app, prompt_path: str, case_retriever: CaseLawRetriever):
        self.app = app
        self.prompt_path = prompt_path
        with open(prompt_path, 'r', encoding='utf-8') as f:
            self.system_prompt = f.read()
        get_openai_api_key("backend/conf.d/config.yaml")
        self.client = OpenAI()
        self.case_retriever = case_retriever
        with open("backend/prompts/format_output.txt", 'r', encoding='utf-8') as f:
            self.format_prompt = f.read()
    
    def format_case(self, case_details: str) -> str:  # 반환 타입을 dict에서 str로 변경
        """Format case details using LLM"""
        messages = [
            {"role": "system", "content": self.format_prompt},
            {"role": "user", "content": case_details}
        ]
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                temperature=0.1
            )
            
            # LLM 응답을 그대로 문자열로 반환
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            self.app.logger.error(f"Case formatting error: {str(e)}")
            return "판례 분석 실패"

    def highlight(self, text: str) -> list:
        """
        text: PDF 전체 텍스트
        반환: 독소 조항 분석 결과 리스트
        """
        print("Analyzing document with LLM...")
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": text}
        ]
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini", 
                messages=messages,
                temperature=0.1
            )
            
            result = response.choices[0].message.content
            # app.logger.info(f"Raw GPT response: {result}")  # 디버깅을 위한 로깅 추가
            
            # Remove code block markers if they exist
            result = result.replace('```json', '').replace('```', '').strip()
            # print(result)
            # JSON 시작과 끝 위치 찾기
            start_idx = result.find('[')
            end_idx = result.rfind(']') + 1
            
            if (start_idx == -1 or end_idx == 0):
                self.app.logger.error("No JSON array found in response")
                return []
                
            # JSON 부분만 추출
            json_str = result[start_idx:end_idx]
            
            try:
                parsed_result = json.loads(json_str)
                print(parsed_result)  # 디버깅을 위한 로깅 추가
                if not isinstance(parsed_result, list):
                    self.app.logger.error("Parsed result is not a list")
                    return []
                
                print("Finding similar cases...")
                # 결과 재구성 - 키 순서 변경
                reordered_result = []
                fri_exp = parsed_result[-1]["친절한_설명"]
                parsed_result = parsed_result[:-1]
                
                for item in tqdm(parsed_result, desc="Finding similar cases"):
                    similar_case = self.case_retriever.find_similar_case(item["독소조항"])
                    # Format the case details
                    formatted_case = self.format_case(str(similar_case["case"]))
                    
                    reordered_item = {
                        "독소조항": item["독소조항"],
                        "유사판례_정리": formatted_case,  # formatted_case는 이제 문자열
                        "유사판례_원문": similar_case["case"],
                        "유사도": similar_case["similarity_score"]
                        ,"친절한_설명": fri_exp
                    }
                    # OrderedDict를 사용하여 키 순서 보장
                    ordered_item = OrderedDict()
                    for key in ["독소조항", "유사판례_정리", "유사판례_원문", "유사도","친절한_설명"]:
                        ordered_item[key] = reordered_item[key]
                    reordered_result.append(ordered_item)
                
                print("Analysis complete!")
                return reordered_result
                
            except json.JSONDecodeError as je:
                self.app.logger.error(f"JSON parsing error: {str(je)}")
                return []
            
        except Exception as e:
            self.app.logger.error(f"LLM Analysis error: {str(e)}")
            return []

class OrderedJsonEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, OrderedDict):
            return {key: obj[key] for key in obj}
        return super().default(obj)


