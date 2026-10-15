from typing import List, Optional
from pydantic import BaseModel, Field


class Evidence(BaseModel):
    time: str = Field(description="Mốc thời gian dạng mm:ss của dòng chứa trích dẫn")
    speaker: Optional[str] = None
    quote: str = Field(description="Trích dẫn NGUYÊN VĂN từ transcript")


class Item(BaseModel):
    type: str = Field(description="decision | action_item | blocker | request_feedback | open_issue | knowledge")
    content: str
    status: str = Field(description="final | superseded | proposed | deferred | cancelled | open")
    owner: Optional[str] = None
    due: Optional[str] = None
    rationale: Optional[str] = None
    evidence: List[Evidence]
    confidence: float
    needs_review: bool
    note: Optional[str] = None


class Thread(BaseModel):
    topic: str
    steps: List[str]


class Extraction(BaseModel):
    threads: List[Thread]
    items: List[Item]
