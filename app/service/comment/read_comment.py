from sqlalchemy.orm import Session
from fastapi import HTTPException
from sqlalchemy import func, select, or_
from uuid import UUID
from typing import Dict, Any, Optional

from app.models import Comment, User, Block
from app.schemas.response.post import CommentListResponse, CommentDetailResponse, CommentItem, PaginationMeta

class CommentReadService:
    def get_comments(
        self,
        db: Session,
        post_id: int,
        current_user_id: Optional[UUID],
        page: int = 1,
        size: int = 20,
    ) -> CommentListResponse:
        offset = (page - 1) * size
        
        # 1. 댓글(Comment)과 작성자(User) 조인 및 기본 필터링 적용 쿼리 생성
        base_query = db.query(Comment, User).join(User, Comment.user_id == User.id).filter(
            Comment.post_id == post_id,
            Comment.status == "ACTIVE"
        )
        
        # 2. 로그인한 사용자인 경우 차단 관계 필터링 추가
        if current_user_id:
            blocked_by_me = select(Block.blocked_id).where(Block.blocker_id == current_user_id)
            blocking_me = select(Block.blocker_id).where(Block.blocked_id == current_user_id)
            base_query = base_query.filter(
                Comment.user_id.notin_(blocked_by_me),
                Comment.user_id.notin_(blocking_me)
            )
        
        # 3. 전체 개수 산정 (필터링된 결과 기준)
        total_count = base_query.with_entities(func.count(Comment.id)).scalar() or 0

        comments = base_query.order_by(Comment.created_at.asc()).offset(offset).limit(size).all()

        items: list[CommentItem] = []
        for c, author in comments:
            author_name = "알 수 없음" if not author or author.status == "DELETED" else f"{author.nickname}#{author.tag}"
            is_spoiler = c.is_spoiler == 1
            items.append(CommentItem(
                id=c.id,
                parent_id=c.parent_id,
                author_id=None if not author or author.status == "DELETED" else author.id,
                author=author_name,
                content="*** 스포일러로 인해 블라인드 처리되었습니다. 보기 버튼을 눌러 확인하세요. ***" if is_spoiler else c.content,
                is_spoiler=is_spoiler,
                created_at=c.created_at,
            ))

        return CommentListResponse(
            items=items,
            meta=PaginationMeta(
                total_count=total_count,
                current_page=page,
                page_size=size,
                total_pages=(total_count + size - 1) // size if total_count > 0 else 1,
            ),
        )

    def get_comment_detail(self, db: Session, comment_id: int, current_user_id: Optional[UUID]) -> CommentDetailResponse:
        comment = db.query(Comment).filter(Comment.id == comment_id, Comment.status == "ACTIVE").first()
        if not comment:
            raise HTTPException(status_code=404, detail={"code": "COMMENT_NOT_FOUND", "message": "댓글을 찾을 수 없습니다."})
            
        # 비회원이 아니면, 차단 관계를 확인
        if current_user_id:
            is_blocked = db.query(Block).filter(
                or_(
                    (Block.blocker_id == current_user_id) & (Block.blocked_id == comment.user_id),
                    (Block.blocker_id == comment.user_id) & (Block.blocked_id == current_user_id)
                )
            ).first()
            if is_blocked:
                raise HTTPException(status_code=403, detail={"code": "FORBIDDEN_BLOCKED_COMMENT", "message": "차단된 사용자의 댓글입니다."})

        return CommentDetailResponse(id=comment.id, content=comment.content)

comment_read_service = CommentReadService()
