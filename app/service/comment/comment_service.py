from .create_comment import CommentCreateService
from .read_comment import CommentReadService
from .update_comment import CommentUpdateService
from .delete_comment import CommentDeleteService

class CommentService(CommentCreateService, CommentReadService, CommentUpdateService, CommentDeleteService):
    """
    다중 상속을 통해 분리된 서비스 메서드들을 하나의 진입점으로 모아 제공합니다.
    """
    pass

comment_service = CommentService()
