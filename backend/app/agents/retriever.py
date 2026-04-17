# path: backend/app/agents/retriever.py
from crewai import Agent
import logging

from app.rag.vectorstore import similarity_search
from app.core.config import settings

logger = logging.getLogger(__name__)

def get_llm():
    """Get the Gemini LLM name."""
    if settings.GEMINI_API_KEY or settings.GOOGLE_API_KEY:
        # Using the exact model requested by the user
        return "gemini/gemini-flash-latest"
    
    return None

def create_retriever_agent() -> Agent:
    return Agent(
        role="Code Retriever",
        goal="Search for relevant code examples and solutions.",
        backstory="You are an expert at finding the right algorithms for any problem.",
        llm=get_llm(),
        verbose=True,
        allow_delegation=False,
    )

async def retrieve_context(query: str, k: int = 5) -> list:
    """Retrieve relevant documents for a query."""
    try:
        docs = similarity_search(query, k=k)
        return [
            {
                "title": doc.metadata.get("title", "Unknown"),
                "difficulty": doc.metadata.get("difficulty", "N/A"),
                "tags": doc.metadata.get("tags", ""),
                "content": doc.page_content[:800],
                "time_complexity": doc.metadata.get("time_complexity", "O(?)"),
                "space_complexity": doc.metadata.get("space_complexity", "O(?)"),
            }
            for doc in docs
        ]
    except Exception as e:
        logger.error(f"Retrieval error: {e}")
        return []
