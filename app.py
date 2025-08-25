# app.py
import asyncio
import traceback
import httpx
import json
import re
import unicodedata
from itertools import cycle

import streamlit as st
from langchain_core.messages import HumanMessage, AIMessage

# Build the KG from the latest answer
from knowledge_graph_formatter import generate_graph_json

# Your LangGraph compiled graph (adjust import if path differs)
from gradpath_graph import compiled_graph  # noqa

st.set_page_config(page_title="🎓 GradPath AI: Your AI Career Copilot", layout="wide")
st.title("🎓 GradPath AI: Your AI Career Copilot")

# -----------------------------------------------------------------------------
# Session state
# -----------------------------------------------------------------------------
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "last_answer" not in st.session_state:
    st.session_state.last_answer = ""

# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------
def _extract_text_from_result(result) -> str:
    """Pull final assistant text from a compiled_graph result dict."""
    msgs = result.get("messages", []) if isinstance(result, dict) else []
    if not msgs:
        return ""
    last = msgs[-1]
    return getattr(last, "content", str(last)) or ""

def _render_history():
    for m in st.session_state.chat_history:
        role = "user" if isinstance(m, HumanMessage) else "assistant"
        with st.chat_message(role):
            st.markdown(m.content)

def _norm(s: str) -> str:
    s = (s or "").strip().lower()
    s = unicodedata.normalize("NFKD", s)
    s = re.sub(r"\s+", " ", s)
    return s

def _extract_sections_from_answer(doc: str):
    """Map bullet items under headings to section tags (TOOLS, SKILLS, …)."""
    SECTION_ALIASES = {
        "tools": "TOOLS",
        "skills": "SKILLS",
        "soft skills": "SOFT_SKILLS",
        "projects": "PROJECTS",
        "interview topics": "INTERVIEW_TOPICS",
        "cloud & devops": "CLOUD",
        "cloud and devops": "CLOUD",
        "roadmap": "ROADMAP",
        "overview": "OVERVIEW",
    }
    blocks = re.split(r"(?m)^#{2,3}\s+", doc or "")
    section_map = {}
    for block in blocks:
        lines = block.strip().splitlines()
        if not lines:
            continue
        header = _norm(lines[0].rstrip(":"))
        tag = None
        for k, v in SECTION_ALIASES.items():
            if _norm(k) in header:
                tag = v
                break
        if not tag:
            continue
        body = "\n".join(lines[1:])
        items = re.findall(r"(?m)^\s*[-*]\s+(.+?)\s*$", body)
        items += re.findall(r"(?mi)^(week\s*[\d\-–]+)\s*:", body)
        cleaned = []
        for x in items:
            x = re.sub(r"^\*\*?|\*\*$", "", x).strip()
            x = re.sub(r"[•\-–]\s*", "", x).strip()
            x = re.sub(r"\s*\(.*?\)\s*$", "", x).strip()
            if x:
                cleaned.append(x)
        for it in cleaned:
            section_map[_norm(it)] = tag
    return section_map

def _annotate_sections(payload: dict, doc: str) -> dict:
    """Add data.section to nodes so we can color/group by section."""
    section_map = _extract_sections_from_answer(doc)
    for n in payload.get("nodes", []):
        d = n.get("data", {})
        name_norm = _norm(d.get("name"))
        label_norm = _norm(d.get("label"))
        sec = section_map.get(name_norm) or section_map.get(label_norm)
        if not sec and re.match(r"(?i)^week\s*\d+(\s*[-–]\s*\d+)?$", d.get("name", "")):
            sec = "ROADMAP"
        if not sec and name_norm in {
            "tools","skills","projects","interview topics","soft skills",
            "cloud & devops","cloud and devops","roadmap","overview"
        }:
            sec = {
                "tools":"TOOLS","skills":"SKILLS","projects":"PROJECTS","interview topics":"INTERVIEW_TOPICS",
                "soft skills":"SOFT_SKILLS","cloud & devops":"CLOUD","cloud and devops":"CLOUD",
                "roadmap":"ROADMAP","overview":"OVERVIEW",
            }[name_norm]
        if sec:
            d["section"] = sec
    return payload

def _colorize_by_section(payload: dict) -> dict:
    """Attach a color hex per node based on its data.section; duplicate name into label."""
    PALETTE = {
        "TOOLS": "#1f77b4",           # blue
        "SKILLS": "#ff7f0e",          # orange
        "PROJECTS": "#2ca02c",        # green
        "INTERVIEW_TOPICS": "#d62728",# red
        "CLOUD": "#9467bd",           # purple
        "SOFT_SKILLS": "#8c564b",     # brown
        "ROADMAP": "#17becf",         # teal
        "OVERVIEW": "#7f7f7f",        # gray
    }
    for n in payload.get("nodes", []):
        d = n.get("data", {})
        sec = d.get("section")
        if sec:
            d["color"] = PALETTE.get(sec, "#333333")
            if "group" not in d:
                d["group"] = sec
        d["label"] = d.get("name") or d.get("label") or ""
    return payload

