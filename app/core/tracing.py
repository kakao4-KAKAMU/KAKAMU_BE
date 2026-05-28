# 트래픽 트레이스 추적
import os

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

from opentelemetry.sdk.trace.export import ConsoleSpanExporter # 로컬 전용
from app.db.session import engine

def setup_tracing(app):
    service_name = os.getenv("OTEL_SERVICE_NAME", "filma-back")
    environment = os.getenv("APP_ENV", "dev")
    otlp_endpoint = os.getenv(
        "OTEL_EXPORTER_OTLP_ENDPOINT",
        "alloy.monitoring.svc.cluster.local:4317"
    )

    resource = Resource.create({
        "service.name": service_name, # Grafana Tempo에서 보이는 이름
        "deployment.environment": environment, # 실행 환경 추후에 prod로 변경 필요
    })

    provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(provider)

    # 수집한 trace 데이터를 어디로 보낼지 결정
    otlp_exporter = OTLPSpanExporter(
        endpoint=otlp_endpoint, # 쿠버네티스 내부 dns 주소
        insecure=True, # 평문으로 보내겠다 (내부 클러스터 통신)
    )

    # 생성된 span을 바로 안 보내고 모아서 배치로 전송
    trace.get_tracer_provider().add_span_processor(
        BatchSpanProcessor(otlp_exporter)
    )

    provider.add_span_processor(
        BatchSpanProcessor(otlp_exporter)
    )

    # 로컬로 하고 싶으면 설정 파일에 true으로 해야 함.
    if os.getenv("OTEL_CONSOLE_EXPORTER", "false").lower() == "true":
        provider.add_span_processor(
            BatchSpanProcessor(ConsoleSpanExporter())
        )

     # 자동 instrumentation
    FastAPIInstrumentor.instrument_app(app) # FastAPI 요청을 자동 추적
    RedisInstrumentor().instrument() # Redis 호출을 자동 추적
    SQLAlchemyInstrumentor().instrument(
        engine=engine
    ) # DB 쿼리를 자동 추적