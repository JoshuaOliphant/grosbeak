from openai import AsyncOpenAI
import json
import aiohttp
import logfire
from typing import Dict, Any, Union
from src.models.job import JobInformation
from src.models.linkedin import LinkedInProfile


class WebScraper:

    def __init__(self, api_key: str, llm_client: AsyncOpenAI):
        self.api_key = api_key
        self.base_url = "https://scrape.serper.dev"
        self.llm_client = llm_client

    async def fetch_data(self, url: str) -> Union[str, Dict[str, str]]:
        """
        Fetches raw data from the given URL.
        """
        headers = {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json"
        }
        payload = json.dumps({"url": url})

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.base_url,
                                        headers=headers,
                                        data=payload) as response:
                    if response.status == 200:
                        return await response.text()
                    else:
                        logfire.error("Failed to fetch data",
                                      url=url,
                                      status=response.status)
                        return {
                            "error":
                            f"Failed to fetch data. Status: {response.status}"
                        }
        except aiohttp.ClientError as client_error:
            logfire.error("HTTP request failed",
                          url=url,
                          error=str(client_error))
            return {
                "error":
                f"Failed to fetch data due to network error: {str(client_error)}"
            }
        except Exception as e:
            logfire.error("Unexpected error occurred while fetching data",
                          url=url,
                          error=str(e))
            return {"error": f"Unexpected error: {str(e)}"}

    def parse_json(self,
                   content: str) -> Union[Dict[str, Any], Dict[str, str]]:
        """
        Parses a JSON string into a Python dictionary.
        """
        try:
            return json.loads(content)
        except json.JSONDecodeError as json_error:
            logfire.error("Failed to parse JSON", error=str(json_error))
            return {
                "error": f"Failed to parse response as JSON: {str(json_error)}"
            }

    def construct_job_prompt(self, data: Dict[str, Any]) -> str:
        """
        Constructs a prompt for the LLM to parse job description data.
        """
        return f"""
        Parse the following job description data and extract the relevant information:

        {json.dumps(data, indent=2)}

        Provide a structured output with the job information, including title, company, location, description, 
        seniority level, employment type, job function, industries, full description, key requirements, 
        qualifications, and benefits if available.
        """

    def construct_linkedin_prompt(self, data: Dict[str, Any]) -> str:
        """
        Constructs a prompt for the LLM to parse LinkedIn profile data.
        """
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

    async def query_llm(self, prompt: str,
                        response_model: Any) -> Union[Any, Dict[str, str]]:
        """
        Queries the LLM with the given prompt and returns the parsed information.
        """
        try:
            return await self.llm_client.chat.completions.create(
                model="gpt-4",
                response_model=response_model,
                messages=[
                    {
                        "role":
                        "system",
                        "content":
                        "You are an expert at parsing structured data and extracting relevant information.",
                    },
                    {
                        "role": "user",
                        "content": prompt
                    },
                ],
            )
        except Exception as e:
            logfire.error("Failed to query LLM", error=str(e))
            return {"error": f"Failed to parse information: {str(e)}"}

    async def fetch_job_description(self,
                                    url: str) -> Union[str, Dict[str, str]]:
        """
        Fetches the job description data from the given URL.
        """
        result = await self.fetch_data(url)
        if isinstance(result, dict) and "error" in result:
            return result
        logfire.info("Successfully fetched job description", url=url)
        return result

    def parse_job_description(
            self, content: str) -> Union[Dict[str, Any], Dict[str, str]]:
        """
        Parses the raw job description content into a structured dictionary.
        """
        result = self.parse_json(content)
        if isinstance(result, dict) and "error" in result:
            return result
        logfire.info("Successfully parsed job description JSON")
        return result

    async def process_job_description(
            self, data: Dict[str,
                             Any]) -> Union[JobInformation, Dict[str, str]]:
        """
        Processes the structured job description data through the LLM.
        """
        prompt = self.construct_job_prompt(data)
        result = await self.query_llm(prompt, JobInformation)
        if isinstance(result, dict) and "error" in result:
            return result
        logfire.info("Successfully processed job description through LLM")
        return result

    async def fetch_and_parse_job_description(
            self, url: str) -> Union[JobInformation, Dict[str, str]]:
        """
        Orchestrates the process of fetching, parsing, and processing a job description.
        """
        fetched_data = await self.fetch_job_description(url)
        if isinstance(fetched_data, dict) and "error" in fetched_data:
            return fetched_data

        parsed_data = self.parse_job_description(fetched_data)
        if isinstance(parsed_data, dict) and "error" in parsed_data:
            return parsed_data

        return await self.process_job_description(parsed_data)

    async def fetch_linkedin_profile(self,
                                     url: str) -> Union[str, Dict[str, str]]:
        """
        Fetches the LinkedIn profile data from the given URL.
        """
        result = await self.fetch_data(url)
        if isinstance(result, dict) and "error" in result:
            return result
        logfire.info("Successfully fetched LinkedIn profile", url=url)
        return result

    def parse_linkedin_profile(
            self, content: str) -> Union[Dict[str, Any], Dict[str, str]]:
        """
        Parses the raw LinkedIn profile content into a structured dictionary.
        """
        result = self.parse_json(content)
        if isinstance(result, dict) and "error" in result:
            return result
        logfire.info("Successfully parsed LinkedIn profile JSON")
        return result

    async def process_linkedin_profile(
            self, data: Dict[str,
                             Any]) -> Union[LinkedInProfile, Dict[str, str]]:
        """
        Processes the structured LinkedIn profile data through the LLM.
        """
        prompt = self.construct_linkedin_prompt(data)
        result = await self.query_llm(prompt, LinkedInProfile)
        if isinstance(result, dict) and "error" in result:
            return result
        logfire.info("Successfully processed LinkedIn profile through LLM")
        return result

    async def fetch_and_parse_linkedin_profile(
            self, url: str) -> Union[LinkedInProfile, Dict[str, str]]:
        """
        Orchestrates the process of fetching, parsing, and processing a LinkedIn profile.
        """
        fetched_data = await self.fetch_linkedin_profile(url)
        if isinstance(fetched_data, dict) and "error" in fetched_data:
            return fetched_data

        parsed_data = self.parse_linkedin_profile(fetched_data)
        if isinstance(parsed_data, dict) and "error" in parsed_data:
            return parsed_data

        return await self.process_linkedin_profile(parsed_data)
