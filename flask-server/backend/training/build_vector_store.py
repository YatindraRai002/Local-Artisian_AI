#!/usr/bin/env python3
"""
Build Vector Store for Kala-Kaart Chatbot
- Loads text/CSV/JSON files from backend/training/training_data/
- Builds Chroma (preferred) or FAISS (fallback) vector store
- Saves under backend/training/vector_stores/
"""

import os
import glob
import logging
import pandas as pd
from langchain_community.vectorstores import Chroma, FAISS
from langchain_community.embeddings import SentenceTransformerEmbeddings

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "training_data")
VECTOR_STORE_DIR = os.path.join(BASE_DIR, "vector_stores")

# Embeddings model (stable for langchain 0.2.x)
embedding_model = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")


def load_documents():
    """Load documents from training_data directory."""
    texts, metadatas = [], []

    # TXT files
    for filepath in glob.glob(os.path.join(DATA_DIR, "*.txt")):
        with open(filepath, "r", encoding="utf-8") as f:
            text = f.read().strip()
            if text:
                texts.append(text)
                metadatas.append({"source": os.path.basename(filepath)})

    # CSV files
    for filepath in glob.glob(os.path.join(DATA_DIR, "*.csv")):
        try:
            df = pd.read_csv(filepath)
            for i, row in df.iterrows():
                row_text = " ".join(str(v) for v in row.values if pd.notna(v))
                if row_text.strip():
                    texts.append(row_text)
                    metadatas.append({"source": os.path.basename(filepath), "row": i})
        except Exception as e:
            logger.warning(f"⚠️ Could not parse {filepath}: {e}")

    # JSON files
    for filepath in glob.glob(os.path.join(DATA_DIR, "*.json")):
        try:
            df = pd.read_json(filepath)
            for i, row in df.iterrows():
                row_text = " ".join(str(v) for v in row.values if pd.notna(v))
                if row_text.strip():
                    texts.append(row_text)
                    metadatas.append({"source": os.path.basename(filepath), "row": i})
        except Exception as e:
            logger.warning(f"⚠️ Could not parse {filepath}: {e}")

    logger.info("📄 Loaded %s documents from %s files", len(texts), len(metadatas))
    return texts, metadatas


def build_vector_store():
    """Build and persist vector store."""
    texts, metadatas = load_documents()

    if not texts:
        logger.error("❌ No documents found in %s. Cannot build vector store.", DATA_DIR)
        return None

    os.makedirs(VECTOR_STORE_DIR, exist_ok=True)

    try:
        logger.info("🔧 Building Chroma vector store...")
        vectorstore = Chroma.from_texts(
            texts=texts,
            embedding=embedding_model,
            metadatas=metadatas,
            persist_directory=VECTOR_STORE_DIR,
        )
        logger.info("✅ Chroma vector store built and persisted at %s", VECTOR_STORE_DIR)
        return vectorstore
    except Exception as e:
        logger.error("❌ Chroma failed: %s", e)
        logger.info("⚠️ Falling back to FAISS...")

    try:
        vectorstore = FAISS.from_texts(
            texts=texts,
            embedding=embedding_model,
            metadatas=metadatas,
        )
        faiss_path = os.path.join(VECTOR_STORE_DIR, "faiss_index")
        vectorstore.save_local(faiss_path)
        logger.info("✅ FAISS vector store saved at %s", faiss_path)
        return vectorstore
    except Exception as e:
        logger.error("❌ Failed to build FAISS: %s", e)
        return None


if __name__ == "__main__":
    vs = build_vector_store()
    if vs:
        logger.info("🎉 Vector store ready for use")
    else:
        logger.warning("⚠️ Vector store build failed")
