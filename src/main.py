import asyncio
import logfire
import instructor
from openai import AsyncOpenAI
from orchestrator import Orchestrator

# Initialize Logfire
logfire.configure()

# Create a single, global Instructor-patched OpenAI client
client = instructor.apatch(AsyncOpenAI())


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
