from agents.resume_agent import ResumeAgent


class ExistingResumeAgent(ResumeAgent):
    name: str = "ExistingResumeAgent"
    description: str = (
        "Agent that creates a resume based on the user's existing resume and job description"
    )
