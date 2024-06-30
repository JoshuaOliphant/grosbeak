from pydantic import BaseModel, Field
from typing import List, Optional


class JobInformation(BaseModel):
    title: str = Field(..., description="The title of the job position")
    company: str = Field(
        ..., description="The name of the company offering the job")
    location: str = Field(..., description="The location of the job")
    description: str = Field(..., description="A brief description of the job")
    seniority: Optional[str] = Field(
        None, description="The seniority level of the position")
    employment_type: Optional[str] = Field(
        None,
        description="The type of employment (e.g., full-time, part-time)")
    job_function: Optional[str] = Field(
        None, description="The primary function or department of the job")
    industries: Optional[str] = Field(
        None, description="The industries relevant to the job")
    full_description: str = Field(
        ..., description="The full, detailed description of the job")
    requirements: List[str] = Field(default_factory=list,
                                    description="List of key job requirements")
    qualifications: List[str] = Field(
        default_factory=list, description="List of desired qualifications")
    benefits: Optional[List[str]] = Field(
        None, description="List of benefits offered with the job")
