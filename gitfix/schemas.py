from typing import Literal, Union

from pydantic import BaseModel, Field

types = Literal["command", "documentation", "other"]


class Suggestion(BaseModel):
    type_: types = Field(alias="type")
    explanation: str | None = None


class Command(Suggestion):
    command: str


class Documentation(Suggestion):
    url: str


class Response(BaseModel):
    error: str
    suggestions: dict[str, Union[Suggestion, Command, Documentation]]
