import requests

url = 'http://localhost:5000/recommend'  # 서버 주소에 맞게 수정
data = {'prompt': 'I want to submit to CVPR'}

response = requests.post(url, json=data)

if response.status_code == 200:
    result = response.json()
    file_names = result.get("files", [])
    if file_names:
        print("추천된 논문 파일 목록:")
        for name in file_names:
            print("-", name)
    else:
        print("추천된 논문이 없습니다.")
else:
    print("에러 발생:", response.status_code, response.text)
