import asyncio
import logging
import json
from app.core.redis import redis_client
from app.db.session import SessionLocal
from app.models import Post, Comment, EntityRelationshipLog

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
                    valid_keys = []
                    valid_values = []
                    
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

async def ml_log_sync_worker():
    """
    [추천 엔진 데이터 파이프라인]
    Redis Queue에 쌓인 ML 활동 로그를 주기적으로 꺼내어 RDB에 Bulk Insert 합니다.
    """
    queue_key = "kakamu:queue:ml_logs"
    
    while True:
        try:
            # 1분(60초) 주기로 일괄 처리 (운영 환경에 따라 조절 가능)
            await asyncio.sleep(60)
            
            # 1. 큐에서 데이터 조회만 먼저 수행 (삭제하지 않음)
            raw_logs = await redis_client.lrange(queue_key, 0, 999)
            if not raw_logs:
                continue
                
            logs_to_insert = [json.loads(raw_log) for raw_log in raw_logs]
            processed_count = len(logs_to_insert)
            
            db = SessionLocal()
            try:
                # [최적화] Bulk Insert를 통해 단 1번의 쿼리로 수백/수천 건의 로그 저장
                db.bulk_insert_mappings(EntityRelationshipLog, logs_to_insert)
                db.commit()
                logger.info(f"Successfully bulk inserted {processed_count} ML logs to DB.")
                
                # 2. DB 저장이 완벽하게 성공한 것을 확인한 후 Redis 큐에서 처리한 만큼만 삭제 (데이터 유실 방지)
                await redis_client.ltrim(queue_key, processed_count, -1)
            except Exception as e:
                db.rollback()
                logger.error(f"ML log Bulk Insert Error: {e}")
                # 에러 발생 시 ltrim을 실행하지 않으므로 다음 주기에 똑같은 데이터를 다시 가져와 재시도합니다.
            finally:
                db.close()
                
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"ML log worker error: {e}")