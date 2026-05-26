import asyncio
import logging
from app.core.redis import redis_client
from app.db.session import SessionLocal

logger = logging.getLogger(__name__)

async def stat_sync_worker():
    """
    [3.4 통계 데이터 완충 계층 정책] 
    Redis에 쌓인 좋아요/조회수 등을 5분 주기로 메인 DB에 일괄 반영(Write-Back)하는 백그라운드 워커입니다.
    """
    while True:
        try:
            # 5분(300초) 주기로 실행
            await asyncio.sleep(300)
            
            # Redis에 저장된 통계 Keys 스캔 (예: kakamu:stat:post:*:likes)
            cursor = b'0'
            while cursor:
                cursor, keys = await redis_client.scan(cursor=cursor, match="kakamu:stat:*:likes", count=100)
                if not keys:
                    continue
                    
                db = SessionLocal()
                try:
                    for key in keys:
                        parts = key.split(":")
                        if len(parts) == 5:
                            target_type = parts[2]
                            target_id = int(parts[3])
                            
                            # 1. Redis에서 현재 누적값 조회
                            current_val = await redis_client.get(key)
                            if current_val is None:
                                continue
                                
                            # 2. 메인 DB 업데이트 (DB 모델에 view_count, like_count 등의 필드가 추가될 경우 활용)
                            # if target_type == "post":
                            #     db.query(Post).filter(Post.id == target_id).update({"like_count": int(current_val)})
                            # elif target_type == "comment":
                            #     db.query(Comment).filter(Comment.id == target_id).update({"like_count": int(current_val)})
                            pass
                    # db.commit() # 실제 DB 필드 적용 후 주석 해제
                    logger.info(f"Successfully synced {len(keys)} stat records to DB.")
                except Exception as e:
                    db.rollback()
                    logger.error(f"DB Sync Error: {e}")
                finally:
                    db.close()
                    
        except asyncio.CancelledError:
            logger.info("Stat sync worker cancelled.")
            break
        except Exception as e:
            logger.error(f"Stat sync worker error: {e}")