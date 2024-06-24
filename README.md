# Grosbeak: AI-Powered Resume Customizer

## Overview

This project is an AI-powered resume customization system that tailors a candidate's resume to a specific job description. It utilizes multiple data sources, including the candidate's existing resume, LinkedIn profile, and GitHub profile, to create a comprehensive and tailored resume.

## Features

- Asynchronous processing for efficient data gathering and resume generation
- Integration with OpenAI's GPT models for intelligent resume customization
- Web scraping capabilities for job descriptions and LinkedIn profiles
- GitHub profile analysis for additional context
- Multiple AI agents working in parallel:
  - ExistingResumeAgent: Tailors the existing resume to the job description
  - LinkedInAgent: Creates a resume based on LinkedIn profile and job description
  - AggregatorAgent: Combines and refines the output from other agents
- Markdown output format for easy editing and conversion

## Prerequisites

- Python 3.8+
- Poetry (for dependency management)

## Setup

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/ai-resume-customizer.git
   cd ai-resume-customizer
   ```

2. Install dependencies using Poetry:
   ```
   poetry install
   ```

3. Set up environment variables:
   Create a `.env` file in the project root and add the following:
   ```
   OPENAI_API_KEY=your_openai_api_key
   SERPER_API_KEY=your_serper_api_key
   GITHUB_API_KEY=your_github_api_key
   ```

## Usage

1. Prepare your input files:
   - Save your existing resume as a Markdown file (e.g., `existing_resume.md`)

2. Run the script:
   ```
   poetry run python main.py
   ```

3. When prompted, enter the following information:
   - Job posting URL
   - Your LinkedIn profile URL
   - Path to your existing resume file
   - Your GitHub profile URL (optional)

4. The script will process the information and generate a customized resume in Markdown format.

5. Find the output resume in the file specified (default: `customized_resume.md`).

## Configuration

You can modify the following parameters in the `main.py` file:

- `resume_file_path`: Path to your existing resume file
- `output_file_path`: Path where the customized resume will be saved

## How It Works

1. The system gathers information from multiple sources:
   - Scrapes the job description from the provided URL
   - Fetches and parses the LinkedIn profile
   - Reads the existing resume file
   - Retrieves GitHub profile information (if provided)

2. Three AI agents process the information concurrently:
   - ExistingResumeAgent tailors the existing resume to the job description
   - LinkedInAgent creates a resume based on the LinkedIn profile and job description
   - AggregatorAgent combines and refines the output from the other two agents

3. The final, customized resume is generated in Markdown format and saved to a file.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgements

- OpenAI for providing the GPT models
- Serper for web scraping capabilities
- GitHub for API access to user profiles