#!/usr/bin/env python3
"""
Vector Store Loader Utility
- Loads Chroma (preferred) or FAISS (fallback) for RAG pipeline
"""

import os
import logging
from langchain_community.vectorstores import Chroma, FAISS
from langchain.embeddings import HuggingFaceEmbeddings
  # Updated import

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VECTOR_STORE_DIR = os.path.join(BASE_DIR, "vector_stores")

embedding_model = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)


def load_vector_store():
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
        logger.warning("⚠️ Chroma failed: %s", e)

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
            logger.warning("⚠️ No FAISS index found in %s", faiss_path)
    except Exception as e:
        logger.error("❌ Failed to load FAISS: %s", e)

    logger.error("❌ No vector store found! Run `build_vector_store.py` first.")
    return None


if __name__ == "__main__":
    vs = load_vector_store()
    if vs:
        logger.info("Vector store is ready ✅")
    else:
        logger.warning("Vector store not available ❌")
