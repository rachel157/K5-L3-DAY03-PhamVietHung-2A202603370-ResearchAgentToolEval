import urllib.request
import json
import urllib.parse

def wikipedia(title: str) -> dict:
    if not title or not isinstance(title, str) or not title.strip():
        return {"error": "Title string cannot be empty."}
    try:
        safe_title = urllib.parse.quote(title.strip().replace(" ", "_"))
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{safe_title}"
        req = urllib.request.Request(url, headers={"User-Agent": "ResearchAgent-Lab"})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode("utf-8"))
            return {
                "title": data.get("title"),
                "extract": data.get("extract"),
                "url": data.get("content_urls", {}).get("desktop", {}).get("page")
            }
    except Exception as e:
        return {"error": f"Wikipedia lookup failed for '{title}': {str(e)}"}