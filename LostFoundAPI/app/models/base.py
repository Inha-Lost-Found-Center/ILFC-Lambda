from sqlalchemy.orm import declarative_base, declared_attr
from sqlalchemy import Column, DateTime
import datetime

Base = declarative_base()

class TimestampMixin:

    # @declared_attr는 SQLAlchemy가 이 클래스를 상속받는
    # *모든 하위 모델*에 대해 이 컬럼을 동적으로 생성하도록 지시합니다.

    @declared_attr
    def created_at(cls):
        return Column(
            DateTime,
            default=datetime.datetime.utcnow,
            nullable=False
        )

    @declared_attr
    def updated_at(cls):
        return Column(
            DateTime,
            default=datetime.datetime.utcnow,
            onupdate=datetime.datetime.utcnow,
            nullable=False
        )
