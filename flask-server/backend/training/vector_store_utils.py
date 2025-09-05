import os
import logging
from langchain_community.vectorstores import Chroma, FAISS
from langchain_community.embeddings import SentenceTransformerEmbeddings





logger = logging.getLogger(__name__)

# Path to vector stores
VECTOR_STORE_DIR = "backend/training/vector_stores"

# Embedding model
embedding_model = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")


def load_vector_store():
    """
    Load vector store from disk.
    Prefers Chroma DB. Falls back to FAISS if Chroma fails.
    """
    vectorstore = None

    # Try Chroma first
    try:
        if os.path.exists(VECTOR_STORE_DIR):
            logger.info("🔍 Trying to load Chroma from %s", VECTOR_STORE_DIR)
            vectorstore = Chroma(
                persist_directory=VECTOR_STORE_DIR,
                embedding_function=embedding_model,
            )
            # Quick sanity check
            if vectorstore._collection.count() > 0:
                logger.info("✅ Loaded Chroma vector store with %s documents",
                            vectorstore._collection.count())
                return vectorstore
            else:
                logger.warning("⚠️ Chroma is empty, will try FAISS fallback.")
    except Exception as e:
        logger.error("❌ Failed to load Chroma: %s", e)

    # Fallback: FAISS
    try:
        faiss_path = os.path.join(VECTOR_STORE_DIR, "faiss_index")
        if os.path.exists(faiss_path):
            logger.info("🔍 Trying to load FAISS from %s", faiss_path)
            vectorstore = FAISS.load_local(faiss_path, embedding_model, allow_dangerous_deserialization=True)
            logger.info("✅ Loaded FAISS vector store")
            return vectorstore
        else:
            logger.error("❌ No FAISS index found in %s", faiss_path)
    except Exception as e:
        logger.error("❌ Failed to load FAISS: %s", e)

    logger.error("❌ No vector stores found! Please run build_vector_store.py")
    return None
