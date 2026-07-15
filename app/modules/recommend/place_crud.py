# app/modules/recommend/place_crud.py

from sqlalchemy.orm import Session
from app.modules.recommend.place_models import Place


def upsert_place(db: Session, data: dict) -> Place:
    place = db.query(Place).filter(Place.content_id == data["content_id"]).first()
    if place is None:
        place = Place(**data)
        db.add(place)
    else:
        for key, value in data.items():
            setattr(place, key, value)
    return place


def get_places_by_category(db: Session, content_type_id: str, limit: int = 20) -> list[Place]:
    return (
        db.query(Place)
        .filter(Place.content_type_id == content_type_id)
        .limit(limit)
        .all()
    )


def search_places(db: Session, keyword: str, limit: int = 10) -> list[Place]:
    return (
        db.query(Place)
        .filter(Place.title.contains(keyword))
        .limit(limit)
        .all()
    )

def get_places_sample(db: Session, limit: int = 10) -> list[Place]:
    return db.query(Place).limit(limit).all()