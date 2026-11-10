import urllib.request
import json
import urllib.parse

def hackernews(query: str, limit: int = 5) -> dict:
    if not query or not isinstance(query, str) or not query.strip():
        return {"error": "Query string cannot be empty."}
    try:
        safe_query = urllib.parse.quote(query.strip())
        safe_limit = max(1, min(int(limit or 5), 10))
        url = f"https://hn.algolia.com/api/v1/search?query={safe_query}&tags=story&hitsPerPage={safe_limit}"
        req = urllib.request.Request(url, headers={"User-Agent": "ResearchAgent-Lab"})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode("utf-8"))
            hits = data.get("hits", [])
            results = [{
                "title": hit.get("title"),
                "url": hit.get("url"),
                "points": hit.get("points"),
                "author": hit.get("author"),
                "created_at": hit.get("created_at")
            } for hit in hits[:safe_limit]]
            return {"query": query, "count": len(results), "items": results}
    except Exception as e:
        return {"error": f"HackerNews search failed: {str(e)}"}