def _bake_inline_styles(payload: dict) -> dict:
    """Hard-style every node/edge so labels & colors render even on old viewers."""
    for n in payload.get("nodes", []):
        d = n.get("data", {})
        stl = n.setdefault("style", {})
        if d.get("color"):
            stl["background-color"] = d["color"]
        stl["label"] = d.get("name") or d.get("label") or ""
        stl["color"] = "#222"
        stl["font-size"] = "12px"
        stl["text-wrap"] = "wrap"
        stl["text-max-width"] = 120
        stl["text-valign"] = "center"
        stl["text-halign"] = "center"
        stl["background-opacity"] = 1
        stl["border-width"] = 1
        stl["border-color"] = "#222"
    for e in payload.get("edges", []):
        ed = e.get("data", {})
        stl = e.setdefault("style", {})
        stl["label"] = ed.get("label") or ""
        stl["font-size"] = "10px"
        stl["text-rotation"] = "autorotate"
        stl["curve-style"] = "bezier"
        stl["target-arrow-shape"] = "triangle"
        stl["arrow-scale"] = 1.15
        stl["line-color"] = "#9e9e9e"
        stl["target-arrow-color"] = "#9e9e9e"
    return payload

# -----------------------------------------------------------------------------
# Chat UI
# -----------------------------------------------------------------------------
_render_history()
user_input = st.chat_input("Ask me anything about your AI/ML career path...")

# -----------------------------------------------------------------------------
# Streaming reply with resilient fallback
# -----------------------------------------------------------------------------
async def stream_reply(user_text: str, assistant_box):
    history = st.session_state.chat_history + [HumanMessage(content=user_text)]
    input_state = {"messages": history}
    accumulated = ""

    try:
        # token streaming via LangGraph
        async for event in compiled_graph.astream_events(input=input_state, version="v2"):
            e = event.get("event")
            data = event.get("data", {})
            if e == "on_chat_model_stream":
                chunk = data.get("chunk")
                delta = getattr(chunk, "content", "") if chunk else ""
                if delta:
                    accumulated += delta
                    assistant_box.markdown(accumulated)

    except (httpx.RemoteProtocolError, httpx.ReadError, httpx.ConnectError):
        # stream dropped -> non-stream one-shot
        result = await compiled_graph.ainvoke(input_state)
        full_text = _extract_text_from_result(result)
        if full_text:
            accumulated = full_text
            assistant_box.markdown(accumulated)
        else:
            assistant_box.markdown("❌ Streaming failed and fallback returned no text.")
            st.code(traceback.format_exc(), language="python")
            return
    except Exception:
        assistant_box.markdown("❌ Something went wrong while streaming. See trace below.")
        st.code(traceback.format_exc(), language="python")
        return

    # finalize/history
    assistant_box.markdown(accumulated)
    st.session_state.chat_history.append(HumanMessage(content=user_text))
    st.session_state.chat_history.append(AIMessage(content=accumulated))
    st.session_state.last_answer = accumulated

if user_input:
    with st.chat_message("user"):
        st.markdown(user_input)
    assistant_box = st.chat_message("assistant").empty()
    asyncio.run(stream_reply(user_input, assistant_box))

