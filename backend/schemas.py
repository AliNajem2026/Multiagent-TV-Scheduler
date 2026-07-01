from pydantic import BaseModel


class Program(BaseModel):
    title: str
    category: str
    duration: int


class ScheduleRequest(BaseModel):
    day: str


class ScheduleSlot(BaseModel):
    time: str
    title: str
    category: str
    duration: int


class ScheduleResponse(BaseModel):
    schedule: list[ScheduleSlot]
