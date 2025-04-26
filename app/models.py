from datetime import datetime

from pydantic import BaseModel
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class DateForm:
    age: int
    interests: List[str]
    date_time: datetime
    city: str
    date_type: str
    name: Optional[str] = None
    gender: Optional[str] = None
    budget: Optional[str] = None

class Place(BaseModel):
    id: int
    name: str
    description: str


class PlaceFeedback(BaseModel):
    place_id: int
    feedback: str
