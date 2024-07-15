from enum import Enum
from typing import Union

from pydantic import BaseModel, Field


class Type(str, Enum):
    COMMAND = "command"
    DOCUMENTATION = "documentation"
    OTHER = "other"


class Suggestion(BaseModel):
    type_: Type = Field(alias="type")
    explanation: str | None = None


class Command(Suggestion):
    command: str


class Documentation(Suggestion):
    url: str


class Response(BaseModel):
    error: str
    suggestions: dict[str, Union[Suggestion, Command, Documentation]]
