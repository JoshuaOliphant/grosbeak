from openai import AsyncOpenAI
import json
from src.models.job import JobInformation
import aiohttp
import logfire
from typing import Dict, Any
from src.models.linkedin import LinkedInProfile


class WebScraper:
    def __init__(self, api_key: str, llm_client: AsyncOpenAI):
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
                        data = await response .json()
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
