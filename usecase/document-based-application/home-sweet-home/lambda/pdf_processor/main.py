import json
import os
import base64
import boto3
import openai

# 환경 변수 설정 (Lambda 콘솔에서 환경 변수로 지정하는 것이 좋습니다)
UPSTAGE_API_KEY = os.environ.get("UPSTAGE_API_KEY")
UPSTAGE_API_URL = os.environ.get("UPSTAGE_API_URL")
MIME_TYPE = "application/pdf"
DDB_TABLE_NAME = os.environ.get("DDB_TABLE_NAME")

# OpenAI 라이브러리 설정 (업스테이지 엔드포인트 사용)
openai.api_key = UPSTAGE_API_KEY
openai.api_base = UPSTAGE_API_URL

# boto3 S3 클라이언트 생성
s3_client = boto3.client("s3")
ddb = boto3.resource("dynamodb")
table = ddb.Table(DDB_TABLE_NAME)

def encode_to_base64(file_bytes):
    """파일 바이트 데이터를 Base64 문자열로 인코딩"""
    return base64.b64encode(file_bytes).decode("utf-8")

def lambda_handler(event, context):
    try:
        # S3 이벤트에서 버킷과 객체 키 추출
        bucket = event["Records"][0]["s3"]["bucket"]["name"]
        key = event["Records"][0]["s3"]["object"]["key"]
        print(f"Processing file from S3: s3://{bucket}/{key}")
        
        # S3에서 PDF 파일 다운로드
        response = s3_client.get_object(Bucket=bucket, Key=key)
        pdf_bytes = response["Body"].read()
        
        # PDF 데이터를 Base64로 인코딩
        base64_encoded = encode_to_base64(pdf_bytes)
        
        # Upstage API 호출
        extraction_response = openai.ChatCompletion.create(
            model="information-extract",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",  # 실제 PDF를 전달하지만 MIME_TYPE이 application/pdf로 지정되어 있음
                            "image_url": {"url": f"data:{MIME_TYPE};base64,{base64_encoded}"}
                        }
                    ]
                }
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "document_schema",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "announcementDate": {
                                "type": "string",
                                "description": "The date of the announcement for the housing application."
                            },
                            "location": {
                                "type": "string",
                                "description": "The location of the housing project in Korean."
                            },
                            "developer": {
                                "type": "string",
                                "description": "The company responsible for the development of the housing project." #json에는 미포함
                            },
                            "managementCompany": {
                                "type": "string",
                                "description": "The company managing the assets of the housing project." #json에는 미포함
                            },
                            "totalUnits": {
                                "type": "integer",
                                "description": "The total number of housing units available for application." #json에는 미포함
                            },
                            "eligibilityCriteria": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "category": {
                                            "type": "string",
                                            "description": "The category of applicants eligible for the housing."
                                        },
                                        "requirements": {
                                            "type": "string",
                                            "description": "Specific requirements for the eligibility category."
                                        }
                                    },
                                    "required": [
                                        "category",
                                        "requirements"
                                    ]
                                }
                            },
                            "applicationSchedule": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "applicationStart": {
                                            "type": "string",
                                            "description": "The start date for applications."
                                        },
                                        "applicationEnd": {
                                            "type": "string",
                                            "description": "The end date for applications."
                                        },
                                        "resultAnnouncement": {
                                            "type": "string",
                                            "description": "The date when the results of the application will be announced."
                                        }
                                    },
                                    "required": [
                                        "applicationStart",
                                        "applicationEnd",
                                        "resultAnnouncement"
                                    ]
                                }
                            },
                            "rentalConditions": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "netLeasableArea": {
                                            "type": "number",
                                            "description": "net residential area exclusively available to the occupant, excluding any shared or common areas"
                                        },
                                        "deposit": {
                                            "type": "number",
                                            "description": "The rental deposit amount."
                                        },
                                        "monthlyRent": {
                                            "type": "number",
                                            "description": "The monthly rent amount."
                                        }
                                    },
                                    "required": [
                                        "netLeasableArea",
                                        "deposit",
                                        "monthlyRent"
                                    ]
                                }
                            }
                        },
                        "required": [
                            "announcementDate",
                            "location",
                            "developer",
                            "managementCompany",
                            "totalUnits",
                            "eligibilityCriteria",
                            "applicationSchedule",
                            "rentalConditions"
                        ]
                    }
                }
            }
        )
        

        # API 응답 결과 파싱
        result = extraction_response.choices[0].message.content
        print("Extracted Schema:", result)
        schema = json.loads(result)

        # API 응답이 이미 dict 형태라고 가정 (필요시 json.loads()로 변환)
        # schema = result.get("schema", {})

        # 기본 정보 추출
        announcementDate = schema.get("announcementDate")
        buildingLocation = schema.get("location")
        totalUnits = schema.get("totalUnits")

        # eligibilityCriteria: "대학생 계층" -> "University", "청년 계층" -> "Young"
        eligibility_list = schema.get("eligibilityCriteria", [])
        mapped_eligibility = []
        for criterion in eligibility_list:
            category = criterion.get("category", "")
            if category == "대학생 계층":
                mapped_eligibility.append("University")
            elif category == "청년 계층":
                mapped_eligibility.append("Young")

        # applicationSchedule 배열 처리: 첫 번째 항목에서 값 추출
        app_schedule = schema.get("applicationSchedule", [])
        if app_schedule and isinstance(app_schedule, list):
            first_schedule = app_schedule[0]
            applicationStart = first_schedule.get("applicationStart")
            applicationEnd = first_schedule.get("applicationEnd")
            resultAnnouncement = first_schedule.get("resultAnnouncement")
        else:
            applicationStart = applicationEnd = resultAnnouncement = None

        # rentalConditions 그대로 사용
        rentalConditions = schema.get("rentalConditions")
        rentalConditions_temp = []
        rentalCondition_ = {}
        for rentalCondition in rentalConditions:
            rentalCondition_['net_leasable_area'] = int(rentalCondition['netLeasableArea'])
            rentalCondition_['deposit'] = rentalCondition['deposit']
            rentalCondition_['monthly_rent'] = rentalCondition['monthlyRent']
            rentalConditions_temp.append(rentalCondition_)
        
        splied_location = buildingLocation.split(" ")
        if splied_location[0][0:2] in ["부산", "대구", "인천", "광주", "대전", "울산", "서울"]:
            buildingLocation = splied_location[0][0:2]
        else:
            buildingLocation = splied_location[1][0:2]
        
        

        # 목표 포맷에 맞게 재구성
        formatted_result = {
            "announcementDate": announcementDate,
            "buildingLocation": buildingLocation,
            "totalUnits": totalUnits,
            "eligibilityCriteria": mapped_eligibility,
            "applicationStart": applicationStart,
            "applicationEnd": applicationEnd,
            "resultAnnouncement": resultAnnouncement,
            "rentalConditions": rentalConditions_temp
        }
        print("Formatted Result:", json.dumps(formatted_result, ensure_ascii=False, indent=4))

        # DynamoDB 업데이트를 위한 update_key_values 구성
        update_key_values = {
            "announcement_date": formatted_result["announcementDate"],
            "building_location": formatted_result["buildingLocation"],
            "total_units": formatted_result["totalUnits"],
            "eligibility_criteria": formatted_result["eligibilityCriteria"],
            "application_start": formatted_result["applicationStart"],
            "application_end": formatted_result["applicationEnd"],
            "result_announcement": formatted_result["resultAnnouncement"],
            "rental_conditions": formatted_result["rentalConditions"],
            "monthly_income_limit" : {"1" : 4317797, "2" : 6024703, "3" : 7626973},
        }

        # 업데이트 표현식 및 ExpressionAttributeValues 동적 생성
        update_expression = "SET " + ", ".join([f"{k} = :{k}" for k in update_key_values])
        expression_values = {f":{k}": v for k, v in update_key_values.items()}

        # DynamoDB 업데이트 실행
        update_response = table.update_item(
            Key={"id": key},
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_values
        )
        print("DynamoDB Update Response:", update_response)

        
        return {
            "statusCode": 200,
            "body": json.dumps(result)
        }
    
    except Exception as e:
        print("Error:", str(e))
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }

