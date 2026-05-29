from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from uuid import UUID

from app.models import User, Persona, Post, Comment, LikeLog, Follow, FavMovie, FavGenre, FavPeople, EntityRelationshipLog

class AccountTerminationService:
    
    @staticmethod
    async def terminate_account(db: Session, user_id: UUID) -> bool:
        """
        회원 탈퇴 및 데이터 파기 (Atomic Transaction 보장)
        """
        # 1. 유저 및 종속 페르소나 조회
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            # [Fix 1] 프로젝트 에러 메시지 표준 구조(code, message) 준수
            raise HTTPException(status_code=404, detail={"code": "USER_NOT_FOUND", "message": "유저를 찾을 수 없습니다."})
            
        personas = db.query(Persona).filter(Persona.user_id == user_id).all()
        persona_ids = [p.id for p in personas]

        try:
            # === [1] 좋아요 수 즉시 강제 차감 (DB 직접 차감) ===
            # 탈퇴 유저가 하트를 누른 게시물들의 ID와 누른 횟수 그룹화
            # [수정] like_service.py의 정책에 맞춰 is_active == 1 인 로그만 대상으로 산정합니다.
            liked_posts = db.query(
                LikeLog.target_id, 
                func.count(LikeLog.id).label("like_count")
            ).filter(
                LikeLog.persona_id.in_(persona_ids),
                LikeLog.target_type == "POST",
                LikeLog.is_active == 1 
            ).group_by(LikeLog.target_id).all()

            for post_id, decrement_count in liked_posts:
                # DB 즉시 차감
                db.query(Post).filter(Post.id == post_id).update(
                    {"like_count": Post.like_count - decrement_count},
                    synchronize_session=False
                )

            # === [2] 작성한 게시물 및 댓글 연동 파기 (외래키 방어 마스킹) ===
            user_posts = db.query(Post).filter(Post.persona_id.in_(persona_ids)).all()
            for post in user_posts:
                comment_count = db.query(Comment).filter(Comment.post_id == post.id).count()
                
                if comment_count == 0:
                    db.delete(post)
                else:
                    # 타인의 댓글이 존재하면 외래키 에러 방지를 위해 정보 치환 (Masking)
                    post.title = "탈퇴한 사용자의 게시물입니다."
                    post.content = "탈퇴한 사용자의 게시물입니다."
                    post.status = "INACTIVE"
                    post.persona_id = None # [Fix 4] Persona 삭제 시 외래키 제약 에러 방어

            # [Fix 5] 탈퇴 유저가 타인의 글에 쓴 '댓글' 연동 해제 및 마스킹
            db.query(Comment).filter(Comment.persona_id.in_(persona_ids)).update({
                "content": "탈퇴한 사용자의 댓글입니다.",
                "status": "INACTIVE",
                "persona_id": None
            }, synchronize_session=False)

            # === [3] 종속 데이터 최종 영구 파기 (Hard Delete) ===
            # 4-1. 소셜 매핑 로그 (좋아요 로그, 팔로우 관계)
            db.query(LikeLog).filter(LikeLog.persona_id.in_(persona_ids)).delete(synchronize_session=False)
            db.query(Follow).filter(
                or_(Follow.follower_id.in_(persona_ids), Follow.following_id.in_(persona_ids))
            ).delete(synchronize_session=False)
            
            # [Fix 6] 페르소나와 매핑된 모든 취향, 인물, 영화 및 ML 로그 종속 데이터 제거
            db.query(FavMovie).filter(FavMovie.persona_id.in_(persona_ids)).delete(synchronize_session=False)
            db.query(FavGenre).filter(FavGenre.persona_id.in_(persona_ids)).delete(synchronize_session=False)
            db.query(FavPeople).filter(FavPeople.persona_id.in_(persona_ids)).delete(synchronize_session=False)
            db.query(EntityRelationshipLog).filter(
                or_(EntityRelationshipLog.persona_id.in_(persona_ids), 
                    EntityRelationshipLog.target_id.in_(persona_ids))
            ).delete(synchronize_session=False)
            
            # 4-2. 메인 레코드 (페르소나 및 유저)
            db.query(Persona).filter(Persona.user_id == user_id).delete(synchronize_session=False)
            db.query(User).filter(User.id == user_id).delete(synchronize_session=False)

            # === [4] 트랜잭션 확정 ===
            db.commit()
            return True

        except Exception as e:
            db.rollback() # 에러 발생 시 모든 데이터베이스 조작을 롤백하여 무결성 보장
            print(f"[Termination Error] Failed to terminate account for user {user_id}: {e}")
            raise HTTPException(
                status_code=500, 
                detail={"code": "TERMINATION_FAILED", "message": "탈퇴 처리 중 예기치 않은 오류가 발생했습니다."}
            )
            
account_termination_service = AccountTerminationService()