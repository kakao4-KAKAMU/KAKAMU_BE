from uuid import UUID
from fastapi import APIRouter, Depends, BackgroundTasks

from app.api.deps import get_active_user, get_current_persona
from app.models.user import User
from app.schemas.request.log import ActivityLogCreate
from app.service.log.activity_log import activity_log_service
from app.schemas.response.common import SuccessResponse

router = APIRouter()

@router.post("/activity", status_code=202, response_model=SuccessResponse, dependencies=[Depends(get_active_user)])
async def log_activity(
    log_in: ActivityLogCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_active_user),
    current_persona_id: UUID = Depends(get_current_persona)
):
    """프론트엔드에서 수집한 유저 행동 로그를 백그라운드 큐에 적재합니다."""
    background_tasks.add_task(
        activity_log_service.process_activity_log,
        current_user.id,
        current_persona_id,
        log_in,
    )
    return {"status": "success", "message": "Log accepted"}