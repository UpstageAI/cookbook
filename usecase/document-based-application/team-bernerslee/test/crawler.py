import argparse
import boto3
import uuid

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import datetime
import os
import time


aws_region = 'us-east-1'

# DDB
dynamodb = boto3.resource('dynamodb',
    region_name=aws_region
)
table = dynamodb.Table('minerva-1-pdf-info-table')

# S3
bucket_name = 'minerva-1-pdf-bucket'
s3 = boto3.client('s3')



download_dir = os.path.abspath("/home/ec2-user/download/")
os.makedirs(download_dir, exist_ok=True)

options = webdriver.ChromeOptions()
options.add_argument('--start-maximized')
options.add_argument('--headless')

prefs = {
    "download.default_directory": download_dir,
    "download.prompt_for_download": False,
    "download.directory_upgrade": True,
    "safebrowsing.enabled": True
}
options.add_experimental_option("prefs", prefs)

driver = webdriver.Chrome(options=options)
wait = WebDriverWait(driver, 10)

# 랜딩 페이지 캘린더 페이지로 이동
driver.get("https://apply.lh.or.kr/lhapply/apply/sc/list.do?mi=1312")
time.sleep(7)

# 임대만 선택
select_cal = Select(driver.find_element(By.ID, "calSrchType"))
select_cal.select_by_value("01")  # 임대주택
time.sleep(1)

# 접수 하는것만 선택
select_recv = Select(driver.find_element(By.ID, "srchPanSs"))
select_recv.select_by_visible_text("접수")
time.sleep(1)

# 검색 버튼 클릭
driver.find_element(By.ID, "btnSah").click()
time.sleep(5)

# 오늘 날짜 기반 셀렉터 생성
today = datetime.datetime.today()
year = str(today.year)[2:]
month = f"{today.month:02d}"
day = f"{today.day:02d}"
selector_prefix = f"#\\32 0{year}{month}{day}"
calendar_selector = f"{selector_prefix} > a.btn_more.hash"

# 오늘 날짜의 버튼 클릭
wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, calendar_selector))).click()
time.sleep(2)

# 팝업 안에서 공고 리스트 긁기
popup = wait.until(EC.presence_of_element_located((By.ID, 'popSchleMore')))
notice_items = popup.find_elements(By.CSS_SELECTOR, "li")

# for idx in range(1, len(notice_items)+1):
for idx in range(1, 2):
    try:
        a_tag = notice_items[idx].find_element(By.CSS_SELECTOR, "dl > dt > a")
        href = a_tag.get_attribute("href")
        title = a_tag.text

        # 직접 링크 클릭이 아니라, 링크를 새로 여는 방식으로 처리 (팝업 클릭 안 함)
        driver.execute_script("window.open(arguments[0]);", href)
        driver.switch_to.window(driver.window_handles[-1])

        # 페이지 로딩 대기
        time.sleep(6)

        # 공고 pdf 다운로드: "공고" + ".pdf" 포함된 a 태그 클릭
        download_links = driver.find_elements(By.CSS_SELECTOR, "a")
        
        
        for link in download_links:
            notice_pdf_name = link.text.strip()
            if "공고" in notice_pdf_name and ".pdf" in notice_pdf_name:
                link.click()
                time.sleep(5)
                pdf_path = os.path.join(download_dir, notice_pdf_name)
        
                my_uuid = uuid.uuid4()
                new_name = f'{my_uuid}.pdf'
                old_path = pdf_path
                new_path = os.path.join(download_dir, new_name)
                os.rename(old_path, new_path)
                print("Updated name", new_path)

                # S3 업로드
                s3.upload_file(new_path, bucket_name, new_name)
                print("Updated S3", f's3://{bucket_name}/{new_name}')
                
                # DDB table 생성
                table.put_item(Item={
                    "id": new_name,
                    "notice_url": href,
                    "notice_name": title,
                    "notice_s3": f's3://{bucket_name}/{new_name}'
                })
                print("Updated DDB", new_name)


        driver.close()
        driver.switch_to.window(driver.window_handles[0])
        time.sleep(1)

    except:
        pass
