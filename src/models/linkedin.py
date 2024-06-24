from typing import List, Optional, Union
from pydantic import BaseModel, Field, field_validator
from datetime import date
from src.utils.flexible_date_parser import flexible_date_parser


class Position(BaseModel):
    title: str
    company: str
    location: Optional[str] = None
    start_date: Optional[Union[date, str]] = None
    end_date: Optional[Union[date, str]] = None
    description: Optional[str] = None

    @field_validator("start_date", "end_date", mode="before")
    @classmethod
    def parse_dates(cls, value):
        return flexible_date_parser(value)


class Education(BaseModel):
    school: str
    degree: Optional[str] = None
    field_of_study: Optional[str] = None
    start_date: Optional[Union[date, str]] = None
    end_date: Optional[Union[date, str]] = None
    description: Optional[str] = None

    @field_validator("start_date", "end_date", mode="before")
    @classmethod
    def parse_dates(cls, value):
        return flexible_date_parser(value)


class Certification(BaseModel):
    name: str
    issuing_organization: str
    issue_date: Optional[Union[date, str]] = None
    expiration_date: Optional[Union[date, str]] = None
    credential_id: Optional[str] = None

    @field_validator("issue_date", "expiration_date", mode="before")
    @classmethod
    def parse_dates(cls, value):
        return flexible_date_parser(value)


class Skill(BaseModel):
    name: str
    endorsements: Optional[int] = None


class Project(BaseModel):
    name: str
    description: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    url: Optional[str] = None


class Publication(BaseModel):
    title: str
    publisher: str
    publication_date: Optional[date] = None
    description: Optional[str] = None
    url: Optional[str] = None


class VolunteerExperience(BaseModel):
    role: str
    organization: str
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    description: Optional[str] = None


class Language(BaseModel):
    language: str
    proficiency: Optional[str] = None


class LinkedInProfile(BaseModel):
    full_name: str
    headline: Optional[str] = None
    location: Optional[str] = None
    profile_url: str
    about: Optional[str] = None
    current_position: Optional[Position] = None
    experience: List[Position] = Field(default_factory=list)
    education: List[Education] = Field(default_factory=list)
    skills: List[Skill] = Field(default_factory=list)
    certifications: List[Certification] = Field(default_factory=list)
    projects: List[Project] = Field(default_factory=list)
    publications: List[Publication] = Field(default_factory=list)
    volunteer_experience: List[VolunteerExperience] = Field(default_factory=list)
    languages: List[Language] = Field(default_factory=list)
    recommendations: Optional[int] = None
    connections: Optional[int] = None

    class Config:
        json_schema_extra = {
            "example": {
                "full_name": "John Doe",
                "headline": "Senior Software Engineer",
                "location": "San Francisco Bay Area",
                "profile_url": "https://www.linkedin.com/in/johndoe",
                "about": "Passionate software engineer with 10+ years of experience...",
                "current_position": {
                    "title": "Senior Software Engineer",
                    "company": "Tech Corp",
                    "location": "San Francisco, CA",
                    "start_date": "2020-01-01",
                    "description": "Leading backend development team...",
                },
                "experience": [
                    {
                        "title": "Software Engineer",
                        "company": "StartUp Inc",
                        "location": "Palo Alto, CA",
                        "start_date": "2015-03-01",
                        "end_date": "2019-12-31",
                        "description": "Developed scalable microservices...",
                    }
                ],
                "education": [
                    {
                        "school": "Stanford University",
                        "degree": "Master of Science",
                        "field_of_study": "Computer Science",
                        "start_date": "2013-09-01",
                        "end_date": "2015-06-30",
                    }
                ],
                "skills": [
                    {"name": "Python", "endorsements": 50},
                    {"name": "Machine Learning", "endorsements": 30},
                ],
                "certifications": [
                    {
                        "name": "AWS Certified Solutions Architect",
                        "issuing_organization": "Amazon Web Services",
                        "issue_date": "2021-05-15",
                    }
                ],
                "projects": [
                    {
                        "name": "Open Source Contribution",
                        "description": "Contributed to TensorFlow...",
                        "url": "https://github.com/tensorflow/tensorflow/pull/12345",
                    }
                ],
                "publications": [
                    {
                        "title": "Advances in Distributed Systems",
                        "publisher": "Tech Journal",
                        "publication_date": "2022-03-01",
                        "url": "https://techjournal.com/article/12345",
                    }
                ],
                "volunteer_experience": [
                    {
                        "role": "Mentor",
                        "organization": "Code.org",
                        "start_date": "2018-01-01",
                        "description": "Mentoring high school students in programming",
                    }
                ],
                "languages": [
                    {"language": "English", "proficiency": "Native"},
                    {
                        "language": "Spanish",
                        "proficiency": "Professional working proficiency",
                    },
                ],
                "recommendations": 15,
                "connections": 500,
            }
        }
