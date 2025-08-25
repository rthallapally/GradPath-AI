import os
import requests
from dotenv import load_dotenv

load_dotenv()

# --- API Keys ---
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

# -----------------------
# 🔴 YouTube Search Agent
# -----------------------
def search_youtube_videos(query, max_results=5):
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "maxResults": max_results,
        "key": YOUTUBE_API_KEY
    }

    response = requests.get(url, params=params)
    if response.status_code != 200:
        print("YouTube API Error:", response.json())
        return []

    data = response.json()
    results = []

    for item in data.get("items", []):
        video_id = item["id"]["videoId"]
        title = item["snippet"]["title"]
        url = f"https://www.youtube.com/watch?v={video_id}"
        results.append({"title": title, "url": url})

    return results

# -----------------------
# 🟣 GitHub Search Agent
# -----------------------
def search_github_repos(query, max_results=5):
    url = "https://api.github.com/search/repositories"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}"
    }
    params = {
        "q": query,
        "sort": "stars",
        "order": "desc",
        "per_page": max_results
    }

    response = requests.get(url, headers=headers, params=params)
    if response.status_code != 200:
        print("GitHub API Error:", response.json())
        return []

    data = response.json()
    results = []

    for item in data.get("items", []):
        results.append({
            "name": item["name"],
            "url": item["html_url"],
            "description": item.get("description", "No description")
        })

    return results
