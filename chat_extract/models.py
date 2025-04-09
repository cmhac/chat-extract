"""Defines pydantic models for the groupchat text extraction API."""

from datetime import datetime
import typing as T

from pydantic import BaseModel, field_validator


class Message(BaseModel):
    """Defines one message in a text thread"""

    sender: T.Optional[T.Union[str, None]] = None
    message: T.Optional[T.Union[str, None]] = None
    timestamp: T.Optional[T.Union[str, datetime, None]] = None
    image_description: T.Optional[T.Union[str, None]] = None

    @classmethod
    @field_validator("timestamp", mode="before")
    def parse_timestamp(cls, v):
        """Converts a timestamp string to a datetime object"""
        if isinstance(v, str):
            try:
                return datetime.fromisoformat(v)
            except ValueError as exc:
                raise ValueError(
                    "timestamp must be a valid ISO format datetime string"
                ) from exc
        return v


class MessageList(BaseModel):
    """Defines a list of messages in a text thread"""

    messages: T.List[Message]
