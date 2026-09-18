import os
import logging
from pathlib import Path
from typing import Any
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("insight_copilot.config")

# Look for .env in current directory, backend dir, or project root
root_dir = Path(__file__).resolve().parent.parent.parent
env_paths = [
    Path.cwd() / ".env",
    Path(__file__).resolve().parent.parent / ".env",
    root_dir / ".env",
]
for p in env_paths:
    if p.exists():
        load_dotenv(p)
        logger.info(f"Loaded environment from {p}")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or ""
DATABASE_URL = os.getenv("DATABASE_URL", "")
DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")

# Default dataset: resolve olist_master.csv across root or backend subdirectory deployments
possible_paths = [
    Path(os.getenv("DATASET_PATH")) if os.getenv("DATASET_PATH") else None,
    root_dir / "data" / "olist_master.csv",
    Path(__file__).resolve().parent.parent / "data" / "olist_master.csv",
    Path.cwd() / "data" / "olist_master.csv",
    root_dir / "data" / "global_superstore.csv",
]
DATASET_PATH = str(root_dir / "data" / "olist_master.csv")
for p in possible_paths:
    if p and p.exists():
        DATASET_PATH = str(p)
        logger.info(f"Using dataset at: {DATASET_PATH}")
        break


def get_llm(model_name: str = DEFAULT_MODEL, temperature: float | None = None) -> Any:
    """
    Factory function returning the configured LLM instance.
    Defaults to Gemini 3.1 Flash Lite via langchain-google-genai.
    """
    if not GEMINI_API_KEY:
        logger.warning("GEMINI_API_KEY / GOOGLE_API_KEY is not set. LLM calls will fail unless a mock/key is provided.")
    
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        kwargs = {"model": model_name, "google_api_key": GEMINI_API_KEY}
        if temperature is not None:
            kwargs["temperature"] = temperature
        return ChatGoogleGenerativeAI(**kwargs)
    except Exception as e:
        logger.error(f"Failed to initialize ChatGoogleGenerativeAI: {e}")
        raise


def get_checkpointer() -> Any:
    """
    Returns PostgresSaver if DATABASE_URL is configured, else falls back to MemorySaver.
    """
    if DATABASE_URL:
        try:
            import psycopg
            from langgraph.checkpoint.postgres import PostgresSaver
            logger.info("Connecting to PostgreSQL (Neon.tech) for persistent checkpoints...")
            db_url = DATABASE_URL
            if "sslmode=" not in db_url:
                db_url += ("&" if "?" in db_url else "?") + "sslmode=require"
            conn = psycopg.connect(db_url, autocommit=True)
            checkpointer = PostgresSaver(conn)
            checkpointer.setup()
            logger.info("PostgresSaver checkpointer setup complete.")
            return checkpointer
        except Exception as e:
            logger.error(f"PostgreSQL connection failed ({e}). Falling back to in-memory MemorySaver.")
    
    from langgraph.checkpoint.memory import MemorySaver
    logger.info("Using in-memory MemorySaver for conversation checkpointer.")
    return MemorySaver()

