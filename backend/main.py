import os
import json
import uuid
import logging
from typing import AsyncGenerator
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse
from langchain_core.messages import HumanMessage

from backend.src.graph import build_graph
from backend.src.schema import get_dataset_profile
from backend.src.data import get_dataset

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("insight_copilot.api")

app = FastAPI(
    title="Insight Copilot API",
    description="Backend API powering the Insight Copilot LangGraph AI Business Intelligence Agent.",
    version="1.0.0",
)

# CORS setup
cors_origins_str = os.getenv("BACKEND_CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000,*")
cors_origins = [orig.strip() for orig in cors_origins_str.split(",") if orig.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Compile graph singleton on startup
graph = None


@app.on_event("startup")
async def on_startup():
    global graph
    logger.info("Initializing Insight Copilot backend...")
    # Pre-warm dataset cache
    df = get_dataset()
    logger.info(f"Dataset preloaded with {len(df):,} records.")
    # Initialize graph
    graph = build_graph()
    logger.info("Backend startup complete and ready for queries.")


class ChatRequest(BaseModel):
    query: str = Field(..., description="User question or prompt")
    thread_id: str | None = Field(None, description="Conversation session thread UUID")


@app.get("/health")
async def health():
    """Liveness & health probe for hosting platforms and frontend check."""
    return {"status": "ok", "service": "insight-copilot-backend", "version": "1.0.0"}


@app.get("/api/dataset/profile")
async def dataset_profile():
    """Returns dataset summary profile for UI sidebar and exploration."""
    try:
        profile = get_dataset_profile()
        return profile
    except Exception as e:
        logger.error(f"Failed to load dataset profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    """
    SSE streaming endpoint that streams agent reasoning steps and state updates in real-time.
    """
    global graph
    if graph is None:
        graph = build_graph()

    thread_id = request.thread_id or str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    async def event_generator() -> AsyncGenerator[dict, None]:
        initial_payload = {
            "event": "session",
            "data": json.dumps({"thread_id": thread_id, "query": request.query}),
        }
        yield initial_payload

        inputs = {
            "messages": [HumanMessage(content=request.query)],
            "user_query": request.query,
            "plan": "",
            "route": "direct_answer",
            "tool_plan": [],
            "tool_results": [],
            "iterations": 0,
            "reasoning_trace": [],
            "chart_spec": None,
            "final_answer": "",
            "error": None,
        }

        try:
            # Stream graph state snapshots step by step
            for output in graph.stream(inputs, config=config, stream_mode="updates"):
                for node_name, node_output in output.items():
                    yield {
                        "event": "node_update",
                        "data": json.dumps({
                            "node": node_name,
                            "reasoning_trace": node_output.get("reasoning_trace", []),
                            "plan": node_output.get("plan"),
                            "route": node_output.get("route"),
                            "tool_results": node_output.get("tool_results"),
                            "chart_spec": node_output.get("chart_spec"),
                            "final_answer": node_output.get("final_answer"),
                            "error": node_output.get("error"),
                        }),
                    }

            # Fetch final state snapshot from checkpointer
            final_state = graph.get_state(config).values
            yield {
                "event": "final_result",
                "data": json.dumps({
                    "thread_id": thread_id,
                    "final_answer": final_state.get("final_answer", ""),
                    "reasoning_trace": final_state.get("reasoning_trace", []),
                    "chart_spec": final_state.get("chart_spec"),
                    "tool_results": final_state.get("tool_results", []),
                }),
            }
        except Exception as e:
            logger.error(f"Error during graph streaming: {e}", exc_info=True)
            yield {
                "event": "error",
                "data": json.dumps({"error": str(e), "thread_id": thread_id}),
            }

    return EventSourceResponse(event_generator())


@app.get("/api/threads/{thread_id}")
async def get_thread_history(thread_id: str):
    """Retrieves conversation history and checkpoints for a given thread_id."""
    global graph
    if graph is None:
        graph = build_graph()

    config = {"configurable": {"thread_id": thread_id}}
    try:
        state = graph.get_state(config)
        if not state or not state.values:
            return {"thread_id": thread_id, "messages": [], "reasoning_trace": []}
        
        # Serialize messages
        messages_serialized = []
        for m in state.values.get("messages", []):
            messages_serialized.append({
                "type": getattr(m, "type", "message"),
                "content": getattr(m, "content", str(m)),
            })

        return {
            "thread_id": thread_id,
            "messages": messages_serialized,
            "reasoning_trace": state.values.get("reasoning_trace", []),
            "chart_spec": state.values.get("chart_spec"),
        }
    except Exception as e:
        logger.error(f"Failed to fetch thread {thread_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
