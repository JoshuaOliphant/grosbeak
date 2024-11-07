from typing import Dict, Any, Union
from src.config import get_settings
import json
import httpx

settings = get_settings()

serper_scrape_url = "https://scrape.serper.dev"
headers = {
    "X-API-KEY": settings.SERPER_API_KEY,
    "Content-Type": "application/json"
}

def scrape_text_from_url(url: str) -> str:
    """
    Scrapes text content from a given URL.

    Args:
        url (str): The URL to scrape content from

    Returns:
        str: The text content scraped from the URL
    """
    payload = json.dumps({"url": url})
    response = httpx.get(url, headers=headers)

    print(response.text)
    return response.text

tools = [
    {
        "name": "scrape_text_from_url",
        "description": "Scrape text content from a given URL.",
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "The URL to scrape content from."
                }
            },
            "required": ["customer_id"]
        }
    },
]

def process_tool_call(tool_name, tool_input) -> str:
    if tool_name == "scrape_text_from_url":
        return scrape_text_from_url(tool_input["url"])
    else:
        raise ValueError(f"Unknown tool: {tool_name}")
