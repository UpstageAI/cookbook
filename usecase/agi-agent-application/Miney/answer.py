import os
from openai import OpenAI
from rag_law_current import handle_user_query
from risk_assessor import LegalRiskAssessor
from dotenv import load_dotenv
load_dotenv()

# 🔐 OpenAI API 키 설정 (직접 입력 OR .env 방식도 가능)
client=OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 프롬프트 생성 함수 (질문을 받는 부분)
def make_question_prompt(user_input, contract, state):
    # 계약서 내용과 분석 결과를 포함한 프롬프트 생성
    조항들 = "\n".join([
        f"{c['조항']}: {c['내용']}\n"
        f"→ 위험도: {c['위험도']['score']}점 ({c['위험도']['level']})\n"
        f"  - 위험 요소: {', '.join([f'{k}: {v}점' for k, v in c['위험도']['factors'].items() if v > 0])}\n"
        for c in contract["계약"]
    ])

    특약 = "\n".join([
        f"{s['내용']}\n"
        f"→ 위험도: {s['위험도']['score']}점 ({s['위험도']['level']})\n"
        f"  - 위험 요소: {', '.join([f'{k}: {v}점' for k, v in s['위험도']['factors'].items() if v > 0])}\n"
        for s in contract["특약사항"]
    ])
    
    if state == 1:
        prompt = f"""
        너는 대한민국의 부동산 계약 및 임대차보호법에 정통한 법률 전문가야.
        아래 계약서 분석 결과와 사용자가 실제 발생한 분쟁 상황을 바탕으로 질문에 답해줘.

        [계약 정보 요약]
        - 구분: {contract['구분']}
        - 보증금: {contract['보증금']}
        - 차임: {contract['차임']}

        - 계약 조항:
        {조항들}

        - 특약사항:
        {특약}

        [사용자 상황 설명]
        {user_input}

        법적 판단을 내려줘.
        """
    else:
        prompt = f"""
        너는 대한민국의 부동산 계약 및 임대차보호법에 정통한 법률 전문가야.
        아래 계약서 분석 결과와 사용자가 실제 발생한 분쟁 상황을 바탕으로 사용자가 어떤 조치를 취해야 할지 정리해줘.

        [계약 정보 요약]
        - 구분: {contract['구분']}
        - 보증금: {contract['보증금']}
        - 차임: {contract['차임']}

        - 계약 조항:
        {조항들}

        - 특약사항:
        {특약}

        [사용자 상황 설명]
        {user_input}

        어떤 조치를 취해야 할지 정리해줘.
        """
    
    return prompt


# 계약서 분석 및 위험도 평가
def assess_contract_with_risk(contract_data):
    # 위험도 분석을 위한 LegalRiskAssessor 클래스 호출
    assessor = LegalRiskAssessor()
    contract_with_risk = assessor.assess_contract(contract_data)["contract_data"]
    
    return contract_with_risk

def get_legal_advice(user_input, contract_data, state):
    conversation_history = []
    contract_with_risk = assess_contract_with_risk(contract_data)
    res = handle_user_query(make_question_prompt( user_input, contract_with_risk, state), conversation_history)
    return res

'''
# 예시 실행
if __name__ == "__main__":
    # 계약서 예시 데이터 (실제 사용시, 업로드된 계약서 데이터를 사용할 수 있습니다.)
    contract_data = {
        "구분": "월세",
        "보증금": "10,000,000원",
        "차임": "600,000원",
        "계약": [
            {
                "조항": "제2조 [존속기간]",
                "내용": "임대인은 위 부동산을 임대차 목적대로 사용할 수 있는 상태로 2025년 02월 22일까지 임차인에게 인도하며, 임대차 기간은 인도일로부터 2027년 02월 21일(24개월)까지로 한다."
            },
            {
                "조항": "제3조 [용도변경 및 전대 등]",
                "내용": "임차인은 임대인의 동의 없이 위 부동산의 용도나 구조를 변경하거나 전대, 임차권 양도 또는 담보제공을 하지 못하며 임대차 목적 이외의 용도로 사용할 수 없다."
            }
        ],
        "특약사항": [
            "임차인은 현장확인 후 원상복구에 동의한다.",
            "계약기간 중 수리비용은 임차인이 부담한다.",
            "임차인이 월세를 연체할 경우, 연체 금액에 대해 월 10%의 지체이자를 가산하며, 해당 이자는 보증금에서 공제한다.",
            "보증금은 새로운 임차인이 구해질 때까지 반환되지 않으며, 반환 지연에 따른 이자는 지급하지 않는다.",
            "본 계약은 재건축 계획이 있을 경우 조건 없이 명도하는 것을 원칙으로 한다.",
            "세입자 과실이 아닌 경우에도 모든 시설물의 유지보수나 수리는 세입자가 부담한다."
        ]
    }

    # 사용자가 입력한 질문 예시
    user_input = "퇴실했는데, 집주인이 벽지 더러워졌다고 200만원을 공제하고 300만원만 주려 합니다."
    
    # 계약서 분석 후 법적 판단 결과를 받아오기
    # contract_with_risk = assess_contract_with_risk(contract_data)

    # 결과 출력
    print(get_legal_advice(user_input, contract_data))
    '''
