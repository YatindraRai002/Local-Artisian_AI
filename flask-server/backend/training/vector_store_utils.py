#!/usr/bin/env python3
"""
Vector Store Loader Utility
Loads vector stores for retrieval in the RAG pipeline.
- Prefers Chroma persistence
- Falls back to FAISS if Chroma is unavailable
"""

import os
import logging
from langchain_community.vectorstores import Chroma, FAISS
from langchain_community.embeddings import SentenceTransformerEmbeddings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VECTOR_STORE_DIR = os.path.join(BASE_DIR, "training", "vector_stores")

# Embedding model (small + fast multilingual)
embedding_model = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")


def load_vector_store():
    """
    Load a vector store from disk.
    - Tries Chroma DB first
    - Falls back to FAISS if Chroma is unavailable
    Returns:
        vectorstore (Chroma | FAISS | None): Loaded vector store object
    """
    vectorstore = None

    # ---- Try Chroma ----
    try:
        if os.path.exists(VECTOR_STORE_DIR):
            logger.info("🔍 Attempting to load Chroma from %s", VECTOR_STORE_DIR)
            vectorstore = Chroma(
                persist_directory=VECTOR_STORE_DIR,
                embedding_function=embedding_model,
            )
            if vectorstore._collection.count() > 0:
                logger.info("✅ Loaded Chroma vector store with %s documents",
                            vectorstore._collection.count())
                return vectorstore
            else:
                logger.warning("⚠️ Chroma store is empty. Falling back to FAISS.")
    except Exception as e:
        logger.error("❌ Failed to load Chroma: %s", e)

    # ---- Try FAISS ----
    try:
        faiss_path = os.path.join(VECTOR_STORE_DIR, "faiss_index")
        if os.path.exists(faiss_path):
            logger.info("🔍 Attempting to load FAISS from %s", faiss_path)
            vectorstore = FAISS.load_local(
                faiss_path,
                embedding_model,
                allow_dangerous_deserialization=True
            )
            logger.info("✅ Loaded FAISS vector store")
            return vectorstore
        else:
            logger.error("❌ No FAISS index found in %s", faiss_path)
    except Exception as e:
        logger.error("❌ Failed to load FAISS: %s", e)

    # ---- Failure ----
    logger.error("❌ No vector stores found! Run `build_vector_store.py` first.")
    return None


if __name__ == "__main__":
    # Quick check
    vs = load_vector_store()
    if vs:
        logger.info("Vector store is ready for use ✅")
    else:
        logger.warning("Vector store not available ❌")
