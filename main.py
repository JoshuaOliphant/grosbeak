import asyncio
import json
from typing import List, Dict, Any, Optional, TypeAlias, Union
from enum import Enum
from pydantic import BaseModel, Field, field_validator
import aiohttp
import aiofiles
import instructor
from openai import AsyncOpenAI
import chromadb
from chromadb.config import Settings
import logfire
import os
from datetime import datetime, timedelta, date

# Initialize Logfire
logfire.configure()

# Create a type alias for the Instructor-patched AsyncOpenAI client
InstructorClient: TypeAlias = (
    Any  # In reality, this is a patched version of AsyncOpenAI
)

# Create a single, global Instructor-patched OpenAI client
client: InstructorClient = instructor.patch(AsyncOpenAI())


class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, date):
            return obj.isoformat()
        if isinstance(obj, BaseModel):
            return obj.dict()
        return super().default(obj)


def flexible_date_parser(value):
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        if value.lower() in ["not available", "n/a", ""]:
            return None
        try:
            return date.fromisoformat(value)
        except ValueError:
            # Try parsing just the year
            try:
                return date(int(value), 1, 1)
            except ValueError:
                return None
    return None


class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, date):
            return obj.isoformat()
        return super().default(obj)


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


class CustomizedResume(BaseModel):
    markdown_content: str = Field(
        ..., description="The complete resume in Markdown format"
    )


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


class JobInformation(BaseModel):
    title: str = Field(..., description="The title of the job position")
    company: str = Field(..., description="The name of the company offering the job")
    location: str = Field(..., description="The location of the job")
    description: str = Field(..., description="A brief description of the job")
    seniority: Optional[str] = Field(
        None, description="The seniority level of the position"
    )
    employment_type: Optional[str] = Field(
        None, description="The type of employment (e.g., full-time, part-time)"
    )
    job_function: Optional[str] = Field(
        None, description="The primary function or department of the job"
    )
    industries: Optional[str] = Field(
        None, description="The industries relevant to the job"
    )
    full_description: str = Field(
        ..., description="The full, detailed description of the job"
    )
    requirements: List[str] = Field(
        default_factory=list, description="List of key job requirements"
    )
    qualifications: List[str] = Field(
        default_factory=list, description="List of desired qualifications"
    )
    benefits: Optional[List[str]] = Field(
        None, description="List of benefits offered with the job"
    )


