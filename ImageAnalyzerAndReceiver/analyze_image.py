import json
import base64
import boto3
import re
from analyze_image import analyze_image_with_bedrock

def lambda_handler(event, context):
    try:
        # 1. API Gateway에서 이미지 데이터 추출
        body = event.get('body', '')

        if not body:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'body가 비어있습니다'})
            }

        # 2. base64 디코딩
        if event.get('isBase64Encoded', False):
            image_data = base64.b64decode(body)
        else:
            image_data = base64.b64decode(body)

        # 3. Bedrock Vision으로 이미지 분석
        result = analyze_image_with_bedrock(image_data)

        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps(result)
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': str(e)})
        }
