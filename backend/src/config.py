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

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
DATABASE_URL = os.getenv("DATABASE_URL", "")
DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# Default dataset: prioritize olist_master.csv if present, else fallback to global_superstore.csv
olist_path = root_dir / "data" / "olist_master.csv"
superstore_path = root_dir / "data" / "global_superstore.csv"

if os.getenv("DATASET_PATH"):
    DATASET_PATH = os.getenv("DATASET_PATH")
elif olist_path.exists():
    DATASET_PATH = str(olist_path)
else:
    DATASET_PATH = str(superstore_path)


def get_llm(model_name: str = DEFAULT_MODEL, temperature: float = 0.0) -> Any:
    """
    Factory function returning the configured LLM instance.
    Defaults to Gemini 2.x Flash via langchain-google-genai.
    """
    if not GEMINI_API_KEY:
        logger.warning("GEMINI_API_KEY is not set. LLM calls will fail unless a mock/key is provided.")
    
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=GEMINI_API_KEY,
            temperature=temperature,
        )
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
            conn = psycopg.connect(DATABASE_URL, autocommit=True)
            checkpointer = PostgresSaver(conn)
            checkpointer.setup()
            logger.info("PostgresSaver checkpointer setup complete.")
            return checkpointer
        except Exception as e:
            logger.error(f"PostgreSQL connection failed ({e}). Falling back to in-memory MemorySaver.")
    
    from langgraph.checkpoint.memory import MemorySaver
    logger.info("Using in-memory MemorySaver for conversation checkpointer.")
    return MemorySaver()
