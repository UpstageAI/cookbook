#!/usr/bin/env python3
import csv
import glob
import json
import os
import chardet

def detect_encoding(filepath, num_bytes=10000):
    """파일의 인코딩을 chardet로 감지"""
    with open(filepath, 'rb') as f:
        rawdata = f.read(num_bytes)
    result = chardet.detect(rawdata)
    return result['encoding']

def process_file(filepath, regions):
    """
    CSV 파일에서 '시도명'과 '시군구명' 컬럼의 값을 읽어,
    각 행정구역을 아래의 구조로 저장:
    
    {
      province: {
         "direct": { set of 지역명 },
         "city": { city_name : set( districts ) }
      },
      ...
    }
    
    CSV 헤더 예시:
    법정동코드,시도명,시군구명,읍면동명,리명,순위,생성일자,삭제일자,과거법정동코드
    """
    encoding = detect_encoding(filepath) or "utf-8-sig"
    print(f"{filepath}: detected encoding = {encoding}")
    with open(filepath, "r", encoding=encoding, errors="replace") as f:
        reader = csv.DictReader(f)
        for row in reader:
            province = row.get("시도명", "").strip()
            region = row.get("시군구명", "").strip()  # 예: "수원시권선구", "종로구" 등
            if not (province and region):
                continue

            # 초기화: province가 regions에 없으면 새 객체 생성
            if province not in regions:
                regions[province] = {"direct": set(), "city": {}}

            # 만약 region 문자열에 "시"라는 단어가 포함되어 있고,
            # 그 이후에 추가 문자열이 있다면 (즉, "시"로 끝나지 않으면) 도시+구 분리 시도
            if "시" in region:
                idx = region.find("시")
                city_name = region[:idx+1]  # "수원시" 처럼
                remaining = region[idx+1:].strip()
                # 만약 남은 문자열이 있으면, 도시의 구 단위로 취급
                if remaining:
                    # city 항목 초기화
                    if city_name not in regions[province]["city"]:
                        regions[province]["city"][city_name] = set()
                    regions[province]["city"][city_name].add(remaining)
                else:
                    # 남은 문자열이 없으면, region 전체는 도시명 그대로 취급하여 direct에 추가
                    regions[province]["direct"].add(city_name)
            else:
                # "시"가 없으면, region은 바로 direct 항목에 추가 (예: "종로구", "중구", "강남구" 등)
                regions[province]["direct"].add(region)

# 결과를 저장할 딕셔너리 구조 (키: 시도명)
regions = {}

# 현재 디렉터리에서 .csv 파일 모두 처리
csv_files = glob.glob("*.csv")
print(f"총 {len(csv_files)}개의 파일을 처리합니다.")

for filepath in csv_files:
    print(f"파일 처리중: {filepath}")
    try:
        process_file(filepath, regions)
    except Exception as e:
        print(f"파일 처리 중 에러 발생 ({filepath}): {e}")

# 집합을 리스트로 변환 및 정렬 (각 항목 별)
for province, data in regions.items():
    data["direct"] = sorted(list(data["direct"]))
    for city, district_set in data["city"].items():
        data["city"][city] = sorted(list(district_set))

# 최종 JSON 구조 예:
# {
#    "서울특별시": { "direct": ["종로구", "중구", ...], "city": {} },
#    "경기도": { "direct": ["가평군", "강화군", ...], "city": { "수원시": ["권선구", "시장안구", ...], ... } },
#    ...
# }
output_file = "korea_regions_hierarchical.json"
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(regions, f, ensure_ascii=False, indent=2)

print(f"데이터가 {os.path.abspath(output_file)} 에 저장되었습니다.")