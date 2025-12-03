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

