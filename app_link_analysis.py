
# import json
# import streamlit as st

# from knowledge_graph_formatter import generate_graph_json, save_graph_json

# st.set_page_config(page_title="KG → Link Analysis", layout="wide")
# st.title("🔗 Knowledge Graph → Link Analysis")

# with st.sidebar:
#     st.markdown("### Generator Settings")
#     model = st.text_input("OpenAI model", "gpt-4o-mini")
#     temperature = st.slider("Temperature", 0.0, 1.0, 0.1, 0.05)

# st.markdown("Paste your source text, generate a graph JSON, then visualize it below.")

# col1, col2 = st.columns([2, 1], gap="large")
# with col1:
#     doc = st.text_area("Text to analyze:", height=260, placeholder="Paste a report, article, or notes…")
#     topic = st.text_input("Primary topic (optional)", "GenAI stack")
#     go = st.button("✨ Generate Graph JSON", type="primary")
# with col2:
#     st.info("Tip: Keep entities concise. The generator targets 8–15 nodes and 10–20 edges by default.")

# payload = None
# if go:
#     if not doc.strip():
#         st.error("Please paste some text.")
#     else:
#         with st.spinner("Generating…"):
#             payload = generate_graph_json(doc, topic=topic, model=model, temperature=temperature)
#         st.success("Graph JSON created.")
#         st.code(json.dumps(payload, indent=2), language="json")
#         st.download_button(
#             "Download graph_payload.json",
#             data=json.dumps(payload, indent=2),
#             file_name="graph_payload.json",
#             mime="application/json",
#         )

# st.markdown("---")
# st.header("👀 Visualize with st-link-analysis")

# # Allow user to paste/override JSON too
# user_json = st.text_area("Paste JSON (optional, overrides the generated payload):", height=220)
# if user_json.strip():
#     try:
#         payload = json.loads(user_json)
#     except Exception as e:
#         st.error(f"Invalid JSON: {e}")
#         payload = None

# # Render, if we have a payload
# if payload:
#     # Be tolerant about library signatures:
#     try:
#         from st_link_analysis import st_link_analysis  # pip: st-link-analysis
#         CONFIG = {
#             "layout": "cose",  # alternate: dagre, concentric, grid
#             "zoom": 1.0,
#             "edgeArrows": True,
#         }
#         try:
#             # common signature: (nodes, edges, config)
#             st_link_analysis(payload["nodes"], payload["edges"], config=CONFIG)
#         except TypeError:
#             # some versions accept a single payload
#             st_link_analysis(payload)
#     except Exception as e:
#         st.warning(
#             "Couldn't import or render with `st-link-analysis`. "
#             "Make sure `st-link-analysis` is in requirements and Streamlit re-ran. "
#             f"Import error: {e}"
#         )
# else:
#     st.caption("Generate a graph above, or paste JSON, to render the network here.")

# app_link_analysis.py
import json
import re
import unicodedata
import streamlit as st
from knowledge_graph_formatter import generate_graph_json, save_graph_json

st.set_page_config(page_title="KG → Link Analysis", layout="wide")
st.title("🔗 Knowledge Graph → Link Analysis")
st.caption("Generate a Cytoscape-style JSON graph from text and visualize it with st-link-analysis.")

# ----------------------- helpers -----------------------
def ensure_degree(payload: dict) -> dict:
    """If nodes don't have data.degree, compute it from edges."""
    try:
        nodes = payload.get("nodes", [])
        edges = payload.get("edges", [])
        if not nodes or not edges:
            return payload
        if any("degree" in n.get("data", {}) for n in nodes):
            return payload
        deg = {}
        for e in edges:
            d = e.get("data", {})
            s, t = d.get("source"), d.get("target")
            if s: deg[s] = deg.get(s, 0) + 1
            if t: deg[t] = deg.get(t, 0) + 1
        for n in nodes:
            nid = n.get("data", {}).get("id")
            if nid:
                n["data"]["degree"] = deg.get(nid, 0)
    except Exception:
        pass
    return payload

def _norm(s: str) -> str:
    s = (s or "").strip().lower()
    s = unicodedata.normalize("NFKD", s)
    s = re.sub(r"\s+", " ", s)
    return s

def _extract_sections_from_text(doc: str):
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

