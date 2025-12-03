import json
import base64
import requests
from analyze_image import analyze_image_with_bedrock
from send_image import upload_image

def lambda_handler(event, context):
    try:
        # API Gateway에서 이미지 데이터 추출
        body = event.get('body', '')

        if not body:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'body가 비어있습니다'})
            }

        # base64 디코딩
        if event.get('isBase64Encoded', False):
            image_data = base64.b64decode(body)
        else:
            image_data = base64.b64decode(body)

        # Bedrock으로 이미지 분석
        analyze_result = analyze_image_with_bedrock(image_data)

        # # S3에 이미지 저장
        file_url = upload_image(image_data)

        # 이미지 저장용 서버로 API 호출
        api_url = "https://vwfopg9nxh.execute-api.us-west-2.amazonaws.com/v1/images/registry"
        payload = {
            "file_url": file_url,
            "analysis_result": analyze_result
        }
        headers = {
            "Content-Type": "application/json"
        }

        response = requests.post(api_url, json=payload, headers=headers)

        # 응답 데이터(JSON) 파싱
        data = response.json()
        category = data.get('category')
        locker_number = data.get('locker_number')

        # API 응답값 세팅
        response = {
            "category" : category,
            "locker_number" : locker_number,
            "image_url" : file_url
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


