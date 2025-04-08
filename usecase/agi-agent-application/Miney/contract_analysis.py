import os
from openai import OpenAI
from dotenv import load_dotenv
from risk_assessor import LegalRiskAssessor

# 환경 변수 로드
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 위험도 평가 실행
risk_assessor = LegalRiskAssessor()

def analyze_contract(contract_data):
    """
    계약서의 조항에 대한 위험도 분석을 수행하고, 
    불리한 조항과 주의할 조항을 분리하여 반환하는 함수
    """
    result = risk_assessor.assess_contract(contract_data)
    
    categorized_clauses = result['categorized_clauses']

    return categorized_clauses

def create_contract_with_risk(contract_data):
    """
    계약서에 위험도 정보를 추가하여 반환하는 함수
    """
    result = risk_assessor.assess_contract(contract_data)
    
    return result['contract_data']

if __name__ == "__main__":
    pass