# -----------------------------------------------------------------------------
# KG: Build strictly from the latest answer, never empty, and visualize
# -----------------------------------------------------------------------------
st.markdown("---")
with st.expander("🔗 Build Knowledge Graph from this answer", expanded=False):
    last = st.session_state.get("last_answer", "")
    st.caption(f"KG input length: {len(last)} chars")
    st.text_area("KG input preview (read-only)", last[:1500], height=200, disabled=True)

    topic = st.text_input(
        "Primary topic (optional)",
        "GradPath career map",
        key=f"kg_topic_{len(st.session_state.chat_history)}",
    )

    if st.button("✨ Generate KG", key=f"kg_btn_{len(st.session_state.chat_history)}"):
        if not last.strip():
            st.error("No assistant answer captured yet. Ask a question first, then build the graph.")
        else:
            # -------------------- Build KG with fallbacks --------------------
            with st.spinner("Generating graph…"):
                # 1) strict (best quality)
                payload = generate_graph_json(
                    last,
                    topic=topic,
                    model="gpt-4o-mini",
                    temperature=0.0,
                    auto_label=False,
                    add_degree=True,
                    strict=True,
                )
                reason = "strict"

                # 2) lenient fallback
                if not payload or not payload.get("nodes"):
                    payload = generate_graph_json(
                        last,
                        topic=topic,
                        model="gpt-4o-mini",
                        temperature=0.2,
                        auto_label=True,
                        add_degree=True,
                        strict=False,
                    )
                    reason = "lenient"

                # 3) heuristic fallback (never empty)
                if not payload or not payload.get("nodes"):
                    def quick_heuristic_graph(doc: str, topic_text: str) -> dict:
                        heads = re.findall(r"(?m)^#{2,3}\s+(.+?)\s*$", doc)
                        bullets = re.findall(r"(?m)^\s*[-*]\s+(.+?)\s*$", doc)
                        seen, items = set(), []
                        for s in (heads + bullets):
                            s = re.sub(r"^\s+|\s+$", "", s)
                            s = re.sub(r"\s+", " ", s).strip(" -•:").strip()
                            if len(s) >= 3 and s.lower() not in seen:
                                seen.add(s.lower()); items.append(s)
                            if len(items) >= 12:
                                break
                        nodes, edges = [], []
                        hub_id = "hub"
                        nodes.append({"data": {
                            "id": hub_id, "name": topic_text or "GradPath", "label": topic_text or "GradPath",
                            "description": "Auto-created hub (heuristic fallback).",
                            "section": "OVERVIEW", "color": "#7f7f7f", "degree": max(1, len(items))
                        }})
                        for i, text in enumerate(items, start=1):
                            nid = f"node_{i}"
                            nodes.append({"data": {
                                "id": nid, "name": text, "label": text, "description": text,
                                "section": "ITEM", "color": "#2A629A", "degree": 1
                            }})
                            edges.append({"data": {"id": f"edge_{i}", "source": hub_id, "target": nid, "label": "RELATED_TO"}})
                        return {"nodes": nodes, "edges": edges}

                    payload = quick_heuristic_graph(last, topic or "Answer")
                    reason = "heuristic"

            # Post-process
            payload = _annotate_sections(payload, last)
            payload = _colorize_by_section(payload)

            st.caption(f"KG built via: **{reason}** mode")
            st.subheader("JSON")
            st.code(json.dumps(payload, indent=2), language="json")

            # -------------------- Visualize (new API first, fallback to old) --------------------
            try:
                # New API (NodeStyle / EdgeStyle / LAYOUTS)
                from st_link_analysis import st_link_analysis, NodeStyle, EdgeStyle, LAYOUTS

                elements = {"nodes": payload["nodes"], "edges": payload["edges"]}

                # Group strictly by SECTION (fallback OTHER)
                groups = sorted({
                    n["data"].get("section") or "OTHER"
                    for n in elements["nodes"]
                })

                palette = cycle([
                    "#FF7F3E", "#2A629A", "#FF6B6B", "#4ECDC4",
                    "#45B7D1", "#96CEB4", "#FFEAA7", "#8D6E63",
                    "#9C27B0", "#17becf", "#2ca02c", "#ff7f0e",
                ])

                node_styles = []
                for g in groups:
                    color = next(palette)
                    # KEY: NodeStyle matches on data['label'] → set it to the GROUP
                    for n in elements["nodes"]:
                        if (n["data"].get("section") or "OTHER") == g:
                            n["data"]["label"] = g
                    # Title shown on node = 'name'; subtitle = 'description'
                    node_styles.append(NodeStyle(g, color, "name", "description"))

                edge_labels = sorted({e["data"].get("label", "RELATED") for e in elements["edges"]})
                edge_styles = [EdgeStyle(lbl, caption="label", directed=True) for lbl in edge_labels]

                # Bake inline labels/colors too so text shows regardless of theme
                payload = _bake_inline_styles(payload)
                elements = {"nodes": payload["nodes"], "edges": payload["edges"]}

                layout_names = list(LAYOUTS.keys())
                chosen = st.selectbox(
                    "Layout",
                    layout_names,
                    index=layout_names.index("cose") if "cose" in layout_names else 0,
                )

                st_link_analysis(
                    elements,
                    layout=chosen,
                    node_styles=node_styles,
                    edge_styles=edge_styles,
                    key=f"NODE_ACTIONS_{len(elements['nodes'])}_{len(elements['edges'])}",
                    node_actions=[],   # add ['remove','expand'] if you wire callbacks
                    on_change=lambda: None,
                )

            except Exception:
                # Old API fallback with inline styles
                try:
                    from st_link_analysis import st_link_analysis
                except Exception as e:
                    st.warning(
                        "Could not render with `st-link-analysis`. Ensure it's installed and restart Streamlit. "
                        f"Import error: {e}"
                    )
                else:
                    payload = _bake_inline_styles(payload)
                    CONFIG = {
                        "layout": "cose",
                        "edgeArrows": True,
                        "nodeSizeProp": "degree",
                        "nodeSizeRange": [22, 64],
                    }
                    try:
                        st_link_analysis(payload["nodes"], payload["edges"], config=CONFIG)
                    except TypeError:
                        st_link_analysis(payload)




                

