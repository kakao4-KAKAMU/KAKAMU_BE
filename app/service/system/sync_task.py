import asyncio
import logging
from app.core.redis import redis_client
from app.db.session import SessionLocal
from app.models import Post, Comment

logger = logging.getLogger(__name__)

# Lua 스크립트: Redis의 값이 내가 방금 DB에 동기화한 값과 일치할 때만 키를 삭제 (Race Condition 방지)
DELETE_IF_MATCH_SCRIPT = """
if redis.call("get", KEYS[1]) == ARGV[1] then
    return redis.call("del", KEYS[1])
else
    return 0
end
"""

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
                    # [최적화 1] Redis 다중 조회 (MGET) - 반복적인 네트워크 I/O 병목 제거
                    values = await redis_client.mget(keys)
                    
                    post_updates = []
                    comment_updates = []
                    
                    for key, current_val in zip(keys, values):
                        if current_val is None:
                            continue
                            
                        # Redis 클라이언트 설정에 따라 bytes로 넘어올 수 있으므로 디코딩 처리
                        key_str = key.decode("utf-8") if isinstance(key, bytes) else key
                        parts = key_str.split(":")
                        if len(parts) == 5:
                            target_type = parts[2]
                            target_id = int(parts[3])
                            
                            if target_type == "post":
                                post_updates.append({"id": target_id, "like_count": int(current_val)})
                            elif target_type == "comment":
                                comment_updates.append({"id": target_id, "like_count": int(current_val)})
                    
                    # [최적화 2] DB 일괄 업데이트 (Bulk Update) - 쿼리 호출 수 극적 감소
                    if post_updates:
                        db.bulk_update_mappings(Post, post_updates)
                    if comment_updates:
                        db.bulk_update_mappings(Comment, comment_updates)
                        
                    db.commit()
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