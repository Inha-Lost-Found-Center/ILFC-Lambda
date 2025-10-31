import json

def lambda_handler(event, context):

    print("Lambda 함수가 실행되었습니다!")
    print(f"Received event: {event}")

    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }

#
