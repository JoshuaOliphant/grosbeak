from src.agents.resume_agent import ResumeAgent


class AggregatorAgent(ResumeAgent):
    name: str = "AggregatorAgent"
    description: str = "Agent that combines and refines resumes from other agents"
