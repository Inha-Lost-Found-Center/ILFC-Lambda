import uuid
import boto3
import json

# S3 설정
S3_BUCKET = 'inha-capstone-14-s3'
s3_client = boto3.client('s3')

"""이미지를 S3에 저장하고 URL 반환"""


def upload_image(image_data):
    file_name = str(uuid.uuid4()) + ".jpg"

    s3_client.put_object(
        Bucket=S3_BUCKET,
        Key=file_name,
        Body=image_data,
        ContentType='image/jpeg'
    )

    file_url = f"https://{S3_BUCKET}.s3.amazonaws.com/{file_name}"

    return file_url


# SQS 설정
SQS_QUEUE_URL = 'https://sqs.us-west-2.amazonaws.com/327784329358/inha-capstone-14-ImageSqs'
sqs_client = boto3.client('sqs', region_name='us-west-2')


def send_sqs_message(file_url, analysis_result):
    message_id = str(uuid.uuid4())  # 고유 메시지 ID 생성

    sqs_data = json.dumps(
        {
            "message_id": message_id,
            "file_url": file_url,
            "analysis_result": analysis_result
        }
    )

    response = sqs_client.send_message(
        QueueUrl=SQS_QUEUE_URL,
        MessageBody=sqs_data
    )

    return response['MessageId']
