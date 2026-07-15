# app/modules/posts/router.py
# 커뮤니티 게시판 HTTP 요청·응답 담당

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.posts import crud, schemas

router = APIRouter(prefix="/api/posts", tags=["community"])


@router.get(
    "",
    response_model=schemas.PostListResponse,
    summary="게시글 목록",
    description=(
        "category로 필터링하거나 search로 제목 부분검색 가능. "
        "category 값: festival(축제 후기/정보), spot(관광지/명소 추천), food(맛집 추천)"
    ),
)
def get_posts(
    category: Optional[schemas.PostCategory] = Query(None, description="게시글 카테고리 필터"),
    search: Optional[str] = Query(None, description="제목 부분 검색어", examples=["라면"]),
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    total, items = crud.list_posts(db, category, search, page, size)
    return schemas.PostListResponse(total=total, page=page, size=size, items=items)


@router.get(
    "/{post_id}",
    response_model=schemas.PostDetail,
    summary="게시글 상세",
    description="조회할 때마다 view_count가 1 증가한다.",
)
def get_post_detail(
    post_id: int = Path(..., examples=[1]),
    db: Session = Depends(get_db),
):
    post = crud.get_post(db, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")
    return crud.increment_view_count(db, post)


@router.post(
    "",
    response_model=schemas.PostCreateResponse,
    status_code=201,
    summary="게시글 작성",
    description=(
        "category=spot(관광지 추천)이면 start_date/end_date는 무시되고 저장 시 null로 들어간다. "
        "password는 이 글을 나중에 수정/삭제할 때 필요하니 잘 기억해두라고 안내해야 함."
    ),
)
def create_post(data: schemas.PostCreate, db: Session = Depends(get_db)):
    return crud.create_post(db, data)


@router.put(
    "/{post_id}",
    response_model=schemas.PostUpdateResponse,
    summary="게시글 수정",
    description="작성 시 등록한 password가 일치해야 수정된다. 안 맞으면 401.",
)
def update_post(
    post_id: int = Path(..., examples=[1]),
    *,
    data: schemas.PostUpdate,
    db: Session = Depends(get_db),
):
    post = crud.get_post(db, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")
    if post.password != data.password:
        raise HTTPException(status_code=401, detail="비밀번호가 일치하지 않습니다.")
    return crud.update_post(db, post, data)


@router.delete(
    "/{post_id}",
    summary="게시글 삭제",
    description="작성 시 등록한 password가 일치해야 삭제된다. 안 맞으면 401.",
)
def delete_post(
    post_id: int = Path(..., examples=[1]),
    password: str = Query(..., description="글 작성 시 등록한 비밀번호", examples=["1234"]),
    db: Session = Depends(get_db),
):
    post = crud.get_post(db, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")
    if post.password != password:
        raise HTTPException(status_code=401, detail="비밀번호가 일치하지 않습니다.")
    crud.delete_post(db, post)
    return {"detail": "삭제되었습니다."}
