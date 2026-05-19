from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class CalendarItem(BaseModel):
    title: str
    start_at: datetime
    end_at: datetime
    location: str | None = None
    organizer: str | None = None


class InboxItem(BaseModel):
    subject: str
    sender: str
    received_at: datetime | None = None
    is_read: bool = False
    importance: str = "normal"


class TaskItem(BaseModel):
    subject: str
    created_at: datetime | None = None
    status: str = "notStarted"
    is_important: bool = False


class BriefSourceError(BaseModel):
    source: str
    message: str


class TimeBlock(BaseModel):
    start_at: datetime
    end_at: datetime
    label: str
    rationale: str


class DayBrief(BaseModel):
    timezone: str
    generated_at: datetime
    calendar: list[CalendarItem] = Field(default_factory=list)
    inbox: list[InboxItem] = Field(default_factory=list)
    tasks: list[TaskItem] = Field(default_factory=list)
    source_errors: list[BriefSourceError] = Field(default_factory=list)
    priorities: list[str] = Field(default_factory=list)
    timeblocks: list[TimeBlock] = Field(default_factory=list)
