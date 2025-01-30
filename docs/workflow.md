# Grosbeak Resume Generation Workflow

## Overview
The Grosbeak system uses multiple AI agents working in sequence to generate an optimized resume tailored to a specific job description. The system orchestrates the collection of data from various sources and processes it through specialized agents to produce the final result.

## Data Sources
1. Job Description (via web scraping)
2. LinkedIn Profile (via web scraping)
3. Existing Resume (from file)
4. GitHub Profile (optional)

## Core Components

### Services
1. **WebScraper**: Handles fetching and parsing job descriptions and LinkedIn profiles
2. **GithubScraper**: Fetches GitHub profile information
3. **LLM Client**: Uses Anthropic's Claude 3 Sonnet for AI processing

### AI Agents
1. **ExistingResumeAgent**: Specializes in tailoring existing resumes to job descriptions
2. **LinkedInAgent**: Creates resumes from LinkedIn profiles
3. **AggregatorAgent**: Combines and optimizes multiple resume versions

## Workflow Steps

1. **Data Collection** (Concurrent)
   - Fetch and parse job description
   - Fetch and parse LinkedIn profile
   - Read existing resume file
   - Fetch GitHub information (if URL provided)

2. **Initial Resume Generation** (Concurrent)
   - ExistingResumeAgent processes the data to create a tailored version of the existing resume
   - LinkedInAgent processes the data to create a resume from the LinkedIn profile

3. **Final Optimization**
   - AggregatorAgent combines both versions and creates an optimized final resume

4. **Output**
   - Final resume is written to the specified output file in Markdown format

## Agent Prompts and Responsibilities

### ExistingResumeAgent
**Role**: Resume tailoring specialist
**Tasks**:
- Analyze existing resume and job description
- Customize resume to match job requirements
- Maintain original resume structure
- Incorporate relevant LinkedIn and GitHub information
- Preserve dates and factual information
- Use action verbs and quantify achievements

### LinkedInAgent
**Role**: LinkedIn profile analyzer and resume creator
**Tasks**:
- Create structured resume from LinkedIn data
- Align content with job requirements
- Incorporate GitHub projects
- Use chronological format (unless another format is more suitable)
- Create tailored summary/objective
- Prioritize skills and certifications by relevance

### AggregatorAgent
**Role**: Resume optimization specialist
**Tasks**:
- Compare and combine two resume versions
- Ensure perfect alignment with job description
- Incorporate any missed relevant information
- Optimize structure and formatting
- Create compelling summary
- Ensure appropriate length (1-2 pages)
- Maintain consistency throughout

## Error Handling
- Validates job information and LinkedIn profile data
- Logs errors using logfire
- Raises appropriate exceptions with descriptive messages

## Technical Details
- Uses asyncio for concurrent operations
- Implements proper error handling and logging
- Uses Pydantic models for data validation
- Supports markdown formatting for output
