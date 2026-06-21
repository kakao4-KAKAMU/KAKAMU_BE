from pydantic import BaseModel, Field


class MlIngestResponse(BaseModel):
    outbox_id: int = Field(..., description="ingest outbox ID")
