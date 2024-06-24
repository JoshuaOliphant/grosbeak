from agents.resume_agent import ResumeAgent


class LinkedInAgent(ResumeAgent):
    name: str = "LinkedInAgent"
    description: str = (
        "Agent that creates a resume based on LinkedIn profile and job description"
    )
