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

class GameSummary(BaseModel):
    overall_performance: str
    main_mistakes: list[str]
    style_feedback: str
    suggestions: list[str]


class StyleAdvice(BaseModel):
    matched: bool
    advice: str

class Continuation(BaseModel):
    move: str
    score: int


class BestMove(BaseModel):
    move: str
    score: int
    continuations: List[Continuation]
