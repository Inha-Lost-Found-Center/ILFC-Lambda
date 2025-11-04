import json
import boto3
import base64
from datetime import datetime
import os
from insert_item import insert_lost_item


def lambda_handler(event, context):
    try:
        # SQS에서 받은 메시지 처리
        for record in event['Records']:  # 여러 메시지 처리 가능
            sqs_message = json.loads(record['body'])

            ''' SQS 메시지 구조
             {
                 "message_id": "a1b2c3",
                 "file_url": "0f23e3a3-5165-4204-9c5a-fa626e51d029.jpg",
                 "analysis_result": {
                     "category": "지갑",
                     "brand": "애플",
                     "description": "카드지갑입니다."
                 }
             }
            '''

            # DB에 데이터 저장
            analysis_result = sqs_message['analysis_result']
            file_url = sqs_message['file_url']
            record_id = insert_lost_item(
                file_url=file_url,
                category=analysis_result['category'],
                description=analysis_result['description']
            )

        return {
            'statusCode': 200,
            'body': json.dumps('처리 완료')
        }

    except Exception as e:
        print(f"에러 발생: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps(f'처리 실패: {str(e)}')
        }

