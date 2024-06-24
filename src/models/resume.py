from pydantic import BaseModel, Field


class ResumeContent(BaseModel):
    markdown_content: str = Field(
        ..., description="The complete resume in Markdown format"
    )
