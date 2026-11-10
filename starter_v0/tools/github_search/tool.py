import urllib.request
import json
import urllib.parse

def github_search(query: str, sort: str = "stars", limit: int = 5) -> dict:
    if not query or not isinstance(query, str) or not query.strip():
        return {"error": "Query string cannot be empty."}
    try:
        safe_query = urllib.parse.quote(query.strip())
        safe_sort = sort if sort in ["stars", "forks", "updated"] else "stars"
        safe_limit = max(1, min(int(limit or 5), 10))
        url = f"https://api.github.com/search/repositories?q={safe_query}&sort={safe_sort}&per_page={safe_limit}"
        req = urllib.request.Request(url, headers={"User-Agent": "ResearchAgent-Lab", "Accept": "application/vnd.github.v3+json"})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode("utf-8"))
            items = data.get("items", [])
            results = [{
                "name": item.get("full_name"),
                "description": item.get("description"),
                "url": item.get("html_url"),
                "stars": item.get("stargazers_count"),
                "language": item.get("language")
            } for item in items[:safe_limit]]
            return {"query": query, "count": len(results), "items": results}
    except Exception as e:
        return {"error": f"GitHub search failed: {str(e)}"}