def annotate_sections_and_color(payload: dict, doc: str) -> dict:
    section_map = _extract_sections_from_text(doc)
    PALETTE = {
        "TOOLS": "#1f77b4",
        "SKILLS": "#ff7f0e",
        "PROJECTS": "#2ca02c",
        "INTERVIEW_TOPICS": "#d62728",
        "CLOUD": "#9467bd",
        "SOFT_SKILLS": "#8c564b",
        "ROADMAP": "#17becf",
        "OVERVIEW": "#7f7f7f",
    }
    for n in payload.get("nodes", []):
        d = n.get("data", {})
        name_norm = _norm(d.get("name"))
        label_norm = _norm(d.get("label"))
        sec = section_map.get(name_norm) or section_map.get(label_norm)
        if not sec and re.match(r"(?i)^week\s*\d+(\s*[-–]\s*\d+)?$", d.get("name", "")):
            sec = "ROADMAP"
        if sec:
            d["section"] = sec
            d["color"] = PALETTE.get(sec, "#333333")
    return payload

def render_graph(payload: dict, config: dict):
    try:
        from st_link_analysis import st_link_analysis
    except Exception as e:
        st.warning(
            "Couldn't import `st-link-analysis`. Ensure it's in requirements.txt and restart Streamlit.\n\n"
            f"Import error: {e}"
        )
        return
    payload = ensure_degree(payload)
    try:
        st_link_analysis(payload["nodes"], payload["edges"], config=config)
    except TypeError:
        st_link_analysis(payload)

# ----------------------- sidebar controls -----------------------
with st.sidebar:
    st.markdown("### Generator Settings")
    model = st.text_input("OpenAI model", "gpt-4o-mini")
    temperature = st.slider("Temperature", 0.0, 1.0, 0.1, 0.05)
    strict = st.checkbox("Strict (only use terms in text)", True)

    st.markdown("---")
    st.markdown("### Visualization Settings")
    layout = st.selectbox("Layout", ["concentric", "cose", "dagre", "grid"], index=1)
    show_arrows = st.checkbox("Show edge arrows", True)
    show_node_labels = st.checkbox("Show node labels (name)", True)
    show_edge_labels = st.checkbox("Show edge labels (label)", True)
    color_by_sections = st.checkbox("Color by sections parsed from text", True)
    group_by_label = st.checkbox("Group/color by node label (fallback)", False)

    size_by = st.selectbox("Size nodes by", ["degree", "none"], index=0)
    size_min = st.slider("Node size min", 10, 80, 22, 1)
    size_max = st.slider("Node size max", 20, 120, 60, 1)

# ----------------------- generation area -----------------------
st.markdown("Paste source text, generate a JSON graph, then visualize it below.")

col1, col2 = st.columns([2, 1], gap="large")
with col1:
    doc = st.text_area("Text to analyze:", height=260, placeholder="Paste a report, article, or notes…")
    topic = st.text_input("Primary topic (optional)", "GenAI stack")
    generate = st.button("✨ Generate Graph JSON", type="primary")
with col2:
    st.info("Tip: The generator targets ~8–15 nodes and 10–20 edges by default.")

if "payload" not in st.session_state:
    st.session_state.payload = None

if generate:
    if not doc.strip():
        st.error("Please paste some text.")
    else:
        with st.spinner("Generating…"):
            payload = generate_graph_json(
                doc,
                topic=topic,
                model=model,
                temperature=0.0 if strict else temperature,
                auto_label=False,
                add_degree=True,
                strict=strict,
            )
            if color_by_sections:
                payload = annotate_sections_and_color(payload, doc)
        st.session_state.payload = payload
        st.success("Graph JSON created.")
        st.code(json.dumps(payload, indent=2), language="json")
        st.download_button(
            "Download graph_payload.json",
            data=json.dumps(payload, indent=2),
            file_name="graph_payload.json",
            mime="application/json",
        )

st.markdown("---")
st.header("👀 Visualize with st-link-analysis")

user_json = st.text_area("Paste JSON (optional, overrides the generated payload):", height=200)
payload = None

if user_json.strip():
    try:
        payload = json.loads(user_json)
    except Exception as e:
        st.error(f"Invalid JSON: {e}")
        payload = None
elif st.session_state.payload:
    payload = st.session_state.payload

if payload:
    cfg = {
        "layout": layout,
        "edgeArrows": show_arrows,
        "nodeLabel": "name" if show_node_labels else None,
        "edgeLabel": "label" if show_edge_labels else None,
        "groupBy": "section" if color_by_sections else ("label" if group_by_label else None),
        "nodeColorProp": "color" if color_by_sections else None,
    }
    if size_by == "degree":
        cfg["nodeSizeProp"] = "degree"
        cfg["nodeSizeRange"] = [size_min, size_max]
    render_graph(payload, cfg)
else:
    st.caption("Generate a graph above, or paste JSON, to render the network here.")

