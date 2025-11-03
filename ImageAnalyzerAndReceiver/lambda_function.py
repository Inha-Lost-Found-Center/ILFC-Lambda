import json
import base64


def lambda_handler(event, context):
    body = event.get('body', '')

    if not body:
        return {
            'statusCode': 400,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': 'body가 비어있습니다'})
        }

    # base64 디코딩
    if event.get('isBase64Encoded', False):
        image_data = base64.b64decode(body)
    else:
        image_data = body if isinstance(body, bytes) else body.encode('utf-8')

    # 파일 크기 정보만 리턴
    metadata = {
        'file_size_bytes': len(image_data),
        'file_size_kb': round(len(image_data) / 1024, 2),
        'file_size_mb': round(len(image_data) / (1024 * 1024), 2)
    }

    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps(metadata)
    }
