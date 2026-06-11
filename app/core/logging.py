# 로그 포맷, JSON 포맷 , 로그 레벨 설정

import json
import logging # 로그 구조화를 위한 라이브러리

class JsonFormatter(logging.Formatter):
    def format(self, record):
        # 기본 로그 포멧
        log_record = {
            "timestamp": self.formatTime(record, "%Y-%m-%d %H:%M:%S"), # 시간
            "level" : record.levelname,                                # 로그의 위험도
            "logger" : record.name,
            "message" : record.getMessage(),
        }

        if hasattr(record, "extra_data"):
            log_record.update(record.extra_data)

        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_record, ensure_ascii=False)

logger = logging.getLogger("fastapi_app")
logger.setLevel(logging.INFO) # INFO 레벨 이상만 출력

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(JsonFormatter())
logger.addHandler(stream_handler)

# 로그 레벨
# DEBUG : 개발 디버깅
# INFO : 일반 운영 정보
# WARNING : 경고
# ERROR : 오류
# CRITICAL : 치명적 장애

