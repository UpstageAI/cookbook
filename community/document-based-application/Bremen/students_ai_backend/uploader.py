import pandas as pd
import pymysql

# 엑셀 파일을 pandas로 읽기
file_path = 'papers/paper_inf.xlsx'
df = pd.read_excel(file_path)

# MySQL 데이터베이스 연결
conn = pymysql.connect(
    host='localhost',
    user='root',
    password='1234',
    database='papers'
)

cursor = conn.cursor()

# 데이터 삽입
for i, row in df.iterrows():
    # paper_id를 기반으로 파일 경로 설정 (예: '1.pdf', '2.pdf' 형태)
    file_path = f"{row['paper_id']}.pdf"

    print(row)
    # 각 행의 데이터를 MySQL 테이블에 삽입
    insert_query = """INSERT INTO papers (paper_id, title, publications, date, h5, citations, keyword, index_term, file_path) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"""
    cursor.execute(insert_query, (
        row['paper_id'],
        row['Paper_Title'],
        row['Publications'],
        row['Date'],
        row['h5'],
        row['Citations'],
        row['Keyword'],
        row['Index_Term'],
        file_path  # 'paper_id.pdf' 형식으로 저장
    ))

# 커밋 및 연결 종료
conn.commit()
cursor.close()
conn.close()

print("엑셀 데이터가 MySQL 데이터베이스에 삽입되었습니다.")
