import boto3
import time
import random
from botocore.exceptions import ClientError
from jose import jwt, JWTError
from datetime import timedelta

from app.core.config import settings
from app.core.security import create_access_token

# DynamoDB 리소스 연결 (Lambda 실행 환경의 IAM 권한 사용)
dynamodb = boto3.resource('dynamodb', region_name=settings.AWS_REGION)
table = dynamodb.Table(settings.DYNAMODB_TABLE_VERIFICATION)

def generate_verification_code() -> str:
    """6자리 숫자 코드 생성"""
    return str(random.randint(100000, 999999))

def create_verification_code(email: str) -> str:
    """
    인증 코드를 생성하여 DynamoDB에 저장(TTL 5분)하고 반환합니다.
    실패 시 None을 반환합니다.
    """
    code = generate_verification_code()
    # 현재 시간(초) + 5분 (300초)
    expiration_time = int(time.time()) + 300

    try:
        table.put_item(
            Item={
                'email': email,    # Partition Key
                'code': code,
                'ttl': expiration_time
            }
        )
        return code
    except ClientError as e:
        print(f"[DynamoDB Error] {str(e)}")
        return None

def verify_code(email: str, code: str):
    """
    사용자가 입력한 코드가 DynamoDB의 값과 일치하는지 확인합니다.

    Returns:
        str: 성공 시 발급된 '회원가입용 토큰'
        "EXPIRED": 코드가 없거나 만료됨
        "INVALID": 코드가 일치하지 않음
        None: DB 에러 등 기타 오류
    """
    try:
        response = table.get_item(Key={'email': email})
        item = response.get('Item')

        if not item:
            return "EXPIRED"  # 데이터 없음 (만료되었거나 요청 안 함)

        # 코드 일치 여부 확인
        if item['code'] == code:
            # 인증 성공! -> 회원가입용 임시 토큰(10분 유효) 발급
            token_data = {"sub": email, "type": "verification_complete"}
            verify_token = create_access_token(
                data=token_data,
                expires_delta=timedelta(minutes=10)
            )

            table.delete_item(Key={'email': email})

            return verify_token
        else:
            return "INVALID" # 코드 불일치

    except ClientError as e:
        print(f"[DynamoDB Error] {str(e)}")
        return None

def validate_signup_token(token: str, input_email: str) -> str:
    """
    회원가입 요청 시 제출된 토큰을 검증합니다.

    Returns:
        "SUCCESS": 검증 성공
        "INVALID_TOKEN": 토큰 형식 오류 또는 만료
        "WRONG_TYPE": 토큰 타입 불일치 (로그인 토큰 등을 넣었을 경우)
        "EMAIL_MISMATCH": 토큰 발급 이메일과 가입 이메일 불일치
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )

        token_email: str = payload.get("sub")
        token_type: str = payload.get("type")

        if token_type != "verification_complete":
            return "WRONG_TYPE"

        if token_email != input_email:
            return "EMAIL_MISMATCH"

        return "SUCCESS"

    except JWTError:
        return "INVALID_TOKEN"
