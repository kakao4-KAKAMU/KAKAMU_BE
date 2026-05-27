# 트래픽 트레이스 추적
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor


def setup_tracing(app, engine):

    resource = Resource.create({
        "service.name": "filma-back", # Grafana Tempo에서 보이는 이름
        "deployment.environment": "dev", # 실행 환경 추후에 prod로 변경 필요
    })

    # trace 를 만들 때 이 설정을 사용해라
    trace.set_tracer_provider(
        TracerProvider(resource=resource)
    )

    # 수집한 trace 데이터를 어디로 보낼지 결정
    otlp_exporter = OTLPSpanExporter(
        endpoint="alloy.monitoring.svc.cluster.local:4317", # 쿠버네티스 내부 dns 주소
        insecure=True, # 평문으로 보내겠다 (내부 클러스터 통신)
    )

    # 생성된 span을 바로 안 보내고 모아서 배치로 전송
    trace.get_tracer_provider().add_span_processor(
        BatchSpanProcessor(otlp_exporter)
    )

    # 자동 instrumentation
    FastAPIInstrumentor.instrument_app(app) # FastAPI 요청을 자동 추적
    RedisInstrumentor().instrument() # Redis 호출을 자동 추적
    SQLAlchemyInstrumentor().instrument(
        engine=engine
    ) # DB 쿼리를 자동 추적