from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage
from gradpath_graph import compiled_graph
import asyncio

app = FastAPI()

@app.get("/")
def health():
    return {"message": "🚀 GradPath AI streaming backend running"}

@app.post("/chat")
async def chat(request: Request):
    body = await request.json()
    user_input = body.get("message", "")

    input_state = {"messages": [HumanMessage(content=user_input)]}

    async def token_stream():
        try:
            # v2 events give you model token deltas + tool events
            async for event in compiled_graph.astream_events(input=input_state, version="v2"):
                ev = event.get("event", "")
                data = event.get("data", {})

                # 1) Stream model token deltas
                if ev == "on_chat_model_stream":
                    chunk = data.get("chunk")
                    text = getattr(chunk, "content", "")
                    if text:
                        yield text
                        await asyncio.sleep(0.002)

                # 2) (Optional) stream tool results as soon as a tool returns
                if ev == "on_tool_end":
                    out = data.get("output")
                    if out:
                        # prettify a little for links
                        yield f"\n\n---\n**Tool result**:\n{out}\n"
        except Exception as e:
            yield f"\n[ERROR] {str(e)}"

    return StreamingResponse(token_stream(), media_type="text/plain")
