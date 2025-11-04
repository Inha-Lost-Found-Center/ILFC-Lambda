import psycopg2
from datetime import datetime
import os

# RDS 환경 변수
RDS_HOST = os.environ['RDS_HOST']
RDS_DB = os.environ['RDS_DB']
RDS_USER = os.environ['RDS_USER']
RDS_PASSWORD = os.environ['RDS_PASSWORD']
RDS_PORT = int(os.environ['RDS_PORT'])


def insert_lost_item(file_url, category, description):
    """LostItems 테이블에 데이터 저장"""
    # DB 연결
    conn = psycopg2.connect(
        host=RDS_HOST,
        database=RDS_DB,
        user=RDS_USER,
        password=RDS_PASSWORD,
        port=RDS_PORT
    )

    try:
        cursor = conn.cursor()

        # 태그 찾기
        tag_id = 0

        # INSERT 쿼리
        sql = """
        INSERT INTO "LostItems" (
            photo_url,
            tag_id,
            device_name,
            location,
            registered_at,
            description,
            status,
            created_at,
            updated_at
        ) VALUES (%s, %s, %s, %s, %s)
        RETURNING id;
        """

        now = datetime.now()

        params = (
            file_url,
            tag_id,
            '60주년-1',  # device_name
            '60주년',  # location
            now,  # registered_at
            description,  # description
            '분실',  # default status
            now,  # created_at
            now  # updated_at
        )

        # 실행
        cursor.execute(sql, params)
        record_id = cursor.fetchone()[0]
        conn.commit()

        return record_id
    finally:
        cursor.close()
        conn.close()