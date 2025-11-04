import json
import base64
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
        analyze_result = analyze_image_with_bedrock(image_data)

        response = {
            "category": analyze_result.get("category")
        }

        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps(response)
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': str(e)})
        }


