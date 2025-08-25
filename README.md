# 🎓 GradPath AI – Your Personalized Career Copilot

GradPath AI is an AI-powered career guidance platform that helps students and professionals explore AI/ML career paths.
It combines LLMs (OpenAI GPT), LangChain, LangGraph, API integrations, and interactive knowledge graphs to deliver personalized roadmaps, resources, and visual career maps.

# 🚀 Project Overview

Choosing a career path in AI/ML can be overwhelming. GradPath AI acts as a career copilot, enabling users to:

Chat with an AI agent about different AI/ML roles (e.g., Data Scientist, GenAI Engineer, NLP Engineer).

Fetch curated resources (YouTube tutorials & GitHub projects) relevant to each role.

Generate role-specific roadmaps including skills, tools, projects, and interview prep.

Visualize career knowledge graphs from AI-generated outputs, making career paths more intuitive.

Built with LangGraph (multi-agent orchestration), Streamlit (UI), and FastAPI (backend), this project demonstrates real-time AI streaming, tool integration, and knowledge graph visualization.

# ✨ Key Features

Conversational AI Agent: Ask questions like “What skills do I need to become a GenAI Engineer?” and get structured guidance.

Multi-Agent Orchestration: Uses LangGraph to route queries between the LLM and tools.

Streaming Responses: Token-level output streaming for a responsive, real-time chat experience.

Tool-Integrated Search:

Role Info Tool → Structured data from curated JSON (role_mapping.json)

YouTube Resource Tool → Top tutorials fetched via YouTube API

GitHub Project Tool → Popular projects fetched via GitHub API

Knowledge Graph Extraction: Convert AI answers into structured Cytoscape-style JSON (nodes + edges).

Interactive Visualization: Render graphs in Streamlit with st-link-analysis, with semantic coloring for Skills, Tools, Projects, Roadmaps.

Dual Deployment:

Streamlit Frontend – user interaction & visualization

FastAPI Backend – scalable streaming API for integration with other apps

# 🏗️ System Architecture

flowchart TD
    U[User] -->|Career Question| ST[Streamlit Frontend]
    ST -->|/chat request| API[FastAPI Backend]
    API --> LG[LangGraph Agent]
    LG -->|LLM reasoning| LLM[OpenAI GPT]
    LG -->|Fetch data| Tools[Role/YouTube/GitHub Tools]
    Tools --> LG
    LLM --> LG
    LG --> API
    API -->|Streaming tokens| ST
    ST -->|Optional: Build KG| KG[Knowledge Graph Formatter]
    KG -->|Nodes + Edges JSON| Viz[st-link-analysis Visualization]
    Viz --> U

# ⚙️ Tech Stack

LLMs & Orchestration: OpenAI GPT-4o, LangChain, LangGraph

Frontend: Streamlit

Backend: FastAPI + Uvicorn

Visualization: st-link-analysis (Cytoscape-based)

Data/Models: Pydantic, JSON schemas

APIs: YouTube Data API, GitHub REST API

Other: dotenv, requests, aiohttp

# 📂 Repository Structure

📦 GradPath-AI
 ┣ 📜 app.py                     # Streamlit frontend (chat + KG visualization)
 ┣ 📜 server.py                  # FastAPI backend (streaming responses)
 ┣ 📜 gradpath_graph.py          # Main LangGraph orchestration graph
 ┣ 📜 agent_graph.py             # Alternative agent graph with OpenAI Functions
 ┣ 📜 tools.py                   # LangChain tools (role info, YouTube, GitHub)
 ┣ 📜 resource_agent.py          # YouTube & GitHub API calls
 ┣ 📜 role_agent.py              # Loads role data from JSON
 ┣ 📜 role_mapping.json          # Curated career paths for multiple roles
 ┣ 📜 knowledge_graph_formatter.py # Extracts Cytoscape JSON graphs from AI answers
 ┣ 📜 app_link_analysis.py       # Standalone KG → Link Analysis Streamlit app
 ┣ 📜 requirements.txt           # Project dependencies
 ┣ 📜 .env                       # API keys (OpenAI, YouTube, GitHub)
 ┣ 📜 README.md                  # Documentation (this file)
 ┗ 📜 LICENSE

# 🔧 Setup Instructions

1️⃣ Clone the repo

git clone https://github.com/your-username/GradPath-AI.git

cd GradPath-AI

2️⃣ Install dependencies

pip install -r requirements.txt

3️⃣ Configure API keys

Create a .env file with:

OPENAI_API_KEY=your_openai_key

YOUTUBE_API_KEY=your_youtube_key

GITHUB_TOKEN=your_github_token

4️⃣ Run the FastAPI backend
uvicorn server:app --reload --port 8000

5️⃣ Run the Streamlit frontend
streamlit run app.py

▶️ Usage

Open Streamlit UI at http://localhost:8501.

Ask a question, e.g.:

“What’s the roadmap to become a GenAI Engineer?”

“Give me projects for Data Scientist interviews.”

Explore streaming answers in the chat window.

Expand the Knowledge Graph section → generate & visualize graph from assistant’s answer.

Explore interactive nodes/edges with semantic coloring.

