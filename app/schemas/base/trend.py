from pydantic import BaseModel


class TrendItem(BaseModel):
    rank: int
    keyword: str
    search_count: int
