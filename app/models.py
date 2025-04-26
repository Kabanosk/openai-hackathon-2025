from datetime import datetime

from pydantic import BaseModel


class DateForm(BaseModel):
    age: int
    interests: list[str]
    date_time: datetime
    city: str
    date_type: str


class Place(BaseModel):
    id: int
    name: str
    description: str


class PlaceFeedback(BaseModel):
    place_id: int
    feedback: str
