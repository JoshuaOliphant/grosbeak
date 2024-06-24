from pydantic import BaseModel


class ResumeAgent(BaseModel):
    name: str
    description: str
