import json
import pathlib

def normalize_city(name):
    """
    도시 이름을 정규화합니다.
    만약 이름이 아래 접미사로 끝나면 접미사를 제거하고 "시"를 덧붙입니다.
      - "특별자치시"
      - "광역시"
      - "특별시"
    예)
      "인천광역시" -> "인천시"
      "세종특별자치시" -> "세종시"
      "서울특별시" -> "서울시"
    """
    for suffix in ["특별자치시", "광역시", "특별시"]:
        if name.endswith(suffix):
            return name[:-len(suffix)] + "시"
    return name
# 기존 JSON 파일에서 도시 리스트 읽기 (파일 경로는 필요에 맞게 수정)
input_file = "filtered_cities.json"
data = json.loads(pathlib.Path(input_file).read_text(encoding="utf-8"))

# 각 항목에 대해 정규화 적용
normalized_set = set()
for city in data:
    normalized_name = normalize_city(city)
    normalized_set.add(normalized_name)

# 중복 제거 후 정렬된 리스트로 변환
normalized_list = sorted(list(normalized_set))

# 결과 JSON 파일로 저장
output_file = "normalized_cities.json"
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(normalized_list, f, ensure_ascii=False, indent=2)

print("정규화된 도시 이름:")
for name in normalized_list:
    print(name)
print(f"\n결과 파일: {pathlib.Path(output_file).absolute()}")