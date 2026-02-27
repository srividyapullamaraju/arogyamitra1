"""
YouTube Data API v3 integration — search for exercise tutorial videos.
Falls back to generating YouTube search URLs if no API key is configured.
"""
import os
import httpx
from typing import Optional

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY", "")
YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"


async def search_exercise_video(query: str, max_results: int = 1) -> dict:
    """
    Search YouTube for an exercise tutorial video.
    Returns { video_id, title, thumbnail, url } or a fallback search link.
    """
    # If key looks real, try the API
    if YOUTUBE_API_KEY and not YOUTUBE_API_KEY.startswith("your_"):
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(YOUTUBE_SEARCH_URL, params={
                    "part": "snippet",
                    "q": f"{query} exercise proper form tutorial",
                    "type": "video",
                    "maxResults": max_results,
                    "key": YOUTUBE_API_KEY,
                    "videoDuration": "medium",
                    "relevanceLanguage": "en",
                })
                if resp.status_code == 200:
                    data = resp.json()
                    items = data.get("items", [])
                    if items:
                        item = items[0]
                        video_id = item["id"]["videoId"]
                        return {
                            "video_id": video_id,
                            "title": item["snippet"]["title"],
                            "thumbnail": item["snippet"]["thumbnails"]["high"]["url"],
                            "url": f"https://www.youtube.com/watch?v={video_id}",
                            "embed_url": f"https://www.youtube.com/embed/{video_id}",
                            "source": "youtube_api",
                        }
                else:
                    print(f"⚠️ YouTube API error {resp.status_code}: {resp.text[:200]}")
        except Exception as e:
            print(f"⚠️ YouTube API request failed: {e}")

    # Fallback: return a search URL (no API key needed)
    return _fallback_video(query)


async def search_exercise_videos(query: str, max_results: int = 3) -> list:
    """Search for multiple exercise videos."""
    if YOUTUBE_API_KEY and not YOUTUBE_API_KEY.startswith("your_"):
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(YOUTUBE_SEARCH_URL, params={
                    "part": "snippet",
                    "q": f"{query} exercise tutorial",
                    "type": "video",
                    "maxResults": max_results,
                    "key": YOUTUBE_API_KEY,
                })
                if resp.status_code == 200:
                    data = resp.json()
                    results = []
                    for item in data.get("items", []):
                        video_id = item["id"]["videoId"]
                        results.append({
                            "video_id": video_id,
                            "title": item["snippet"]["title"],
                            "thumbnail": item["snippet"]["thumbnails"]["medium"]["url"],
                            "url": f"https://www.youtube.com/watch?v={video_id}",
                            "embed_url": f"https://www.youtube.com/embed/{video_id}",
                            "source": "youtube_api",
                        })
                    return results
        except Exception as e:
            print(f"⚠️ YouTube API request failed: {e}")

    return [_fallback_video(query)]


def _fallback_video(query: str) -> dict:
    """Generate a fallback YouTube search link when no API key is available."""
    from urllib.parse import quote_plus
    search_query = quote_plus(f"{query} exercise proper form")
    return {
        "video_id": None,
        "title": f"Search: {query}",
        "thumbnail": None,
        "url": f"https://www.youtube.com/results?search_query={search_query}",
        "embed_url": f"https://www.youtube.com/embed?listType=search&list={search_query}",
        "source": "fallback",
    }


def get_youtube_embed_url(exercise_name: str, search_query: Optional[str] = None) -> str:
    """Synchronous helper — get embed URL for an exercise."""
    from urllib.parse import quote_plus
    q = search_query or f"{exercise_name} exercise proper form"
    return f"https://www.youtube.com/embed?listType=search&list={quote_plus(q)}"
