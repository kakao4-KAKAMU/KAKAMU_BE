import logging
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.core.redis import redis_client
from app.worker.search_batch import run_daily_search_aggregation
from app.worker.user_batch import hard_delete_old_users

logger = logging.getLogger(__name__)

async def run_daily_search_aggregation_with_lock():
    lock_key = "lock:daily_search_batch"
    if await redis_client.set(lock_key, "running", nx=True, ex=600):
        try:
            logger.info("[Batch] 검색어 통계 배치를 시작합니다...")
            # 동기 함수인 배치를 비동기 이벤트 루프 블로킹 없이 안전하게 실행
            await asyncio.to_thread(run_daily_search_aggregation)
        finally:
            await redis_client.delete(lock_key)
    else:
        logger.info("[Batch] 다른 서버에서 이미 검색어 통계 배치를 실행 중입니다. 스킵합니다.")

async def hard_delete_old_users_with_lock():
    lock_key = "lock:hard_delete_users_batch"
    if await redis_client.set(lock_key, "running", nx=True, ex=600):
        try:
            logger.info("[Batch] 탈퇴 유저 영구 삭제 배치를 시작합니다...")
            await asyncio.to_thread(hard_delete_old_users)
        finally:
            await redis_client.delete(lock_key)
    else:
        logger.info("[Batch] 다른 서버에서 이미 탈퇴 유저 영구 삭제 배치를 실행 중입니다. 스킵합니다.")

def start_scheduler() -> AsyncIOScheduler:
    """분산 락이 적용된 스케줄러를 초기화하고 시작합니다."""
    # 비동기 함수(async def)를 실행할 수 있는 AsyncIOScheduler 사용
    scheduler = AsyncIOScheduler()
    scheduler.add_job(run_daily_search_aggregation_with_lock, 'cron', hour=3, minute=0)
    scheduler.add_job(hard_delete_old_users_with_lock, 'cron', hour=4, minute=30)
    scheduler.start()
    logger.info("Background scheduler started with distributed locks.")
    return scheduler