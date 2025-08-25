# # knowledge_graph_formatter.py
# # Generate strict Cytoscape / st-link-analysis JSON from arbitrary text via an LLM.

# from typing import List, Optional, Union
# from pydantic import BaseModel, Field, validator
# from langchain_openai import ChatOpenAI
# from langchain_core.prompts import ChatPromptTemplate
# from langchain_core.output_parsers import JsonOutputParser
# import json
# import re
# import uuid
# import os


# # ---------- Pydantic schema (Cytoscape / st-link-analysis friendly) ----------
# class NodeData(BaseModel):
#     id: str = Field(..., description="Unique ID for the node (no spaces)")
#     label: str = Field(..., description="Type/category of the node, e.g., PERSON, ORG, TOPIC")
#     name: str = Field(..., description="Short display name for the node")
#     description: Optional[str] = Field(None, description="1-2 sentence description")

# class Node(BaseModel):
#     data: NodeData

# class EdgeData(BaseModel):
#     id: str = Field(..., description="Unique ID for the edge (no spaces)")
#     source: str = Field(..., description="The source node ID")
#     target: str = Field(..., description="The target node ID")
#     label: Optional[str] = Field(None, description="Relationship label, e.g., FOUNDED, REPORTS_TO, MENTIONS")

# class Edge(BaseModel):
#     data: EdgeData

# class GraphPayload(BaseModel):
#     nodes: List[Node]
#     edges: List[Edge]

#     @validator("nodes")
#     def check_node_counts(cls, v):
#         if not (1 <= len(v) <= 200):
#             raise ValueError("nodes must be between 1 and 200")
#         return v

#     @validator("edges")
#     def check_edge_counts(cls, v):
#         if not (0 <= len(v) <= 500):
#             raise ValueError("edges must be between 0 and 500")
#         return v


# # ---------- Prompt text ----------
# SYSTEM_INSTRUCTIONS = """You are an expert at extracting knowledge graphs from text.
# Return ONLY strict JSON for a Cytoscape-style graph (used by Streamlit Link Analysis).
# Follow these rules exactly:
# - Output a single JSON object with keys: "nodes" and "edges".
# - Every node is: {"data": {"id": "...","label": "...","name": "...","description": "..."}}.
# - Every edge is: {"data": {"id": "...","source": "node_id","target": "node_id","label": "..."}}.
# - "id", "source", "target" must be short, unique, and contain only letters, numbers, underscore or hyphen.
# - Create 8–15 nodes and 10–20 edges unless the text clearly has fewer entities.
# - Use concise, human-readable names; keep descriptions under 30 words.
# - Prefer meaningful relationship labels (e.g., SUPPORTS, CAUSES, BELONGS_TO, EMPLOYS)."""

# USER_TEMPLATE = """Text to analyze:
# ---
# {doc}
# ---
# Primary topic (optional): {topic}

# Now extract the graph and return JSON ONLY. No explanations.
# """


# # ---------- Helpers ----------
# def _short_id(prefix: str) -> str:
#     base = re.sub(r"[^a-zA-Z0-9_-]", "", (prefix or "").strip().lower())[:8]
#     return f"{base}-{uuid.uuid4().hex[:6]}" if base else uuid.uuid4().hex[:8]

# def _dedupe_and_enforce_ids(payload: dict) -> dict:
#     """Ensure node/edge IDs are unique and valid, and lightly sanitize."""
#     if not isinstance(payload, dict):
#         raise TypeError("Graph payload must be a dict with 'nodes' and 'edges'.")

#     # nodes
#     seen_nodes = set()
#     for n in payload.get("nodes", []):
#         d = n.get("data", {})
#         raw = d.get("id") or _short_id(d.get("name", "node"))
#         nid = re.sub(r"[^a-zA-Z0-9_-]", "", raw)
#         if not nid or nid in seen_nodes:
#             nid = _short_id(d.get("name", "node"))
#         d["id"] = nid
#         seen_nodes.add(nid)

#     # edges
#     seen_edges = set()
#     for e in payload.get("edges", []):
#         d = e.get("data", {})
#         raw = d.get("id") or _short_id(f'{d.get("source","e")}_{d.get("target","e")}')
#         eid = re.sub(r"[^a-zA-Z0-9_-]", "", raw)
#         if not eid or eid in seen_edges:
#             eid = _short_id(f'{d.get("source","e")}')
#         d["id"] = eid
#         seen_edges.add(eid)

#     return payload


# # ---------- Public API ----------
# def generate_graph_json(
#     doc: str,
#     topic: str = "",
#     model: str = "gpt-4o-mini",
#     temperature: float = 0.1,
# ) -> dict:
#     """
#     Use an LLM to produce a strict Cytoscape-style graph payload (nodes/edges with 'data' keys).
#     Returns a dict you can dump to JSON for st-link-analysis / Cytoscape.
#     """
#     llm = ChatOpenAI(model=model, temperature=temperature)

