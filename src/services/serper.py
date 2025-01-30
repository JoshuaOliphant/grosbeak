import httpx

base_url = "https://r.jina.ai/"


async def search(url: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(base_url + url)
        return response.text()