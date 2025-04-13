import os
import time
import uuid
import boto3
import datetime
import logging
import argparse

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

logging_sw = True

def parse_arguments():
    parser = argparse.ArgumentParser(description="PDF 공고 크롤러 설정")
    parser.add_argument(
        "--aws-region",
        type=str,
        default=os.environ.get("AWS_REGION", "us-east-1"),
        help="AWS 리전 어떤걸로? 기본 : us-east-1"
    )
    parser.add_argument(
        "--ddb-table-name",
        type=str,
        default=os.environ.get("DDB_TABLE_NAME", "minerva-1-pdf-info-table"),
        help="DynamoDB 테이블 쓸거 "
    )
    parser.add_argument(
        "--s3-bucket-name",
        type=str,
        default=os.environ.get("S3_BUCKET_NAME", "minerva-1-pdf-bucket"),
        help="S3 버킷 이름"
    )
    parser.add_argument(
        "--download-dir",
        type=str,
        default="/home/ec2-user/download/",
        help="다운로드할 디렉토리 경로"
    )
    parser.add_argument(
        "--notice-num",
        type=int,
        default=1,
        help="가져올 Notice 개수"
    )
    return parser.parse_args()


args = parse_arguments()

AWS_REGION    = args.aws_region
DDB_TABLE_NAME = args.ddb_table_name
S3_BUCKET_NAME = args.s3_bucket_name
DOWNLOAD_DIR  = os.path.abspath(args.download_dir)
notice_num = args.notice_num

if logging_sw:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    logger = logging.getLogger(__name__)

dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
ddb_table = dynamodb.Table(DDB_TABLE_NAME)
s3 = boto3.client('s3')


os.makedirs(DOWNLOAD_DIR, exist_ok=True) # 크롬 다운로드 링크


def configure_driver(download_dir: str) -> webdriver.Chrome:
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
    return driver


def open_landing_page(driver: webdriver.Chrome):
    base_url = "https://apply.lh.or.kr/lhapply/apply/sc/list.do?mi=1312"
    driver.get(base_url)
    if logging_sw:
        logger.info("랜딩 페이지 열리는거 확인 : %s", base_url)
    time.sleep(7)

def select_options(driver: webdriver.Chrome):
    wait = WebDriverWait(driver, 10)
    # 임대주택 선택
    cal_select = Select(wait.until(EC.presence_of_element_located((By.ID, "calSrchType"))))
    cal_select.select_by_value("01")
    time.sleep(1)
    
    # 접수 항목 선택
    recv_select = Select(wait.until(EC.presence_of_element_located((By.ID, "srchPanSs"))))
    recv_select.select_by_visible_text("접수")
    time.sleep(1)
    
    # 검색 버튼 클릭
    search_button = wait.until(EC.element_to_be_clickable((By.ID, "btnSah")))
    search_button.click()
    if logging_sw:
        logger.info("검색 버튼 클릭됨.")
    time.sleep(5)

# 오늘 날짜 기반 셀렉터 생성
def click_today_notice(driver: webdriver.Chrome) -> list:
    wait = WebDriverWait(driver, 10)
    today = datetime.datetime.today()
    year = str(today.year)[2:]
    month = f"{today.month:02d}"
    day = f"{today.day:02d}"
    selector_prefix = f"#\\32 0{year}{month}{day}"
    calendar_selector = f"{selector_prefix} > a.btn_more.hash"
    wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, calendar_selector))).click()
    if logging_sw:
        logger.info("오늘 날짜 공고 버튼 클릭됨.")
    time.sleep(2)
    popup = wait.until(EC.presence_of_element_located((By.ID, 'popSchleMore')))
    notice_items = popup.find_elements(By.CSS_SELECTOR, "li")
    if logging_sw:
        logger.info("오늘 날짜 공고 수: %d", len(notice_items))
    return notice_items

