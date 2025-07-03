import httpx

async def is_valid_problem_id(problem_id: int) -> bool:
    url = f"http://problem_service:8002/problems/{problem_id}"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url)
        return resp.status_code == 200
