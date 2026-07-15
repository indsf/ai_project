# app/modules/places/models.py
# 관광지/레포츠/문화시설/쇼핑/숙박/여행코스/음식점/축제공연행사를 전부 담는 통합 테이블.
# TourAPI 8개 카테고리가 필드 구조는 완전히 동일해서(SCHEMA.md 참고) 테이블은 하나로 두고
# content_type_id로 구분한다. 검색/태그필터/거리순 정렬 로직을 8번 복붙하지 않기 위함.

from typing import List

from sqlalchemy import Column, DateTime, Float, Integer, String, func

from app.core.database import Base
from app.modules.places.categories import slug_for


class Place(Base):
    """
    한국관광공사 TourAPI 원본 데이터(관광지/레포츠/문화시설/쇼핑/숙박/여행코스/음식점/축제공연행사).
    공공누리 제3유형(출처표시, 변경금지) 데이터이므로 원본 필드값은 가공하지 않고 그대로 저장한다.
    """

    __tablename__ = "places"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # TourAPI 원본 고유 ID (contentid). 카테고리 상관없이 전역에서 유일. 재수집 시 upsert 기준 키.
    content_id = Column(String(20), unique=True, nullable=False, index=True)

    # TourAPI contentTypeId 원본 값 ("12","14","15","25","28","32","38","39")
    content_type_id = Column(String(5), nullable=False, index=True)

    title = Column(String(200), nullable=False, index=True)
    addr1 = Column(String(255), nullable=True)
    addr2 = Column(String(255), nullable=True)
    tel = Column(String(50), nullable=True)

    mapx = Column(Float, nullable=True)  # 경도
    mapy = Column(Float, nullable=True)  # 위도

    image_url = Column(String(500), nullable=True)      # firstimage
    thumbnail_url = Column(String(500), nullable=True)   # firstimage2

    region = Column(String(50), nullable=True)  # 수집 권역 (예: 구미_경북권)

    # 날씨 적합도 태그 (app.core.weather_tags 로 추론, 정규화 문자열로 저장: ",indoor,rain,")
    # 원본 TourAPI 필드가 아니라 우리가 추가한 파생 데이터이므로 별도 컬럼으로 분리.
    tags_raw = Column(String(255), nullable=True, default="")

    # TourAPI 원본 등록/수정 시각 문자열 (YYYYMMDDHHmmss) - 그대로 보관
    source_created_time = Column(String(20), nullable=True)
    source_modified_time = Column(String(20), nullable=True)

    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    @property
    def tags(self) -> List[str]:
        """정규화된 tags_raw(',indoor,rain,')를 리스트로 반환한다."""
        from app.core.weather_tags import decode_tags

        return decode_tags(self.tags_raw)

    @property
    def category(self) -> str:
        """content_type_id를 사람이 읽기 좋은 슬러그로 변환 (예: '15' -> 'festivals')."""
        return slug_for(self.content_type_id)
