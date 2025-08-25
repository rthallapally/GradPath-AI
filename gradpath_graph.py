import os
from typing import TypedDict, Annotated, List
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END, add_messages
from langgraph.prebuilt import ToolNode

# ⬇️ your existing tools
from tools import get_role_info, get_youtube_resources, get_github_projects

load_dotenv()

# ---- State ----
class AgentState(TypedDict):
    messages: Annotated[List, add_messages]

# ---- Tools ----
tools = [get_role_info, get_youtube_resources, get_github_projects]

# ---- LLM (streaming ON) ----
llm = ChatOpenAI(model="gpt-4o", temperature=0, streaming=True).bind_tools(tools=tools)

def model_node(state: AgentState):
    # ask the model with the entire running message list
    msg = llm.invoke(state["messages"])
    return {"messages": [msg]}

def route_to_tool(state: AgentState):
    last = state["messages"][-1]
    has_calls = getattr(last, "tool_calls", None)
    return "tool" if has_calls else END

tool_node = ToolNode(tools=tools)

# ---- Graph ----
graph = StateGraph(AgentState)
graph.add_node("model", model_node)
graph.add_node("tool", tool_node)
graph.set_entry_point("model")
graph.add_conditional_edges("model", route_to_tool)
graph.add_edge("tool", "model")

compiled_graph = graph.compile()
