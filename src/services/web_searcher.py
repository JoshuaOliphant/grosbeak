from typing import Any, Dict, List
import json
import aiohttp
import logfire


class WebSearcher:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://google.serper.dev/search"

    async def search(self, query: str) -> Dict[str, Any]:
        headers = {"X-API-KEY": self.api_key, "Content-Type": "application/json"}
        payload = json.dumps({"q": query})

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    self.base_url, headers=headers, data=payload
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        logfire.info(f"Successfully performed web search for {query}")
                        return self.parse_search_results(data)
                    else:
                        logfire.error(
                            f"Failed to perform web search for {query}. Status: {response.status}"
                        )
                        return {
                            "error": f"Failed to perform web search. Status: {response.status}"
                        }
            except Exception as e:
                logfire.error(
                    f"Exception occurred while performing web search for {query}: {e}"
                )
                return {"error": f"Exception occurred: {str(e)}"}

    def parse_search_results(self, data: Dict[str, Any]) -> Dict[str, Any]:
        parsed_results = {"organic_results": [], "images": [], "summary": ""}

        for result in data.get("organic", []):
            parsed_results["organic_results"].append(
                {
                    "title": result.get("title"),
                    "link": result.get("link"),
                    "snippet": result.get("snippet"),
                }
            )

        for image in data.get("images", []):
            parsed_results["images"].append(
                {
                    "title": image.get("title"),
                    "imageUrl": image.get("imageUrl"),
                    "link": image.get("link"),
                }
            )

        parsed_results["summary"] = self.generate_summary(
            parsed_results["organic_results"]
        )

        return parsed_results

    def generate_summary(self, organic_results: List[Dict[str, str]]) -> str:
        summary = "Based on the search results:\n"
        for i, result in enumerate(organic_results[:3]):
            summary += f"{i+1}. {result['title']}: {result['snippet']}\n"
        return summary