class WebScraper:
    def __init__(self, api_key: str, llm_client: InstructorClient):
        self.api_key = api_key
        self.base_url = "https://scrape.serper.dev"
        self.llm_client = llm_client

    async def fetch_and_parse_job_description(self, url: str) -> JobInformation:
        headers = {"X-API-KEY": self.api_key, "Content-Type": "application/json"}
        payload = json.dumps({"url": url})

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    self.base_url, headers=headers, data=payload
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        logfire.info(f"Successfully fetched job description: \n {data}")
                        return await self.parse_serper_response(data)
                    else:
                        logfire.error(
                            f"Failed to fetch job description for {url}. Status: {response.status}"
                        )
                        raise ValueError(
                            f"Failed to fetch job description. Status: {response.status}"
                        )
            except Exception as e:
                logfire.error(
                    f"Exception occurred while fetching job description for {url}: {e}"
                )
                raise

    async def parse_serper_response(self, data: Dict[str, Any]) -> JobInformation:
        prompt = f"""
        Parse the following job description data and extract the relevant information:

        {json.dumps(data, indent=2)}

        Provide a structured output with the job information, including title, company, location, description, 
        seniority level, employment type, job function, industries, full description, key requirements, 
        qualifications, and benefits if available.
        """

        try:
            job_info = await self.llm_client.chat.completions.create(
                model="gpt-4o",
                response_model=JobInformation,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at parsing job descriptions and extracting relevant information.",
                    },
                    {"role": "user", "content": prompt},
                ],
            )
            logfire.info(
                f"Successfully parsed job information from Serper response: \n {job_info}"
            )
            return job_info
        except Exception as e:
            logfire.error(f"Failed to parse job information from Serper response: {e}")
            raise

    async def fetch_and_parse_linkedin_profile(
        self, linkedin_url: str
    ) -> Dict[str, Any]:
        headers = {"X-API-KEY": self.api_key, "Content-Type": "application/json"}
        payload = json.dumps({"url": linkedin_url})

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    self.base_url, headers=headers, data=payload
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        logfire.info(
                            "Successfully fetched LinkedIn profile", url=linkedin_url
                        )
                        return await self.parse_linkedin_data(data)
                    else:
                        logfire.error(
                            f"Failed to fetch LinkedIn profile: {linkedin_url} status: {response.status}",
                        )
                        raise ValueError(
                            f"Failed to fetch LinkedIn profile: {linkedin_url} Status: {response.status}"
                        )
            except Exception as e:
                logfire.error(
                    "Exception occurred while fetching LinkedIn profile",
                    url=linkedin_url,
                    error=str(e),
                )
                raise

    async def parse_linkedin_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            linkedin_info = await self.llm_client.chat.completions.create(
                model="gpt-4-1106-preview",
                response_model=LinkedInProfile,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at parsing LinkedIn profiles and extracting comprehensive information.",
                    },
                    {"role": "user", "content": self.construct_linkedin_prompt(data)},
                ],
            )
            logfire.info(
                "Successfully parsed LinkedIn profile", name=linkedin_info.full_name
            )
            return linkedin_info.dict()
        except Exception as e:
            logfire.error(f"Failed to parse LinkedIn profile: {str(e)}")
            return {"error": f"Failed to parse LinkedIn profile: {str(e)}"}

    def construct_linkedin_prompt(self, data: Dict[str, Any]) -> str:
        return f"""
        Parse the following LinkedIn profile data and extract comprehensive information including:
        1. Full name
        2. Current position and company
        3. Location
        4. About/Summary section
        5. Work experience (for each position: company, title, dates, description)
        6. Education (for each entry: school, degree, field of study, dates)
        7. Skills
        8. Certifications
        9. Projects
        10. Publications
        11. Volunteer experience
        12. Languages
        13. Any other relevant sections

        For dates, if the exact date is not available, provide the year or 'not available'.

        LinkedIn Data:
        {json.dumps(data, indent=2)}

        Provide a structured output with all available information from the LinkedIn profile.
        If any information is not available, use null or an empty list as appropriate.
        """


class WebSearcher:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://google.serper.dev/search"

    async def search(self, query: str) -> Dict[str, Any]:
        headers = {"X-API-KEY": self.api_key, "Content-Type": "application/json"}
        payload = json.dumps({"q": query})

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    self.base_url, headers=headers, data=payload
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        logfire.info(f"Successfully performed web search for {query}")
                        return self.parse_search_results(data)
                    else:
                        logfire.error(
                            f"Failed to perform web search for {query}. Status: {response.status}"
                        )
                        return {
                            "error": f"Failed to perform web search. Status: {response.status}"
                        }
            except Exception as e:
                logfire.error(
                    f"Exception occurred while performing web search for {query}: {e}"
                )
                return {"error": f"Exception occurred: {str(e)}"}

    def parse_search_results(self, data: Dict[str, Any]) -> Dict[str, Any]:
        parsed_results = {"organic_results": [], "images": [], "summary": ""}

        for result in data.get("organic", []):
            parsed_results["organic_results"].append(
                {
                    "title": result.get("title"),
                    "link": result.get("link"),
                    "snippet": result.get("snippet"),
                }
            )

        for image in data.get("images", []):
            parsed_results["images"].append(
                {
                    "title": image.get("title"),
                    "imageUrl": image.get("imageUrl"),
                    "link": image.get("link"),
                }
            )

        parsed_results["summary"] = self.generate_summary(
            parsed_results["organic_results"]
        )

        return parsed_results

    def generate_summary(self, organic_results: List[Dict[str, str]]) -> str:
        summary = "Based on the search results:\n"
        for i, result in enumerate(organic_results[:3]):
            summary += f"{i+1}. {result['title']}: {result['snippet']}\n"
        return summary


class ChromaContextStore:
    def __init__(self, name: str):
        self.name = name
        self.client = chromadb.Client(Settings(is_persistent=False))
        self.collection = self.client.create_collection(name)

    async def add(self, content: str, embedding: List[float], metadata: Dict = None):
        self.collection.add(
            documents=[content],
            embeddings=[embedding],
            metadatas=[metadata] if metadata else None,
            ids=[str(self.collection.count() + 1)],
        )
        logfire.info(
            f"Added content to context store {self.name}",
        )

    async def search(self, query_embedding: List[float], top_k: int = 5) -> List[str]:
        results = self.collection.query(
            query_embeddings=[query_embedding], n_results=top_k
        )
        logfire.info(
            f"Searched context store {self.name} with {top_k} results",
        )
        return results["documents"][0]


