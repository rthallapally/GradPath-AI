import os
from dotenv import load_dotenv
from typing import TypedDict, List, Any, Union
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langchain.agents import initialize_agent, AgentType
from langgraph.graph import StateGraph, END

from tools import get_role_info, get_youtube_resources, get_github_projects

# 1) Env
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# 2) State schema
class AgentState(TypedDict):
    input: str
    chat_history: List[BaseMessage]
    final_output: Any

# 3) LLM + Tools + Agent
tools = [get_role_info, get_youtube_resources, get_github_projects]

# Streaming ON; you can switch to "gpt-4o" or "gpt-4o-mini" if available
llm = ChatOpenAI(model="gpt-4", temperature=0, streaming=True)

# Turn verbose OFF to avoid console spam
agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.OPENAI_FUNCTIONS,
    verbose=False,                 # <- was True
    handle_parsing_errors=True     # small guard for bad tool JSON
)

def _as_ai_message(resp: Union[AIMessage, BaseMessage, dict, str]) -> AIMessage:
    """
    Normalize AgentExecutor output so we always push an AIMessage into chat_history.
    """
    if isinstance(resp, AIMessage):
        return resp
    if isinstance(resp, BaseMessage):
        return AIMessage(content=resp.content, additional_kwargs=getattr(resp, "additional_kwargs", {}))
    if isinstance(resp, dict) and "output" in resp:
        return AIMessage(content=str(resp["output"]))
    return AIMessage(content=str(resp))

# 4) LangGraph nodes
def run_agent_node(state: AgentState) -> AgentState:
    response = agent.invoke({
        "input": state["input"],
        "chat_history": state["chat_history"]
    })

    state["chat_history"].append(HumanMessage(content=state["input"]))
    state["chat_history"].append(_as_ai_message(response))
    return state

def run_tool_node(state: AgentState) -> AgentState:
    # If you want to surface intermediate tool results to the UI mid-stream,
    # you can write them into state["final_output"] here.
    state["final_output"] = state["chat_history"][-1]
    return state

def should_call_tool(state: AgentState) -> str:
    last = state["chat_history"][-1]
    # OPENAI_FUNCTIONS agent adds tool_calls on the AI message when it wants tools
    if hasattr(last, "tool_calls") and getattr(last, "tool_calls", None):
        return "call_tool"
    return "end"

# 5) Build graph
builder = StateGraph(AgentState)
builder.add_node("agent", run_agent_node)
builder.add_node("call_tool", run_tool_node)
builder.set_entry_point("agent")
builder.add_conditional_edges("agent", should_call_tool, {"call_tool": "call_tool", "end": END})
builder.add_edge("call_tool", "agent")

graph = builder.compile()
