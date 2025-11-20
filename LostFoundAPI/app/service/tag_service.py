from sqlalchemy.orm import Session
from app.models import Tags

def get_all_tags(db: Session):
    return db.query(Tags).all()

def get_tag_by_name(db: Session, name: str):
    return db.query(Tags).filter(Tags.name == name).first()

def create_tag(db: Session, name: str):
    tag = Tags(name=name)
    db.add(tag)
    db.commit()
    db.refresh(tag)
    return tag

def update_tag(db: Session, tag_id: int, name: str):
    tag = db.query(Tags).filter(Tags.id == tag_id).first()
    if tag:
        tag.name = name
        db.commit()
        db.refresh(tag)
    return tag

def delete_tag(db: Session, tag_id: int):
    tag = db.query(Tags).filter(Tags.id == tag_id).first()
    if tag:
        db.delete(tag)
        db.commit()
        return True
    return False

def get_or_create_tag(db: Session, tag_name: str):
    tag = get_tag_by_name(db, tag_name)
    if not tag:
        tag = create_tag(db, tag_name)
    return tag
