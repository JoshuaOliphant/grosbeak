from pydantic import BaseModel
from typing import List, Dict
from enum import Enum


class Message(BaseModel):
    role: str
    content: str


class Thread(BaseModel):
    id: str
    messages: List[Message] = []


class EventType(Enum):
    INPUT = 1
    JOB_DESCRIPTION = 2
    CANDIDATE_PROFILE = 3
    SKILL_MATCH = 4
    RESUME_SECTION = 5
    PROCESSED = 6
    AGGREGATED = 7


class Event:
    def __init__(self, type: EventType, content: str, metadata: Dict = None):
        self.type = type
        self.content = content
        self.metadata = metadata or {}