class ContextManager:
    def __init__(self):
        self.threads: Dict[str, Thread] = {}

    def create_thread(self, thread_id: str) -> Thread:
        if thread_id in self.threads:
            raise ValueError(f"Thread with id {thread_id} already exists")
        thread = Thread(id=thread_id)
        self.threads[thread_id] = thread
        logfire.info(f"Created new thread: {thread_id}")
        return thread

    def get_thread(self, thread_id: str) -> Thread:
        if thread_id not in self.threads:
            raise ValueError(f"Thread with id {thread_id} does not exist")
        return self.threads[thread_id]

    def add_message(self, thread_id: str, role: str, content: str):
        thread = self.get_thread(thread_id)
        message = Message(role=role, content=content)
        thread.messages.append(message)
        logfire.info(
            f"Added message to thread: {thread_id}",
        )

    def get_messages(self, thread_id: str) -> List[Message]:
        return self.get_thread(thread_id).messages

    def clear_thread(self, thread_id: str):
        if thread_id in self.threads:
            del self.threads[thread_id]
            logfire.info(f"Cleared thread: {thread_id}")


class LLMInteractionManager:
    def __init__(self, llm_client: InstructorClient, context_manager: ContextManager):
        self.llm_client = llm_client
        self.context_manager = context_manager

    async def process_with_llm(
        self, thread_id: str, user_input: str, response_model: Any
    ) -> Any:
        self.context_manager.add_message(thread_id, "user", user_input)
        messages = self.context_manager.get_messages(thread_id)
        response = await self.llm_client.chat.completions.create(
            model="gpt-4o",
            response_model=response_model,
            messages=[{"role": m.role, "content": m.content} for m in messages],
        )
        self.context_manager.add_message(thread_id, "assistant", str(response))
        return response


