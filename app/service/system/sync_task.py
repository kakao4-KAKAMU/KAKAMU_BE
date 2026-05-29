import asyncio
import logging
import json
from app.core.redis import redis_client
from app.db.session import SessionLocal
from app.models import Post, Comment, EntityRelationshipLog

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
            
            # 트랜잭션 안전성을 위해 파이프라인을 사용해 최대 1000건을 가져오고 큐에서 삭제
            pipeline = redis_client.pipeline()
            pipeline.lrange(queue_key, 0, 999)
            pipeline.ltrim(queue_key, 1000, -1)
            results = await pipeline.execute()
            
            raw_logs = results[0]
            if not raw_logs:
                continue
                
            logs_to_insert = [json.loads(raw_log) for raw_log in raw_logs]
            
            db = SessionLocal()
            try:
                # [최적화] Bulk Insert를 통해 단 1번의 쿼리로 수백/수천 건의 로그 저장
                db.bulk_insert_mappings(EntityRelationshipLog, logs_to_insert)
                db.commit()
                logger.info(f"Successfully bulk inserted {len(logs_to_insert)} ML logs to DB.")
            except Exception as e:
                db.rollback()
                logger.error(f"ML log Bulk Insert Error: {e}")
            finally:
                db.close()
                
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"ML log worker error: {e}")