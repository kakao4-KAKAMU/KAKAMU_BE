import logging
from datetime import datetime, timedelta, timezone
from sqlalchemy import func, or_
from app.db.session import SessionLocal
from app.models import User, Persona, Post, Comment, LikeLog, Follow, FavMovie, FavGenre, FavPeople, EntityRelationshipLog

logger = logging.getLogger(__name__)

def hard_delete_old_users():
    """
    [매일 실행] 회원 탈퇴(Soft Delete) 후 30일이 경과한 유저 데이터 최종 영구 파기 및 마스킹
    """
    db = SessionLocal()
    try:
        delete_threshold = datetime.now(timezone.utc) - timedelta(days=30)
        
        # 30일이 지나 영구 삭제 대상이 된 탈퇴 유저 조회
        target_users = db.query(User).filter(
            User.status == "DELETED",
            User.deleted_at <= delete_threshold
        ).all()

        if not target_users:
            logger.debug("[Batch] 30일 경과 영구 탈퇴 대상 유저 없음")
            return

        user_ids = [u.id for u in target_users]
        
        # 유저들의 모든 페르소나 ID 추출
        target_personas = db.query(Persona.id).filter(Persona.user_id.in_(user_ids)).all()
        persona_ids = [p_id for (p_id,) in target_personas]

        if persona_ids:
            # 1. 탈퇴 유저가 남겼던 좋아요(LikeCount) 롤백 연산
            liked_posts = db.query(
                LikeLog.target_id, 
                func.count(LikeLog.id).label("like_count")
            ).filter(
                LikeLog.persona_id.in_(persona_ids),
                LikeLog.target_type == "POST",
                LikeLog.is_active == 1 
            ).group_by(LikeLog.target_id).all()

            for post_id, decrement_count in liked_posts:
                db.query(Post).filter(Post.id == post_id).update(
                    {"like_count": Post.like_count - decrement_count},
                    synchronize_session=False
                )

            # 2. 작성했던 게시물 및 댓글 외래키 마스킹 처리
            user_posts = db.query(Post).filter(Post.persona_id.in_(persona_ids)).all()
            for post in user_posts:
                comment_count = db.query(Comment).filter(Comment.post_id == post.id).count()
                if comment_count == 0:
                    db.delete(post)
                else:
                    post.title = "탈퇴한 사용자의 게시물입니다."
                    post.content = "탈퇴한 사용자의 게시물입니다."
                    post.status = "INACTIVE"
                    post.persona_id = None

            db.query(Comment).filter(Comment.persona_id.in_(persona_ids)).update({
                "content": "탈퇴한 사용자의 댓글입니다.",
                "status": "INACTIVE",
                "persona_id": None
            }, synchronize_session=False)

            # 3. 기타 종속 데이터들 최종 Hard Delete
            db.query(LikeLog).filter(LikeLog.persona_id.in_(persona_ids)).delete(synchronize_session=False)
            db.query(Follow).filter(or_(Follow.follower_id.in_(persona_ids), Follow.following_id.in_(persona_ids))).delete(synchronize_session=False)
            db.query(FavMovie).filter(FavMovie.persona_id.in_(persona_ids)).delete(synchronize_session=False)
            db.query(FavGenre).filter(FavGenre.persona_id.in_(persona_ids)).delete(synchronize_session=False)
            db.query(FavPeople).filter(FavPeople.persona_id.in_(persona_ids)).delete(synchronize_session=False)
            db.query(EntityRelationshipLog).filter(or_(EntityRelationshipLog.persona_id.in_(persona_ids), EntityRelationshipLog.target_id.in_(persona_ids))).delete(synchronize_session=False)
            db.query(Persona).filter(Persona.user_id.in_(user_ids)).delete(synchronize_session=False)

        # 4. 최종 유저(User) 계정 영구 삭제 (LocalAuth/SocialAuth 필요시 추가)
        deleted_users_count = db.query(User).filter(User.id.in_(user_ids)).delete(synchronize_session=False)
        db.commit()
        logger.info(f"[Batch] 30일 경과 탈퇴 유저 영구 삭제 완료: {deleted_users_count}명")

    except Exception as e:
        db.rollback()
        logger.error(f"[Batch] 유저 영구 삭제 배치 실패: {e}")
    finally:
        db.close()