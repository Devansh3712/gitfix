from enum import Enum
from typing import Union

from pydantic import BaseModel, ConfigDict, Field


class Type(str, Enum):
    COMMAND = "command"
    DOCUMENTATION = "documentation"
    OTHER = "other"


class Suggestion(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    type_: Type = Field(alias="type")
    explanation: str | None = None


class Command(Suggestion):
    command: str


class Documentation(Suggestion):
    url: str


class Response(BaseModel):
    error: str
    suggestions: dict[str, Union[Suggestion, Command, Documentation]]