#     parser = JsonOutputParser(pydantic_object=GraphPayload)

#     # IMPORTANT: Use Jinja2 to avoid treating {"data": ...} as template variables.
#     prompt = ChatPromptTemplate.from_messages(
#         [
#             ("system", SYSTEM_INSTRUCTIONS),
#             ("human", USER_TEMPLATE),
#         ],
#         template_format="jinja2",
#     )

#     chain = prompt | llm | parser

#     # NOTE: Depending on LangChain/version, this may return a Pydantic model or a plain dict.
#     result: Union[GraphPayload, dict, str] = chain.invoke({"doc": doc, "topic": topic or "N/A"})

#     if isinstance(result, GraphPayload):
#         payload = result.dict()
#     elif isinstance(result, dict):
#         payload = result
#     elif isinstance(result, str):
#         # Last resort: parse JSON string
#         payload = json.loads(result)
#     else:
#         # Shouldn't happen, but let's be explicit
#         raise TypeError(f"Unexpected chain result type: {type(result)}")

#     payload = _dedupe_and_enforce_ids(payload)
#     return payload


# def save_graph_json(payload: dict, path: str) -> str:
#     """Write JSON to disk (pretty). Returns the path."""
#     os.makedirs(os.path.dirname(path), exist_ok=True)
#     with open(path, "w", encoding="utf-8") as f:
#         json.dump(payload, f, ensure_ascii=False, indent=2)
#     return path

# knowledge_graph_formatter.py
# Generate strict Cytoscape / st-link-analysis JSON from arbitrary text via an LLM.

# knowledge_graph_formatter.py
# Generate strict Cytoscape / st-link-analysis JSON from arbitrary text via an LLM.

# knowledge_graph_formatter.py
# Generate strict Cytoscape / st-link-analysis JSON from arbitrary text via an LLM.

# knowledge_graph_formatter.py
# Generate Cytoscape / st-link-analysis JSON from arbitrary text via an LLM.
# STRICT mode guarantees nodes come from the answer text (no placeholders).

# knowledge_graph_formatter.py
# Strict, Cytoscape/st-link-analysis compatible graph extraction from text.

from typing import List, Optional, Union, Dict
from pydantic import BaseModel, Field, validator
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
import json
import re
import uuid
import os

# ---------- Pydantic schema ----------
class NodeData(BaseModel):
    id: str
    label: str
    name: str
    description: Optional[str] = None

class Node(BaseModel):
    data: NodeData

class EdgeData(BaseModel):
    id: str
    source: str
    target: str
    label: Optional[str] = None

class Edge(BaseModel):
    data: EdgeData

class GraphPayload(BaseModel):
    nodes: List[Node]
    edges: List[Edge]

    @validator("nodes")
    def check_node_counts(cls, v):
        if not (1 <= len(v) <= 2000):
            raise ValueError("nodes must be between 1 and 2000")
        return v

    @validator("edges")
    def check_edge_counts(cls, v):
        if not (0 <= len(v) <= 5000):
            raise ValueError("edges must be between 0 and 5000")
        return v

# ---------- Base prompts ----------
SYSTEM_INSTRUCTIONS = """You are an expert at extracting knowledge graphs from text.
Return ONLY strict JSON for a Cytoscape-style graph (used by Streamlit Link Analysis).
Rules:
- Output one JSON object with keys: "nodes" and "edges".
- Node: {"data":{"id","label","name","description"}}, Edge: {"data":{"id","source","target","label"}}.
- "id","source","target" are unique and contain only letters/numbers/_/-.
- Prefer 8–15 nodes and 10–20 edges when possible.
- Use concise names; descriptions under 30 words.
- Use ONLY entities present in the provided text. Do NOT invent placeholders.
"""

STRICT_SYSTEM_INSTRUCTIONS = SYSTEM_INSTRUCTIONS + """
You are also given AllowedEntities (a JSON array). You MUST choose node names ONLY from this list
(case-insensitive match is OK, but keep the original spelling). Do not rename or invent items.
If the list is long, pick the most relevant ~8–20.
AllowedEntities:
{{ allowed }}
"""

USER_TEMPLATE = """Text to analyze:
---
{doc}
---
Primary topic (optional): {topic}

Return JSON ONLY.
"""

# ---------- Helpers ----------
def _short_id(prefix: str) -> str:
    base = re.sub(r"[^a-zA-Z0-9_-]", "", (prefix or "").strip().lower())[:12]
    return f"{base}-{uuid.uuid4().hex[:6]}" if base else uuid.uuid4().hex[:8]

