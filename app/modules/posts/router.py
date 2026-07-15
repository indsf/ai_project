# app/modules/posts/router.py
# 커뮤니티 게시판 HTTP 요청·응답 담당

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.posts import crud, schemas

router = APIRouter(prefix="/api/posts", tags=["community"])


@router.get("", response_model=schemas.PostListResponse)
def get_posts(
    category: Optional[str] = None,
    search: Optional[str] = None,
    page: int = 1,
    size: int = 10,
    db: Session = Depends(get_db),
):
    total, items = crud.list_posts(db, category, search, page, size)
    return schemas.PostListResponse(total=total, page=page, size=size, items=items)


@router.get("/{post_id}", response_model=schemas.PostDetail)
def get_post_detail(post_id: int, db: Session = Depends(get_db)):
    post = crud.get_post(db, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")
    return crud.increment_view_count(db, post)


@router.post("", response_model=schemas.PostCreateResponse, status_code=201)
def create_post(data: schemas.PostCreate, db: Session = Depends(get_db)):
    return crud.create_post(db, data)


@router.put("/{post_id}", response_model=schemas.PostUpdateResponse)
def update_post(post_id: int, data: schemas.PostUpdate, db: Session = Depends(get_db)):
    post = crud.get_post(db, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")
    if post.password != data.password:
        raise HTTPException(status_code=401, detail="비밀번호가 일치하지 않습니다.")
    return crud.update_post(db, post, data)


@router.delete("/{post_id}")
def delete_post(post_id: int, password: str, db: Session = Depends(get_db)):
    post = crud.get_post(db, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")
    if post.password != password:
        raise HTTPException(status_code=401, detail="비밀번호가 일치하지 않습니다.")
    crud.delete_post(db, post)
    return {"detail": "삭제되었습니다."}