class GithubScraper:
    def __init__(self, github_token: str):
        self.github_token = github_token
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {self.github_token}",
            "Accept": "application/vnd.github.v3+json",
        }

    def extract_username(self, github_url: str) -> str:
        parts = github_url.strip("/").split("/")
        return parts[-1] if parts else ""

    async def fetch_github_info(self, github_url: str) -> Dict[str, Any]:
        username = self.extract_username(github_url)
        if not username:
            logfire.error(f"Invalid GitHub URL: {github_url}")
            return {"error": "Invalid GitHub URL"}

        async with aiohttp.ClientSession() as session:
            user_info = await self.fetch_user_info(session, username)
            if not user_info:
                return {"error": f"GitHub user {username} not found"}

            repos = await self.fetch_repos(session, username)
            contributions = await self.fetch_contributions(session, username)

            return {
                "url": github_url,
                "user_info": user_info,
                "repos": repos,
                "contributions": contributions,
            }

    async def fetch_user_info(
        self, session: aiohttp.ClientSession, username: str
    ) -> Dict[str, Any]:
        url = f"{self.base_url}/users/{username}"
        async with session.get(url, headers=self.headers) as response:
            if response.status == 200:
                data = await response.json()
                return {
                    "name": data.get("name"),
                    "bio": data.get("bio"),
                    "public_repos": data.get("public_repos"),
                    "followers": data.get("followers"),
                    "following": data.get("following"),
                    "created_at": data.get("created_at"),
                }
            else:
                logfire.error(f"Failed to fetch user info for {url}: {response.status}")
                return {}

    async def fetch_repos(
        self, session: aiohttp.ClientSession, username: str
    ) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/users/{username}/repos"
        repos = []
        page = 1
        per_page = 100

        while True:
            async with session.get(
                url, headers=self.headers, params={"page": page, "per_page": per_page}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if not data:
                        break
                    repos.extend(
                        [
                            {
                                "name": repo["name"],
                                "description": repo["description"],
                                "stars": repo["stargazers_count"],
                                "forks": repo["forks_count"],
                                "language": repo["language"],
                            }
                            for repo in data
                        ]
                    )
                    page += 1
                else:
                    logfire.error(f"Failed to fetch repos for {url}: {response.status}")
                    break

        return repos

    async def fetch_contributions(
        self, session: aiohttp.ClientSession, username: str
    ) -> int:
        # GitHub API doesn't provide a direct way to get contribution count
        # We'll approximate it by counting commits in the last year
        url = f"{self.base_url}/search/commits"
        headers = {**self.headers, "Accept": "application/vnd.github.cloak-preview"}
        one_year_ago = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
        query = f"author:{username} committer-date:>{one_year_ago}"

        async with session.get(
            url, headers=headers, params={"q": query, "per_page": 1}
        ) as response:
            if response.status == 200:
                data = await response.json()
                return data.get("total_count", 0)
            else:
                logfire.error(
                    f"Failed to fetch contributions for {username}: {response.status}"
                )
                return 0

    async def fetch_languages(
        self, session: aiohttp.ClientSession, username: str
    ) -> Dict[str, int]:
        languages = {}
        repos = await self.fetch_repos(session, username)

        for repo in repos:
            url = f"{self.base_url}/repos/{username}/{repo['name']}/languages"
            async with session.get(url, headers=self.headers) as response:
                if response.status == 200:
                    repo_languages = await response.json()
                    for lang, bytes_count in repo_languages.items():
                        languages[lang] = languages.get(lang, 0) + bytes_count
                else:
                    logfire.error(
                        f"Failed to fetch languages for repo {repo['name']}: {response.status}"
                    )

        return languages


class InputParser:
    def parse_input(
        self,
        job_url: str,
        github_url: str = None,
        linkedin_profile: str = None,
    ) -> Dict[str, Any]:
        parsed_input = {
            "job_url": job_url,
            "github_url": github_url,
            "linkedin_profile": linkedin_profile,
        }
        logfire.info(f"Parsed user input: {parsed_input}")
        return parsed_input


class ResumeAgent(BaseModel):
    name: str
    description: str


class ExistingResumeAgent(ResumeAgent):
    name: str = "ExistingResumeAgent"
    description: str = (
        "Agent that creates a resume based on the user's existing resume and job description"
    )


class LinkedInAgent(ResumeAgent):
    name: str = "LinkedInAgent"
    description: str = (
        "Agent that creates a resume based on LinkedIn profile and job description"
    )


class AggregatorAgent(ResumeAgent):
    name: str = "AggregatorAgent"
    description: str = "Agent that combines and refines resumes from other agents"


class ResumeContent(BaseModel):
    markdown_content: str = Field(
        ..., description="The complete resume in Markdown format"
    )


class Orchestrator:
    def __init__(self, llm_client: AsyncOpenAI):
        self.llm_client = llm_client
        self.web_scraper = WebScraper(
            api_key=os.environ.get("SERPER_API_KEY"), llm_client=self.llm_client
        )
        self.github_scraper = GithubScraper(
            github_token=os.environ.get("GITHUB_API_KEY")
        )

    async def read_resume_file(self, file_path: str) -> str:
        try:
            async with aiofiles.open(file_path, mode="r") as file:
                return await file.read()
        except IOError as e:
            raise ValueError(f"Unable to read resume file at {file_path}: {str(e)}")

    async def process_with_agent(
        self, agent: ResumeAgent, context: Dict[str, Any]
    ) -> ResumeContent:
        prompt = self.construct_prompt(agent, context)
        response = await self.llm_client.chat.completions.create(
            model="gpt-4o",
            response_model=ResumeContent,
            messages=[
                {
                    "role": "system",
                    "content": f"You are the {agent.name}. {agent.description}",
                },
                {"role": "user", "content": prompt},
            ],
        )
        return response

    def construct_prompt(self, agent: ResumeAgent, context: Dict[str, Any]) -> str:
        if isinstance(agent, ExistingResumeAgent):
            return f"""
            Create a tailored resume based on the following information:
            1. Existing Resume: {context['existing_resume']}
            2. Job Description: {json.dumps(context['job_information'].dict(), indent=2, cls=CustomJSONEncoder)}

            The new resume should:
            1. Be in Markdown format.
            2. Maintain the overall structure and content of the existing resume.
            3. Tailor the content to highlight skills and experiences relevant to the job description.
            4. Ensure all dates and other factual information from the original resume are preserved.
            """
        elif isinstance(agent, LinkedInAgent):
            return f"""
            Create a comprehensive resume based on the following information:
            1. LinkedIn Profile: {json.dumps(context['linkedin_profile'], indent=2, cls=CustomJSONEncoder)}
            2. Job Description: {json.dumps(context['job_information'].dict(), indent=2, cls=CustomJSONEncoder)}
            3. GitHub Information: {json.dumps(context['github_info'], indent=2, cls=CustomJSONEncoder)}

            The resume should:
            1. Be in Markdown format.
            2. Include all relevant professional experiences from the LinkedIn profile.
            3. Highlight skills and experiences that match the job description.
            4. Incorporate relevant information from the GitHub profile, if available.
            """
        elif isinstance(agent, AggregatorAgent):
            return f"""
            Combine and refine the following two resumes into a single, improved resume:
            1. Resume from Existing Resume Agent: {context['existing_resume_output']}
            2. Resume from LinkedIn Agent: {context['linkedin_resume_output']}

            The final resume should:
            1. Be in Markdown format.
            2. Incorporate the best elements from both input resumes.
            3. Ensure all information is consistent and complementary.
            4. Be tailored to the job description: {json.dumps(context['job_information'].dict(), indent=2, cls=CustomJSONEncoder)}
            5. Be comprehensive yet concise, highlighting the most relevant skills and experiences.
            """
        else:
            raise ValueError(f"Unknown agent type: {type(agent)}")

    async def process_resume_request(
        self,
        job_url: str,
        linkedin_url: str,
        resume_file_path: str,
        github_url: str = None,
    ) -> str:
        # Gather all necessary information concurrently
        job_info_task = self.web_scraper.fetch_and_parse_job_description(job_url)
        linkedin_profile_task = self.web_scraper.fetch_and_parse_linkedin_profile(
            linkedin_url
        )
        existing_resume_task = self.read_resume_file(resume_file_path)
        github_info_task = (
            self.github_scraper.fetch_github_info(github_url)
            if github_url
            else asyncio.create_task(asyncio.sleep(0))
        )

        job_information, linkedin_profile, existing_resume, github_info = (
            await asyncio.gather(
                job_info_task,
                linkedin_profile_task,
                existing_resume_task,
                github_info_task,
            )
        )

        context = {
            "job_information": job_information,
            "linkedin_profile": linkedin_profile,
            "existing_resume": existing_resume,
            "github_info": github_info,
        }

        # Process with ExistingResumeAgent and LinkedInAgent concurrently
        existing_resume_task = self.process_with_agent(ExistingResumeAgent(), context)
        linkedin_resume_task = self.process_with_agent(LinkedInAgent(), context)

        existing_resume_output, linkedin_resume_output = await asyncio.gather(
            existing_resume_task, linkedin_resume_task
        )

        # Prepare context for AggregatorAgent
        aggregator_context = {
            **context,
            "existing_resume_output": existing_resume_output.markdown_content,
            "linkedin_resume_output": linkedin_resume_output.markdown_content,
        }

        # Process with AggregatorAgent
        final_resume = await self.process_with_agent(
            AggregatorAgent(), aggregator_context
        )

        return final_resume.markdown_content

    async def write_resume_to_file(
        self, resume_content: str, output_file_path: str
    ) -> None:
        try:
            async with aiofiles.open(output_file_path, mode="w") as file:
                await file.write(resume_content)
            logfire.info(f"Resume successfully written to {output_file_path}")
        except IOError as e:
            logfire.error(
                f"Failed to write resume to file {output_file_path}: {str(e)}"
            )
            raise


async def main():
    client = instructor.patch(AsyncOpenAI())
    orchestrator = Orchestrator(client)

    resume_file_path = "existing_resume.md"
    output_file_path = "customized_resume.md"

    job_url = (
        "https://elicit.com/careers?ashby_jid=aa99e2e9-5b15-4cd3-ac9d-9c9177ff61c8"
    )
    github_url = "https://github.com/JoshuaOliphant"
    linkedin_url = "https://www.linkedin.com/in/joshuaoliphant/"

    try:
        final_resume = await orchestrator.process_resume_request(
            job_url, linkedin_url, resume_file_path, github_url
        )
        await orchestrator.write_resume_to_file(final_resume, output_file_path)
        print(f"Resume customization complete. Output written to: {output_file_path}")
    except Exception as e:
        logfire.error(f"An error occurred during resume customization: {str(e)}")
        print("An error occurred. Please check the logs for more information.")


if __name__ == "__main__":
    logfire.configure()
    asyncio.run(main())
