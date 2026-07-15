# app/modules/festival/models.py
# 한국관광공사 TourAPI(축제공연행사) 원본 데이터를 담는 테이블

from sqlalchemy import Column, DateTime, Float, Integer, String, func

from app.core.database import Base


class Festival(Base):
    """
    한국관광공사 TourAPI 축제공연행사(contentTypeId=15) 데이터.
    공공누리 제3유형(출처표시, 변경금지) 데이터이므로 원본 필드값은 가공하지 않고 그대로 저장한다.
    """

    __tablename__ = "festivals"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # TourAPI 원본 고유 ID (contentid). 재수집 시 upsert 기준 키.
    content_id = Column(String(20), unique=True, nullable=False, index=True)

    title = Column(String(200), nullable=False, index=True)
    addr1 = Column(String(255), nullable=True)
    addr2 = Column(String(255), nullable=True)
    tel = Column(String(50), nullable=True)

    mapx = Column(Float, nullable=True)  # 경도
    mapy = Column(Float, nullable=True)  # 위도

    image_url = Column(String(500), nullable=True)      # firstimage
    thumbnail_url = Column(String(500), nullable=True)   # firstimage3

    region = Column(String(50), nullable=True)  # 수집 권역 (예: 구미_경북권)

    # TourAPI 원본 등록/수정 시각 문자열 (YYYYMMDDHHmmss) - 그대로 보관
    source_created_time = Column(String(20), nullable=True)
    source_modified_time = Column(String(20), nullable=True)

    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )