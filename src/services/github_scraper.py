from typing import Any, Dict, List
from datetime import datetime, timedelta
import aiohttp
import logfire


class GithubScraper:
    def __init__(self, github_token: str):
        self.github_token = github_token
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {self.github_token}",
            "Accept": "application/vnd.github.v3+json",
        }

    def extract_username(self, github_url: str) -> str:
        parts = github_url.strip("/").split("/")
        return parts[-1] if parts else ""

    async def fetch_github_info(self, github_url: str) -> Dict[str, Any]:
        username = self.extract_username(github_url)
        if not username:
            logfire.error(f"Invalid GitHub URL: {github_url}")
            return {"error": "Invalid GitHub URL"}

        async with aiohttp.ClientSession() as session:
            user_info = await self.fetch_user_info(session, username)
            if not user_info:
                return {"error": f"GitHub user {username} not found"}

            repos = await self.fetch_repos(session, username)
            contributions = await self.fetch_contributions(session, username)

            return {
                "url": github_url,
                "user_info": user_info,
                "repos": repos,
                "contributions": contributions,
            }

    async def fetch_user_info(
        self, session: aiohttp.ClientSession, username: str
    ) -> Dict[str, Any]:
        url = f"{self.base_url}/users/{username}"
        async with session.get(url, headers=self.headers) as response:
            if response.status == 200:
                data = await response.json()
                return {
                    "name": data.get("name"),
                    "bio": data.get("bio"),
                    "public_repos": data.get("public_repos"),
                    "followers": data.get("followers"),
                    "following": data.get("following"),
                    "created_at": data.get("created_at"),
                }
            else:
                logfire.error(f"Failed to fetch user info for {url}: {response.status}")
                return {}

    async def fetch_repos(
        self, session: aiohttp.ClientSession, username: str
    ) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/users/{username}/repos"
        repos = []
        page = 1
        per_page = 100

        while True:
            async with session.get(
                url, headers=self.headers, params={"page": page, "per_page": per_page}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if not data:
                        break
                    repos.extend(
                        [
                            {
                                "name": repo["name"],
                                "description": repo["description"],
                                "stars": repo["stargazers_count"],
                                "forks": repo["forks_count"],
                                "language": repo["language"],
                            }
                            for repo in data
                        ]
                    )
                    page += 1
                else:
                    logfire.error(f"Failed to fetch repos for {url}: {response.status}")
                    break

        return repos

    async def fetch_contributions(
        self, session: aiohttp.ClientSession, username: str
    ) -> int:
        # GitHub API doesn't provide a direct way to get contribution count
        # We'll approximate it by counting commits in the last year
        url = f"{self.base_url}/search/commits"
        headers = {**self.headers, "Accept": "application/vnd.github.cloak-preview"}
        one_year_ago = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
        query = f"author:{username} committer-date:>{one_year_ago}"

        async with session.get(
            url, headers=headers, params={"q": query, "per_page": 1}
        ) as response:
            if response.status == 200:
                data = await response.json()
                return data.get("total_count", 0)
            else:
                logfire.error(
                    f"Failed to fetch contributions for {username}: {response.status}"
                )
                return 0

    async def fetch_languages(
        self, session: aiohttp.ClientSession, username: str
    ) -> Dict[str, int]:
        languages = {}
        repos = await self.fetch_repos(session, username)

        for repo in repos:
            url = f"{self.base_url}/repos/{username}/{repo['name']}/languages"
            async with session.get(url, headers=self.headers) as response:
                if response.status == 200:
                    repo_languages = await response.json()
                    for lang, bytes_count in repo_languages.items():
                        languages[lang] = languages.get(lang, 0) + bytes_count
                else:
                    logfire.error(
                        f"Failed to fetch languages for repo {repo['name']}: {response.status}"
                    )

        return languages
