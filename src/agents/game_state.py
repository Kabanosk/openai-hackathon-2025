from typing import List, Optional

from pydantic import BaseModel, Field


class User(BaseModel):
    name: str
    elo: int
    style: Optional[str] = None
    openings: List[str] = Field(default_factory=list)


class Game(BaseModel):
    fen: str
    user: User
