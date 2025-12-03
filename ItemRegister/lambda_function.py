import json
import boto3
import base64
from datetime import datetime
import os
from insert_item import insert_lost_item


def lambda_handler(event, context):
    try:
        # Request Body 값 추출
        body = json.loads(event['body'])
        file_url = body.get('file_url')
        analysis_result = body.get('analysis_result')

        # DB에 데이터 저장
        locker_number = insert_lost_item( # 사물함 번호 리턴
            file_url=file_url,
            category=analysis_result.get('category'),
            description=analysis_result.get('description')
        )

        response = {
            "category" : analysis_result.get('category'),
            "locker_number" : locker_number
        }

        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps(response)
        }

    except Exception as e:
        print(f"에러 발생: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps(f'처리 실패: {str(e)}')
        }

