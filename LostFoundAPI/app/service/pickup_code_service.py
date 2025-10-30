import random
import datetime
from sqlalchemy.orm import Session
from app.models import PickupCodes, LostItems, Users

def generate_unique_code(db: Session, length: int = 6) -> str:
    """
    DB에서 중복되지 않는 6자리 '숫자' 코드를 생성합니다.
    """
    while True:
        code = str(random.randint(100000, 999999))

        existing_code = db.query(PickupCodes).filter(PickupCodes.code == code).first()

        if not existing_code:
            return code

def create_pickup_code(db: Session, item: LostItems, user: Users) -> PickupCodes:
    """
    특정 아이템과 사용자에 대한 픽업 코드를 생성합니다.
    """
    expires_at = datetime.datetime.utcnow() + datetime.timedelta(days=7)

    unique_code = generate_unique_code(db)

    db_pickup_code = PickupCodes(
        lost_item_id=item.id,
        user_id=user.id,
        code=unique_code,
        expires_at=expires_at,
        is_used=False
    )

    db.add(db_pickup_code)

    return db_pickup_code
