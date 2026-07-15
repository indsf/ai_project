# app/modules/recommend/place_models.py
# 한국관광공사 TourAPI 공공데이터 저장 테이블

from sqlalchemy import Column, Integer, String, Float, DateTime, func

from app.core.database import Base


class Place(Base):
    """
    TourAPI 4.0 관광정보 (관광지/음식점/축제/숙박 등 통합)
    contentTypeId로 카테고리 구분
    """

    __tablename__ = "places"

    id = Column(Integer, primary_key=True, index=True)

    content_id = Column(String(20), unique=True, nullable=False, index=True)
    content_type_id = Column(String(10), nullable=False, index=True)  # 12,14,15,25,28,32,38,39

    title = Column(String(200), nullable=False)
    addr1 = Column(String(300), nullable=True)
    addr2 = Column(String(200), nullable=True)
    tel = Column(String(50), nullable=True)

    mapx = Column(Float, nullable=True)  # 경도
    mapy = Column(Float, nullable=True)  # 위도

    area_code = Column(String(10), nullable=True)
    sigungu_code = Column(String(10), nullable=True)

    cat1 = Column(String(10), nullable=True)
    cat2 = Column(String(10), nullable=True)
    cat3 = Column(String(10), nullable=True)

    first_image = Column(String(500), nullable=True)

    created_at = Column(DateTime, server_default=func.now())