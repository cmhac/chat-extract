"""Defines pydantic models for the groupchat text extraction API."""

import typing as T

from pydantic import BaseModel


class Message(BaseModel):
    """Defines one message in a text thread"""

    sender: T.Union[str, None]
    message: T.Union[str, None]
    timestamp: T.Union[str, None]


class MessageList(BaseModel):
    """Defines a list of messages in a text thread"""

    messages: T.List[Message]