# 공고 파일인 pdf 파일 다운로드 
def wait_for_file_download(expected_filename: str, download_dir: str, timeout: int = 20):
    elapsed = 0
    file_path = os.path.join(download_dir, expected_filename)
    while elapsed < timeout:
        if os.path.exists(file_path):
            logger.info("파일 다운로드 확인: %s", file_path)
            return file_path
        time.sleep(1)
        elapsed += 1
    if logging_sw:
        logger.error("파일 다운로드 시간 초과: %s", expected_filename)
    return ""

# 팝업 안에서 공고 리스트 긁기
def process_notice_item(driver: webdriver.Chrome, notice_item, wait: WebDriverWait):
    try:
        a_tag = notice_item.find_element(By.CSS_SELECTOR, "dl > dt > a")
        href = a_tag.get_attribute("href")
        title = a_tag.text
        if logging_sw:
            logger.info("공고 처리 시작: %s", title)
        
        # 새 탭에서 공고 페이지 열기
        driver.execute_script("window.open(arguments[0]);", href)
        driver.switch_to.window(driver.window_handles[-1])
        time.sleep(6)
        
        # "공고"와 ".pdf"가 포함된 링크 찾기
        pdf_links = driver.find_elements(By.CSS_SELECTOR, "a")
        print("pdf_links", pdf_links)
        print("notice_num", notice_num)
        for link in pdf_links[1:notice_num+1]:
            print(1111111)
            pdf_link_text = link.text.strip()
            
            print("pdf_link_text", pdf_link_text)
            if "공고" in pdf_link_text and ".pdf" in pdf_link_text:
                print("pdf_link_text", pdf_link_text)
                if logging_sw:
                    logger.info("PDF 링크 발견: %s", pdf_link_text)
                link.click()
                time.sleep(5)
                
                # 다운로드된 파일 이름은 링크 텍스트와 동일하다고 가정
                downloaded_path = wait_for_file_download(pdf_link_text, DOWNLOAD_DIR, timeout=20)
                if not downloaded_path:
                    continue
                
                # 파일 이름 UUID 기반으로 변경
                new_pdf_name = f"{uuid.uuid4()}.pdf"
                new_pdf_path = os.path.join(DOWNLOAD_DIR, new_pdf_name)
                os.rename(downloaded_path, new_pdf_path)
                if logging_sw:
                    logger.info("파일 이름 변경 성공 : %s", new_pdf_path)
                
                # S3 업로드
                s3.upload_file(new_pdf_path, S3_BUCKET_NAME, new_pdf_name)
                if logging_sw:
                    logger.info("S3 업로드 완료 성공 : s3://%s/%s", S3_BUCKET_NAME, new_pdf_name)
                
                # DynamoDB 업데이트
                ddb_table.put_item(Item={
                    "id": new_pdf_name,
                    "notice_url": href,
                    "notice_name": title,
                    "notice_s3": f's3://{S3_BUCKET_NAME}/{new_pdf_name}'
                })
                if logging_sw:
                    logger.info("DynamoDB에 레코드 등록 성공 : %s", new_pdf_name)
        
        # 새 탭 닫고 원래 창으로 전환
        driver.close()
        driver.switch_to.window(driver.window_handles[0])
        time.sleep(1)
    except Exception as e:
        logger.exception("공고 처리 중 오류: %s", e)


def main():
    driver = configure_driver(DOWNLOAD_DIR)
    wait_driver = WebDriverWait(driver, 10)
    try:
        open_landing_page(driver)
        select_options(driver)
        notice_items = click_today_notice(driver)
        if not notice_items:
            logger.info("오늘 날짜의 공고가 없습니다.")
            return

        # 예시로 첫 번째 공고만 처리 (원하는 경우 루프 범위 조정)
        process_notice_item(driver, notice_items[1], wait_driver)
    except Exception as e:
        logger.exception("메인 프로세스 오류: %s", e)
    finally:
        driver.quit()
        if logging_sw:
            logger.info("드라이버 종료됨.")

if __name__ == "__main__":
    main()