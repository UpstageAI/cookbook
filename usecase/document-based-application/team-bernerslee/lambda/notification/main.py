from dataclasses import dataclass, field
from typing import Optional, Dict, List
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
import os
from boto3.dynamodb.types import TypeDeserializer
import boto3

deserializer = TypeDeserializer()
dynamodb_client = boto3.client("dynamodb")
user_info_table_name = "minerva-1-user-info-table"


@dataclass
class UserInfo:
    user_id: str
    email: str
    birth: str  # ISO format (YYYY-MM-DD)
    gender: Optional[str]  # None if "미선택"
    family_size: int
    is_student: bool
    monthly_income: int  # in 만원
    total_assets: int  # in 만원
    own_house: str
    own_car: bool
    saving_count: int
    residence: str  # 시/도
    preferred_area: int  # in ㎡
    max_deposit: int  # in 만원
    budget_monthly: int  # in 만원
    preferred_regions: set[str] = field(default_factory=set)

    @classmethod
    def from_dict(cls, data: dict) -> "UserInfo":

        data = {k: deserializer.deserialize(v) for k, v in data.items()}
        # "미선택" 처리
        gender = data.get("gender")
        if gender == "미선택":
            gender = None

        return cls(
            user_id=data["user_id"],
            email=data["email"],
            birth=data["birth"],
            gender=gender,
            family_size=int(data["family_size"]),
            is_student=bool(data["is_student"]),
            monthly_income=int(data["monthly_income"]),
            total_assets=int(data["total_assets"]),
            own_house=data["own_house"],
            own_car=bool(data["own_car"]),
            saving_count=int(data["saving_count"]),
            residence=data["residence"],
            preferred_area=int(data["preferred_area"]),
            max_deposit=int(data["max_deposit"]),
            budget_monthly=int(data["budget_monthly"]),
            preferred_regions=data.get("preferred_regions", set()),
        )


def calculate_age(birth_str: str) -> int:
    birth_date = datetime.strptime(birth_str, "%Y-%m-%d").date()
    today = datetime.today().date()
    age = (
        today.year
        - birth_date.year
        - ((today.month, today.day) < (birth_date.month, birth_date.day))
    )
    return age


def filter_eligible_users(
    users: list[dict], eligibilities: list[str], rental_conditions: list[dict]
) -> list[UserInfo]:
    filtered_users: list[UserInfo] = []

    for user in users:
        user_info: UserInfo = UserInfo.from_dict(user)
        user_age = calculate_age(user_info.birth)

        # 입주 자격 조건 확인
        if not (
            ("Young" in eligibilities and 19 <= user_age <= 39)
            or ("University" in eligibilities and user_info.is_student)
        ):
            continue

        # 조건에 맞는 임대 조건 확인
        if any(
            cond["deposit"] <= user_info.max_deposit
            and cond["monthly_rent"] <= user_info.budget_monthly
            and cond["net_leasable_area"] >= user_info.preferred_area
            for cond in rental_conditions
        ):
            filtered_users.append(user_info)

    return filtered_users


def lambda_handler(event, context):
    print(event["Records"])
    record = event["Records"][0]

    if record["eventName"] != "MODIFY":
        return {"statusCode": 200, "body": "INSERT 이벤트가 아님"}

    # NewImage 파싱
    new_image = record["dynamodb"]["NewImage"]
    item = {k: deserializer.deserialize(v) for k, v in new_image.items()}

    print(item)
    # 데이터 추출
    # 건물 위치
    location = item.get("building_location")
    notice_name = item.get("notice_name")
    notice_url = item.get("notice_url")
    announcement_id = item.get("id")
    print(f"location {location}")
    # 공급수
    total_units = item.get("total_units")
    # 조건
    eligibilities = item.get("eligibility_criteria", [])
    # 집에 대한 스펙
    rental_conditions = item.get("rental_conditions", [])

    # 지역으로 쿼리
    scan_resp = dynamodb_client.scan(
        TableName=user_info_table_name,
        FilterExpression=("contains(preferred_regions, :location)"),
        ExpressionAttributeValues={
            ":location": {"S": location},
        },
    )
    users = scan_resp.get("Items", [])
    print(f"queried users: {users}")

    # 유저 필터링
    filtered_users = filter_eligible_users(users, eligibilities, rental_conditions)
    print(f"filtered_ users : {filtered_users}")

    if not filtered_users:
        return {"statusCode": 200, "body": "조건에 맞는 유저가 없습니다."}

    # 환경변수 또는 코드 내에 설정 (보안상 환경변수 권장)
    sender_email = "cheongcheongai@gmail.com"
    sender_password = os.environ["EMAIL_PASSWORD"]  # Lambda 환경 변수에 저장

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, sender_password)

            for user in filtered_users:
                chat_url = f"http://ec2-54-144-32-255.compute-1.amazonaws.com:8501/?user_id={user.user_id}&id={announcement_id}"

                body = f"""
                <html>
                  <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px;">
                    <div style="max-width: 600px; margin: auto; background-color: white; padding: 30px; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.1);">
                      <h2 style="color: #333;">New Personalized Housing Announcement Notification</h2>
                      <p style="font-size: 16px; color: #555;">
                        The following housing announcement matches your preferences:
                      </p>
                      <p style="font-size: 18px; color: #000; font-weight: bold;">
                        {notice_name}
                      </p>
                      <div style="margin-top: 30px; text-align: center;">
                        <a href="{notice_url}" style="display: inline-block; padding: 12px 25px; background-color: #2196F3; color: white; text-decoration: none; border-radius: 5px; font-weight: bold; margin-right: 10px;">
                          View Announcement
                        </a>
                        <a href="{chat_url}" style="display: inline-block; padding: 12px 25px; background-color: #4CAF50; color: white; text-decoration: none; border-radius: 5px; font-weight: bold;">
                          Ask AI About This Announcement
                        </a>
                      </div>
                      <p style="font-size: 14px; color: #999; margin-top: 40px;">
                        This email was sent automatically.
                      </p>
                    </div>
                  </body>
                </html>
                """

                msg = MIMEText(body, "html")
                msg["Subject"] = "새로운 맞춤 공고 알림"
                msg["From"] = sender_email
                msg["To"] = user.email
                server.sendmail(sender_email, user.email, msg.as_string())

            # Gmail SMTP 서버에 연결

        return {"statusCode": 200, "body": "이메일 전송 성공"}

    except Exception as e:
        return {"statusCode": 500, "body": f"이메일 전송 실패: {str(e)}"}
