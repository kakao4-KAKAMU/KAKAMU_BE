from sqlalchemy.orm import Session
from fastapi import HTTPException
from sqlalchemy import func, select, or_
from uuid import UUID
from typing import Dict, Any

from app.models import Comment, Persona, Block

class CommentReadService:
    def get_comments(self, db: Session, post_id: int, current_persona_id: UUID, page: int = 1, size: int = 20) -> Dict[str, Any]:
        offset = (page - 1) * size
        
        # 1. 차단 관계 서브쿼리 (메모리에 올리지 않고 DB 엔진 레벨 활용)
        blocked_by_me = select(Block.blocked_id).where(Block.blocker_id == current_persona_id)
        blocking_me = select(Block.blocker_id).where(Block.blocked_id == current_persona_id)
        
        # 2. 댓글(Comment)과 작성자(Persona) 조인 및 필터링 적용 쿼리 생성
        base_query = db.query(Comment).join(Persona, Comment.persona_id == Persona.id).filter(
            Comment.post_id == post_id,
            Comment.status == "ACTIVE",
            Persona.status == "ACTIVE",               # 탈퇴/삭제 유예 기간(DELETED)인 작성자 숨김
            Comment.persona_id.notin_(blocked_by_me), # 내가 차단한 사람 숨김
            Comment.persona_id.notin_(blocking_me)    # 나를 차단한 사람 숨김
        )
        
        # 3. 전체 개수 산정 (필터링된 결과 기준)
        total_count = base_query.with_entities(func.count(Comment.id)).scalar() or 0
        
        comments = base_query.order_by(Comment.created_at.asc()).offset(offset).limit(size).all()
        
        result = []
        for c in comments:
            author = c.persona
            author_name = "알 수 없음" if not author or author.status == "DELETED" else f"{author.nickname}#{author.tag}"
            is_spoiler = c.is_spoiler == 1
            result.append({
                "id": c.id, "parent_id": c.parent_id, "author_id": None if not author or author.status == "DELETED" else author.id,
                "author": author_name, "content": "*** 스포일러로 인해 블라인드 처리되었습니다. 보기 버튼을 눌러 확인하세요. ***" if is_spoiler else c.content,
                "is_spoiler": is_spoiler, "created_at": c.created_at
            })
            
        return {
            "items": result,
            "meta": {
                "total_count": total_count,
                "current_page": page,
                "page_size": size,
                "total_pages": (total_count + size - 1) // size if total_count > 0 else 1
            }
        }

    def get_comment_detail(self, db: Session, comment_id: int, current_persona_id: UUID) -> Dict[str, Any]:
        comment = db.query(Comment).filter(Comment.id == comment_id, Comment.status == "ACTIVE").first()
        if not comment:
            raise HTTPException(status_code=404, detail={"code": "COMMENT_NOT_FOUND", "message": "댓글을 찾을 수 없습니다."})
            
        # 직접 링크를 통해 접속하더라도 본인과의 차단(Block) 관계가 있으면 스포일러 내용 등 확인 불가
        is_blocked = db.query(Block).filter(
            or_(
                (Block.blocker_id == current_persona_id) & (Block.blocked_id == comment.persona_id),
                (Block.blocker_id == comment.persona_id) & (Block.blocked_id == current_persona_id)
            )
        ).first()
        if is_blocked:
            raise HTTPException(status_code=403, detail={"code": "FORBIDDEN_BLOCKED_COMMENT", "message": "차단된 사용자의 댓글입니다."})
            
        return {"id": comment.id, "content": comment.content}

comment_read_service = CommentReadService()