def _dedupe_and_enforce_ids(payload: dict) -> dict:
    seen_nodes, seen_edges = set(), set()
    for n in payload.get("nodes", []):
        d = n.get("data", {})
        raw = d.get("id") or _short_id(d.get("name", "node"))
        nid = re.sub(r"[^a-zA-Z0-9_-]", "", raw)
        if not nid or nid in seen_nodes:
            nid = _short_id(d.get("name", "node"))
        d["id"] = nid
        seen_nodes.add(nid)
    for e in payload.get("edges", []):
        d = e.get("data", {})
        raw = d.get("id") or _short_id(f'{d.get("source","e")}_{d.get("target","e")}')
        eid = re.sub(r"[^a-zA-Z0-9_-]", "", raw)
        if not eid or eid in seen_edges:
            eid = _short_id(f'{d.get("source","e")}')
        d["id"] = eid
        seen_edges.add(eid)
    return payload

def annotate_degree(payload: dict) -> dict:
    deg: Dict[str, int] = {}
    for e in payload.get("edges", []):
        d = e.get("data", {})
        s, t = d.get("source"), d.get("target")
        if s: deg[s] = deg.get(s, 0) + 1
        if t: deg[t] = deg.get(t, 0) + 1
    for n in payload.get("nodes", []):
        nid = n.get("data", {}).get("id")
        if nid:
            n["data"]["degree"] = deg.get(nid, 0)
    return payload

def _allowed_from_answer(doc: str) -> list:
    """Heuristic allowlist of entities (bullets, title-case phrases, Week X-Y)."""
    allowed = set()

    # bullet-like lines
    for raw in (doc or "").splitlines():
        s = raw.strip()
        if not s:
            continue
        if s[:1] in "-•*":
            s = s.lstrip("-•* \t").strip()
        if re.match(r"(?i)week\s*\d+\s*-\s*\d+", s):
            allowed.add(re.sub(r"\s+", " ", s))
            continue
        if (len(s.split()) <= 6 and not s.endswith(".")) or s.istitle():
            allowed.add(re.sub(r"\s+", " ", s))

    # capitalized multi-word terms inside sentences
    for m in re.findall(r"\b([A-Z][A-Za-z0-9+\-]*(?:\s+[A-Z][A-Za-z0-9+\-]*)*)\b", doc or ""):
        if 1 <= len(m.split()) <= 4:
            allowed.add(m.strip())

    allowed = {x for x in allowed if len(x) >= 2}
    return sorted(allowed)

def _enforce_in_text(payload: dict, doc: str) -> dict:
    """Keep only nodes whose name/label occurs in the text; drop dangling edges."""
    text = (doc or "").lower()
    def appears(s: str) -> bool:
        s = (s or "").strip().lower()
        return bool(s) and s in text

    nodes = []
    keep = set()
    for n in payload.get("nodes", []):
        d = n.get("data", {})
        if appears(d.get("name")) or appears(d.get("label")):
            nodes.append(n)
            keep.add(d.get("id"))

    edges = [e for e in payload.get("edges", [])
             if e.get("data", {}).get("source") in keep and e.get("data", {}).get("target") in keep]

    payload["nodes"], payload["edges"] = nodes, edges
    return payload

# ---------- Public API ----------
def generate_graph_json(
    doc: str,
    topic: str = "",
    model: str = "gpt-4o-mini",
    temperature: float = 0.0,   # strict extraction likes low creativity
    auto_label: bool = False,
    add_degree: bool = True,
    strict: bool = True,        # guarantees nodes come from the answer
) -> dict:
    llm = ChatOpenAI(model=model, temperature=temperature)
    parser = JsonOutputParser(pydantic_object=GraphPayload)

    if strict:
        allowed = _allowed_from_answer(doc)
        prompt = ChatPromptTemplate.from_messages(
            [("system", STRICT_SYSTEM_INSTRUCTIONS), ("human", USER_TEMPLATE)],
            template_format="jinja2",
        )
        chain = prompt | llm | parser
        result: Union[GraphPayload, dict, str] = chain.invoke(
            {"doc": doc, "topic": topic or "N/A", "allowed": json.dumps(allowed)}
        )
    else:
        prompt = ChatPromptTemplate.from_messages(
            [("system", SYSTEM_INSTRUCTIONS), ("human", USER_TEMPLATE)],
            template_format="jinja2",
        )
        chain = prompt | llm | parser
        result = chain.invoke({"doc": doc, "topic": topic or "N/A"})

    if isinstance(result, GraphPayload):
        payload = result.dict()
    elif isinstance(result, dict):
        payload = result
    elif isinstance(result, str):
        payload = json.loads(result)
    else:
        raise TypeError(f"Unexpected chain result type: {type(result)}")

    # Hygiene + guardrails
    payload = _dedupe_and_enforce_ids(payload)
    if strict:
        payload = _enforce_in_text(payload, doc)
    if add_degree:
        payload = annotate_degree(payload)
    return payload

def save_graph_json(payload: dict, path: str) -> str:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return path




