from fastapi import APIRouter, BackgroundTasks, Depends
from app.worker.search_batch import run_daily_search_aggregation
from app.worker.user_batch import hard_delete_old_users
from app.api.deps.auth import get_active_user
from app.models.user import User

router = APIRouter(prefix="/test/batch", tags=["Test - Batch"])

@router.post(
    "/search",
    summary="[테스트용] 검색어 통계 배치 수동 실행"
)
def trigger_search_batch(
    background_tasks: BackgroundTasks
):
    """수동으로 검색어 통계 배치를 백그라운드에서 즉시 실행합니다."""
    background_tasks.add_task(run_daily_search_aggregation)
    return {"status": "success", "message": "검색어 통계 배치가 백그라운드에서 시작되었습니다. 서버 로그를 확인하세요."}

@router.post(
    "/user-delete",
    summary="[테스트용] 탈퇴 유저 영구 삭제 배치 수동 실행"
)
def trigger_user_delete_batch(
    background_tasks: BackgroundTasks
):
    """수동으로 7일 경과 탈퇴 유저 영구 삭제 배치를 백그라운드에서 즉시 실행합니다."""
    background_tasks.add_task(hard_delete_old_users)
    return {"status": "success", "message": "탈퇴 유저 영구 삭제 배치가 백그라운드에서 시작되었습니다. 서버 로그를 확인하세요."}