import pandas as pd
import pymysql

# 엑셀 파일을 pandas로 읽기
file_path = 'papers/paper_inf.xlsx'
df = pd.read_excel(file_path)

# MySQL 데이터베이스 연결
conn = pymysql.connect(
    host='localhost',
    user='root',
    password='1234'
)

cursor = conn.cursor()
cursor.execute("CREATE DATABASE IF NOT EXISTS papers")
conn.select_db('papers')

# 테이블이 없다면 테이블 생성 (엑셀 컬럼에 맞는 테이블 구조로 생성)
create_table_query = """
CREATE TABLE IF NOT EXISTS papers (
    paper_id INT PRIMARY KEY,
    title VARCHAR(255),
    publications VARCHAR(255),
    date INT,
    h5 INT,
    citations INT,
    keyword TEXT,
    index_term TEXT,
    file_path VARCHAR(255)
)
"""
cursor.execute(create_table_query)
print(cursor.execute("SELECT * FROM papers"))
conn.commit()
cursor.close()
conn.close()