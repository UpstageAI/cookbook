from openai import OpenAI
import os
from dotenv import load_dotenv
import re

# 환경 변수 로드
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class LegalRiskAssessor:

    def __init__(self):
        self.reference_text = """[계약 조항]
        제1조 (목적): 위 부동산의 임대차에 대하여 합의에 따라 임차인은 임대인에게 임차보증금 및 차임을 아래와 같이 지급하기로 한다.
        제2조 (존속기간): 임대인은 위 부동산을 임대차 목적대로 사용할 수 있는 상태로 임차인에게 인도하며, 임대차 기간은 인도일로부터 정해진 기간까지로 한다.
        제3조 (용도변경 및 전대 등): 임차인은 임대인의 동의 없이 위 부동산의 용도나 구조를 변경하거나 전대, 임차권 양도 또는 담보제공을 하지 못하며 임대차 목적 이외의 용도로 사용할 수 없다.
        제4조 (계약의 해지): 임차인이 계약을 위반하였을 때 임대인은 즉시 본 계약을 해지할 수 있다.
        제5조 (계약의 종료): 임차인은 임대차 계약 종료 시 위 부동산을 원상회복하여 반환하고, 임대인은 보증금에서 손해배상금 등을 제하고 잔액을 반환한다.
        제6조 (계약의 해제): 계약금 반환 또는 포기를 조건으로 계약 해제가 가능하다.
        제7조 (채무불이행과 손해배상): 계약 내용을 이행하지 않을 경우 서면으로 최고 후 계약 해제 및 손해배상 청구가 가능하다.
        제8조 (중개보수): 계약과 동시에 쌍방이 중개보수를 지급하며, 계약 무효 등에도 보수는 지급한다.
        제9조 (확인설명서 교부): 개업공인중개사는 계약 시 설명서 및 증서를 교부해야 한다.

        [특약사항 예시]

        - 임차인은 현장확인 후 원상복구에 동의한다.
        - 관리비는 별도이며, 공과금은 임차인이 부담한다.
        - 임대인은 계약 후 잔금 전까지 권리변동을 하지 않는다.
        - 애완동물 사육은 금지된다.
        """

    def assess_legal_risk(self, clause):
        system_prompt = (
            "당신은 대한민국 부동산 임대차 계약서 분석 전문가입니다. 아래의 계약 조항 또는 특약사항의 법적 위험도를 평가하세요. "
            "다음 조건을 반드시 지켜야 합니다:\n"
            "1. 일반적으로 널리 사용되는 표준 임대차계약서에 포함된 조항일 경우, 위험 점수는 반드시 0으로 평가하세요.\n"
            "2. 조항이 표준 계약서에 없어도, 의미가 같고 표현만 다를 경우에도 동일한 표준 조항으로 간주해야 합니다.\n"
            "3. 숫자나 날짜, 띄어쓰기, 문장 순서가 조금 달라도 내용이 같으면 같은 조항으로 취급해야 합니다.\n"
            "4. 아래의 '표준 임대차계약서 참고 내용'을 반드시 비교 기준으로 활용하고, 의미 기반 비교를 하세요.\n"
            "\n"
            "출력 형식: '위험 점수: [0~10 사이의 숫자], 위험 수준: [안전/주의/불리]'\n"
            "절대로 형식에서 벗어난 말을 하지 마세요."
        )

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"[표준 임대차계약서 참고 내용]\n{self.reference_text}\n\n[조항 또는 특약사항]\n{clause['내용']}"}
            ],
            temperature=0.0
        )

        result = response.choices[0].message.content.strip()
        score = self.parse_response(result)

        level = self.classify_level(score)

        return {
            "score": score,
            "level": level,
            "factors": {}
        }

    def parse_response(self, response):
        try:
            score_match = re.search(r"위험\s*점수\s*[:：]?\s*([0-9]+(?:\.[0-9]+)?)", response)
            if score_match:
                return float(score_match.group(1))
            else:
                print(f"[⚠️ 파싱 실패] 응답 형식이 예상과 다름: {response}")
                return 0.0
        except Exception as e:
            print(f"[❌ 예외 발생] 응답 파싱 오류: {e}")
            return 0.0

    def classify_level(self, score):
        if score >= 8.0:
            return "불리"
        elif score >= 4.0:
            return "주의"
        else:
            return "안전"

    def assess_contract(self, contract_data):
        categorized_clauses = {"안전": [], "주의": [], "불리": []}

        for clause in contract_data["계약"]:
            risk_assessment = self.assess_legal_risk(clause)
            clause["위험도"] = risk_assessment
            categorized_clauses[risk_assessment["level"]].append(clause)

        for i, special in enumerate(contract_data["특약사항"]):
            risk_assessment = self.assess_legal_risk({"내용": special})
            contract_data["특약사항"][i] = {
                "내용": special,
                "위험도": risk_assessment
            }
            categorized_clauses[risk_assessment["level"]].append(contract_data["특약사항"][i])

        return {
            "contract_data": contract_data,
            "categorized_clauses": categorized_clauses
        }