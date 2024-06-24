from openai import AsyncOpenAI
from src.services.web_scraper import WebScraper
from src.services.github_scraper import GithubScraper
import os
import aiofiles
import asyncio
import json
from src.agents.resume_agent import ResumeAgent
from src.agents.linkedin_agent import LinkedInAgent
from src.agents.existing_resume_agent import ExistingResumeAgent
from src.agents.aggregator_agent import AggregatorAgent
from src.models.resume import ResumeContent
from typing import Any, Dict
from src.utils.json_encoder import CustomJSONEncoder
import logfire


class Orchestrator:

    def __init__(self, llm_client: AsyncOpenAI, serper_api_key: str, github_api_key: str):
        self.llm_client = llm_client
        self.web_scraper = WebScraper(api_key=serper_api_key,
                                      llm_client=self.llm_client)
        self.github_scraper = GithubScraper(
            github_token=github_api_key)

    async def read_resume_file(self, file_path: str) -> str:
        try:
            async with aiofiles.open(file_path, mode="r") as file:
                return await file.read()
        except IOError as e:
            raise ValueError(
                f"Unable to read resume file at {file_path}: {str(e)}")

    async def process_with_agent(self, agent: ResumeAgent,
                                 context: Dict[str, Any]) -> ResumeContent:
        prompt = self.construct_prompt(agent, context)
        response = await self.llm_client.chat.completions.create(
            model="gpt-4o",
            response_model=ResumeContent,
            messages=[
                {
                    "role": "system",
                    "content":
                    f"You are the {agent.name}. {agent.description}",
                },
                {
                    "role": "user",
                    "content": prompt
                },
            ],
        )
        return response

    def construct_prompt(self, agent: ResumeAgent, context: Dict[str,
                                                                 Any]) -> str:
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
        job_info_task = self.web_scraper.fetch_and_parse_job_description(
            job_url)
        linkedin_profile_task = self.web_scraper.fetch_and_parse_linkedin_profile(
            linkedin_url)
        existing_resume_task = self.read_resume_file(resume_file_path)
        github_info_task = (self.github_scraper.fetch_github_info(github_url)
                            if github_url else asyncio.create_task(
                                asyncio.sleep(0)))

        job_information, linkedin_profile, existing_resume, github_info = (
            await asyncio.gather(
                job_info_task,
                linkedin_profile_task,
                existing_resume_task,
                github_info_task,
            ))

        context = {
            "job_information": job_information,
            "linkedin_profile": linkedin_profile,
            "existing_resume": existing_resume,
            "github_info": github_info,
        }

        # Process with ExistingResumeAgent and LinkedInAgent concurrently
        existing_resume_task = self.process_with_agent(ExistingResumeAgent(),
                                                       context)
        linkedin_resume_task = self.process_with_agent(LinkedInAgent(),
                                                       context)

        existing_resume_output, linkedin_resume_output = await asyncio.gather(
            existing_resume_task, linkedin_resume_task)

        # Prepare context for AggregatorAgent
        aggregator_context = {
            **context,
            "existing_resume_output": existing_resume_output.markdown_content,
            "linkedin_resume_output": linkedin_resume_output.markdown_content,
        }

        # Process with AggregatorAgent
        final_resume = await self.process_with_agent(AggregatorAgent(),
                                                     aggregator_context)

        return final_resume.markdown_content

    async def write_resume_to_file(self, resume_content: str,
                                   output_file_path: str) -> None:
        try:
            async with aiofiles.open(output_file_path, mode="w") as file:
                await file.write(resume_content)
            logfire.info(f"Resume successfully written to {output_file_path}")
        except IOError as e:
            logfire.error(
                f"Failed to write resume to file {output_file_path}: {str(e)}")
            raise
