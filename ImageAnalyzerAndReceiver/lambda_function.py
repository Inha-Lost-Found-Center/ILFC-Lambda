import json
import base64
import boto3
import re

bedrock = boto3.client('bedrock-runtime', region_name='us-west-2')


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


def analyze_image_with_bedrock(image_data):
    """Claude Vision으로 이미지 분석하여 구조화된 데이터 반환"""
    image_base64 = base64.b64encode(image_data).decode('ascii')

    # 구조화된 출력을 위한 프롬프트
    prompt = """이미지를 분석하고 다음 정보를 정확한 JSON 형식으로 제공해주세요.


1. 이미지에 있는 물체의 카테고리를 식별하세요 (예: 지갑, 카드, 학생증, 마우스, 키보드, 가방, 시계 등)
2. 브랜드를 식별할 수 있다면 브랜드명을 제공하세요
3. 브랜드를 식별할 수 없다면 "알 수 없음"으로 표시하세요
4. 반드시 아래 JSON 형식으로만 응답하세요


출력 형식
{
  "category": "물체의 카테고리",
  "brand": "브랜드명 또는 '알 수 없음'",
  "description": "물체에 대한 간단한 설명"
}

출력 예시 1:
입력: 로지텍 마우스 이미지
출력:
{
  "category": "마우스",
  "brand": "로지텍",
  "description": "무선 게이밍 마우스"
}

출력 예시 2:
입력: 브랜드가 보이지 않는 지갑 이미지
출력:
{
  "category": "지갑",
  "brand": "알 수 없음",
  "description": "가죽 장지갑"
}

출력 예시 3:
입력: 보테가 베네타 지갑 이미지
출력:
{
  "category": "지갑",
  "brand": "보테가 베네타",
  "description": "인트레치아토 위빙 패턴의 가죽 카드지갑"
}

이제 제공된 이미지를 분석하고 JSON 형식으로만 응답해주세요. 다른 설명은 포함하지 마세요."""

    # Bedrock API 요청 바디
    body = json.dumps(
        {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1000,
            "temperature": 0,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
                                "data": image_base64
                            }
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ]
        }
        ,ensure_ascii=False
    )

    # bedrock 호출
    response = bedrock.invoke_model(
        modelId="anthropic.claude-3-sonnet-20240229-v1:0",
        body=body,
        contentType='application/json',
        accept='application/json'
    )

    # 응답 파싱
    response_body = json.loads(response['body'].read())
    result_text = response_body['content'][0]['text']

    # JSON 파싱 (응답에서 JSON 부분만 추출)
    try:
        # Claude가 JSON만 반환하도록 했지만, 혹시 추가 텍스트가 있을 경우 처리
        result_json = json.loads(result_text)
    except json.JSONDecodeError:
        # JSON 파싱 실패 시, 텍스트에서 JSON 부분만 추출
        json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
        if json_match:
            result_json = json.loads(json_match.group())
        else:
            result_json = {
                "category": "알 수 없음",
                "brand": "알 수 없음",
                "description": result_text
            }

    return result_json
