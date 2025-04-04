import json
import re

def cleanhtml(raw_html):
  cleanr = re.compile('<.*?>')
  cleantext = re.sub(cleanr, '', raw_html)
  return cleantext

def extract_all_content(file_path):
    # JSON 파일 읽기
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)

    # 본문 내용을 저장할 리스트
    extracted_texts = []

    # 재귀적으로 content 키를 탐색하여 본문 내용 추출
    def find_content(node):
        if isinstance(node, dict):
            # content 키가 있고 text 필드가 있는 경우 추출
            if 'content' in node and isinstance(node['content'], dict) and 'html' in node['content']:
                extracted_texts.append(cleanhtml(node['content']['html']))
            # 모든 하위 항목 탐색
            for key, value in node.items():
                find_content(value)
        elif isinstance(node, list):
            # 리스트 내부의 각 항목 탐색
            for item in node:
                find_content(item)

    # 탐색 시작
    find_content(data)

    return extracted_texts

def get_content(file_path):
    # 모든 본문 내용 추출
    all_contents = extract_all_content(file_path)
    contents = []
    # 결과 출력
    for idx, content in enumerate(all_contents, start=1):
        contents.append(content)
    return("\n".join(contents))
