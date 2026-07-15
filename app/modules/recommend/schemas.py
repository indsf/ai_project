from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    history: Optional[List[ChatMessage]] = []


class ChatResponse(BaseModel):
    reply: str
    related_post_ids: List[int] = []


class WeatherForecastResponse(BaseModel):
    forecast_at: datetime
    temperature: Optional[float]
    rain_prob: Optional[int]
    rain_type: str

    class Config:
        from_attributes = True