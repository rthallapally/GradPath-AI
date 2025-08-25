from langchain_core.tools import tool
from role_agent import load_role_data, get_role_details
from resource_agent import search_youtube_videos, search_github_repos

# Tool 1: Role Info Tool
@tool
def get_role_info(role: str) -> dict:
    """Return overview, skills, tools, projects, and interview topics for a given AI/ML role."""
    try:
        data = load_role_data()
        details = get_role_details(role, data)
        return details
    except Exception as e:
        return {"error": str(e)}

# Tool 2: YouTube Fetch Tool
@tool
def get_youtube_resources(role: str) -> list:
    """Return top 5 YouTube videos for the given AI/ML role."""
    try:
        query = f"{role} roadmap tutorial"
        return search_youtube_videos(query)
    except Exception as e:
        return [{"error": str(e)}]

# Tool 3: GitHub Project Tool
@tool
def get_github_projects(role: str) -> list:
    """Return top GitHub repositories related to the given role."""
    try:
        query = f"{role} machine learning projects"
        return search_github_repos(query)
    except Exception as e:
        return [{"error": str(e)}]
