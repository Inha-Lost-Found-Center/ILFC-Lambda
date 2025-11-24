import random
from sqlalchemy.orm import Session
from sqlalchemy.orm import Session
from app.models import LostItems, Tags, Users, PickupCodes
from app.models.lost_item import LostItemStatus
from app.service import tag_service  # (기존 tag_service 활용)

# 미리 정의된 태그 목록 (랜덤 선택용)
DUMMY_TAGS = ["지갑", "휴대폰", "에어팟", "카드", "학생증", "우산", "노트북", "가방"]
# 미리 정의된 위치 목록
DUMMY_LOCATIONS = ["60주년", "2호관", "5호관", "하이테크", "학생회관", "정석", "비룡플라자"]

def get_or_create_tag(db: Session, tag_name: str) -> Tags:
    """
    DB에서 태그를 찾거나, 없으면 새로 생성하여 반환합니다.
    """
    tag = db.query(Tags).filter(Tags.name == tag_name).first()
    if not tag:
        tag = Tags(name=tag_name)
        db.add(tag)
        # 참고: 태그는 개별 트랜잭션으로 커밋하거나,
        # 호출한 쪽(create_dummy_items)에서 한 번에 커밋할 수 있습니다.
        # 여기서는 flush를 사용하여 ID를 미리 얻는 방식을 사용할 수 있습니다.
        db.flush()
    return tag

def create_dummy_items(db: Session, count: int) -> list[LostItems]:
    """
    지정된 개수(count)만큼 가상의 분실물을 생성합니다.
    """
    created_items = []

    # 태그 객체를 미리 가져오거나 생성 (DB 조회 최소화)
    tag_objects = {name: get_or_create_tag(db, name) for name in DUMMY_TAGS}
    tag_objects["테스트용"] = get_or_create_tag(db, "테스트용")

    for i in range(count):
        # 1. 가상 데이터 정의
        item_name = random.choice(DUMMY_TAGS)
        location = random.choice(DUMMY_LOCATIONS)
        photo_url = f"https://picsum.photos/seed/{random.randint(1, 10000)}/400/400"
        description = f"테스트용 {item_name}입니다. {location}에서 발견되었습니다. (항목 {i+1})"

        # 2. LostItems 객체 생성 (기존 모델 정의 참조)
        new_item = LostItems(
            photo_url=photo_url,
            device_name="TestAPI-Generator",
            location=location,
            locker_id=1,
            description=description,
            status=LostItemStatus.STORAGE
        )

        # 3. 태그 연결 (M2M 관계 활용)
        new_item.tags.append(tag_objects[item_name])
        new_item.tags.append(tag_objects["테스트용"])

        db.add(new_item)
        created_items.append(new_item)

    # 4. DB에 일괄 커밋
    db.commit()

    # 5. 생성된 객체 반환
    return created_items


def delete_dummy_items(db: Session) -> int:
    """
    device_name이 'TestAPI-Generator'인 아이템과 관련 픽업 코드를 삭제합니다.
    """
    item_ids = [
        item_id for (item_id,) in db.query(LostItems.id).filter(
            LostItems.device_name == "TestAPI-Generator"
        ).all()
    ]

    if not item_ids:
        return 0

    db.query(PickupCodes).filter(
        PickupCodes.lost_item_id.in_(item_ids)
    ).delete(synchronize_session=False)

    item_count = db.query(LostItems).filter(
        LostItems.id.in_(item_ids)
    ).delete(synchronize_session=False)

    db.commit()
    return item_count
