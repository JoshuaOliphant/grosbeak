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
from typing import Any, Dict, Optional
from src.utils.json_encoder import CustomJSONEncoder
import logfire


class Orchestrator:

    def __init__(self, llm_client: AsyncOpenAI, serper_api_key: str,
                 github_api_key: str):
        self.llm_client = llm_client
        self.web_scraper = WebScraper(api_key=serper_api_key,
                                      llm_client=self.llm_client)
        self.github_scraper = GithubScraper(github_token=github_api_key)

    async def read_resume_file(self, file_path: str) -> str:
        try:
            async with aiofiles.open(file_path, mode="r") as file:
                return await file.read()
        except IOError as e:
            raise ValueError(
                f"Unable to read resume file at {file_path}: {str(e)}")

    async def process_with_agent(
        self, agent: ResumeAgent, context: Dict[str, Any]
    ) -> ResumeContent:
        prompt = self.construct_prompt(agent, context)
        try:
            response = await self.llm_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": f"You are the {agent.name}. {agent.description}",
                    },
                    {"role": "user", "content": prompt},
                ],
            )

            # Extract the content from the response
            content = response.choices[0].message.content

            # Create a ResumeContent object
            resume_content = ResumeContent(content)

            logfire.info(f"Successfully processed with {agent.name}")
            return resume_content
        except Exception as e:
            logfire.error(f"Error processing with {agent.name}: {str(e)}")
            raise ValueError(f"Failed to process with {agent.name}: {str(e)}")

    def construct_prompt(self, agent: ResumeAgent, context: Dict[str,
                                                                 Any]) -> str:
        if isinstance(agent, ExistingResumeAgent):
            return f"""
            Role: You are an expert resume tailoring specialist. Your task is to customize an existing resume to perfectly match a specific job description.

            Task: Analyze the provided existing resume and job description. Then, create a tailored version of the resume that highlights the most relevant skills, experiences, and achievements for the target position.

            Existing Resume:
            {context['existing_resume']}

            Job Description:
            {json.dumps(context['job_information'].dict(), indent=2, cls=CustomJSONEncoder)}

            Additional Context:
            LinkedIn Profile: {json.dumps(context['linkedin_profile'].dict(), indent=2, cls=CustomJSONEncoder)}
            GitHub Information: {json.dumps(context['github_info'], indent=2, cls=CustomJSONEncoder)}

            Instructions:
            1. Maintain the overall structure of the existing resume.
            2. Highlight skills and experiences that directly relate to the job description.
            3. Incorporate relevant information from the LinkedIn profile and GitHub account to strengthen the resume.
            4. Ensure all dates and factual information from the original resume are preserved.
            5. Use action verbs and quantify achievements where possible.
            6. Tailor the summary/objective statement to the specific job.
            7. Adjust the order of experiences or skills if it better matches the job requirements.

            Expected Output:
            Provide the tailored resume in Markdown format. The output should be a complete, ready-to-use resume that best positions the candidate for the specific job opportunity.
            """

        elif isinstance(agent, LinkedInAgent):
            return f"""
            Role: You are an expert LinkedIn profile analyzer and resume creator. Your task is to craft a comprehensive resume based on a LinkedIn profile, while taking into account a specific job description.

            Task: Analyze the provided LinkedIn profile and job description. Then, create a detailed resume that showcases the candidate's qualifications and experience in a way that aligns with the target position.

            LinkedIn Profile:
            {json.dumps(context['linkedin_profile'].dict(), indent=2, cls=CustomJSONEncoder)}

            Job Description:
            {json.dumps(context['job_information'].dict(), indent=2, cls=CustomJSONEncoder)}

            GitHub Information:
            {json.dumps(context['github_info'], indent=2, cls=CustomJSONEncoder)}

            Instructions:
            1. Create a well-structured resume using information from the LinkedIn profile.
            2. Highlight skills, experiences, and achievements that are most relevant to the job description.
            3. Incorporate relevant projects or contributions from the GitHub profile to showcase technical skills.
            4. Use a chronological format for work experience, unless a different format would better highlight the candidate's qualifications.
            5. Include a summary or objective statement tailored to the job opportunity.
            6. List skills, certifications, and education in order of relevance to the position.
            7. Use action verbs and quantify achievements where possible.

            Expected Output:
            Provide the created resume in Markdown format. The output should be a complete, professional resume that effectively presents the candidate's qualifications for the specific job opportunity.
            """

        elif isinstance(agent, AggregatorAgent):
            return f"""
            Role: You are an expert resume optimization specialist. Your task is to create the best possible resume by combining and refining input from multiple sources.

            Task: Analyze two different versions of a resume, along with the original job description, LinkedIn profile, and GitHub information. Then, create an optimized resume that incorporates the strongest elements from all sources.

            Resume from Existing Resume Agent:
            {context['existing_resume_output']}

            Resume from LinkedIn Agent:
            {context['linkedin_resume_output']}

            Job Description:
            {json.dumps(context['job_information'].dict(), indent=2, cls=CustomJSONEncoder)}

            LinkedIn Profile:
            {json.dumps(context['linkedin_profile'].dict(), indent=2, cls=CustomJSONEncoder)}

            GitHub Information:
            {json.dumps(context['github_info'], indent=2, cls=CustomJSONEncoder)}

            Instructions:
            1. Compare both input resumes and identify the strongest elements from each.
            2. Ensure the final resume is perfectly tailored to the job description.
            3. Incorporate any additional relevant information from the LinkedIn profile or GitHub account that may have been missed.
            4. Optimize the structure to best highlight the candidate's qualifications for this specific job.
            5. Ensure consistency in formatting and language throughout the resume.
            6. Craft a compelling summary/objective statement that encapsulates the candidate's value proposition for this role.
            7. Prioritize experiences and skills based on their relevance to the job description.
            8. Use strong action verbs and quantify achievements wherever possible.
            9. Ensure the resume length is appropriate (typically 1-2 pages) while including all crucial information.

            Expected Output:
            Provide the optimized resume in Markdown format. The output should be a polished, highly tailored resume that presents the candidate as the ideal fit for the specific job opportunity, drawing from all available information sources.
            """

        else:
            raise ValueError(f"Unknown agent type: {type(agent)}")

    async def process_resume_request(
        self,
        job_url: str,
        linkedin_url: str,
        resume_file_path: str,
        github_url: Optional[str] = None,
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

        # Check for errors in job_information and linkedin_profile
        if isinstance(job_information, dict) and "error" in job_information:
            logfire.error("Failed to fetch job information",
                          error=job_information["error"])
            raise ValueError(
                f"Failed to fetch job information: {job_information['error']}")

        if isinstance(linkedin_profile, dict) and "error" in linkedin_profile:
            logfire.error("Failed to fetch LinkedIn profile",
                          error=linkedin_profile["error"])
            raise ValueError(
                f"Failed to fetch LinkedIn profile: {linkedin_profile['error']}"
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

        return final_resume

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
