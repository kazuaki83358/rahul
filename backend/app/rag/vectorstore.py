# path: backend/app/rag/vectorstore.py
import logging

logger = logging.getLogger(__name__)

# Fallback for simple keyword search if Chroma is not available
MOCK_DOCS = []

def similarity_search(query: str, k: int = 5):
    """
    Search for relevant documents. 
    Robust fallback to simple keyword matching if vector store is missing.
    """
    try:
        from langchain_community.vectorstores import Chroma
        from app.rag.embeddings import get_embeddings
        from app.core.config import settings
        import os

        if not os.path.exists(settings.CHROMA_PERSIST_DIR):
             logger.warning("Vector database not found, falling back to simple search")
             return fallback_search(query, k)

        db = Chroma(
            persist_directory=settings.CHROMA_PERSIST_DIR,
            embedding_function=get_embeddings(),
        )
        return db.similarity_search(query, k=k)
    except Exception as e:
        logger.error(f"Vector store search failed: {e}. Using fallback.")
        return fallback_search(query, k)

def fallback_search(query: str, k: int = 5):
    """Simple keyword matching fallback."""
    from app.models.base import SessionLocal
    from app.models.user import Dataset
    
    db = SessionLocal()
    try:
        # Search for titles containing query words
        results = db.query(Dataset).filter(Dataset.title.contains(query.split()[0])).limit(k).all()
        # Convert to a format that looks like LangChain documents
        class Doc:
            def __init__(self, data):
                self.page_content = data.problem_text
                self.metadata = {
                    "title": data.title,
                    "difficulty": data.difficulty,
                    "tags": data.tags,
                    "time_complexity": data.time_complexity,
                    "space_complexity": data.space_complexity
                }
        return [Doc(r) for r in results]
    except:
        return []
    finally:
        db.close()

def add_documents(documents: list):
    """Add documents to the vector store if available."""
    try:
        from langchain_community.vectorstores import Chroma
        from app.rag.embeddings import get_embeddings
        from app.core.config import settings
        from langchain.docstore.document import Document

        docs = [
            Document(page_content=d["problem_text"], metadata=d) for d in documents
        ]
        Chroma.from_documents(
            docs, get_embeddings(), persist_directory=settings.CHROMA_PERSIST_DIR
        )
        logger.info(f"Added {len(docs)} docs to Chroma")
    except Exception as e:
        logger.error(f"Failed to add documents to vector store: {e}")
