# backend/training/build_vector_store.py

import os
import json
from sentence_transformers import SentenceTransformer
from langchain.vectorstores import Chroma, FAISS
from langchain.embeddings import SentenceTransformerEmbeddings
import pickle

# Paths
TRAINING_DATA_DIR = "backend/training/training_data"
CHROMA_DIR = "backend/chroma_db/multilingual_chroma"
VECTOR_STORE_DIR = "backend/vector_stores"
VECTOR_STORE_FILE = os.path.join(VECTOR_STORE_DIR, "multilingual_faiss_index")

# Load the latest multilingual training data
json_files = [f for f in os.listdir(TRAINING_DATA_DIR) if f.endswith(".json")]
if not json_files:
    raise FileNotFoundError("No multilingual training data JSON found!")

latest_file = sorted(json_files)[-1]
training_data_path = os.path.join(TRAINING_DATA_DIR, latest_file)

with open(training_data_path, "r", encoding="utf-8") as f:
    data = json.load(f)["conversations"]

# Prepare texts for embeddings
texts = [conv["user_message"] + " " + conv["bot_response"] for conv in data]

# Initialize multilingual embedding model
embedding_model = SentenceTransformerEmbeddings(
    model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)

# -----------------------------
# Step 1: Build Chroma DB
# -----------------------------
os.makedirs(CHROMA_DIR, exist_ok=True)
chroma_db = Chroma.from_texts(texts, embedding_model, persist_directory=CHROMA_DIR)
chroma_db.persist()
print(f"✅ Chroma DB created at {CHROMA_DIR}")

# -----------------------------
# Step 2: Build FAISS backup
# -----------------------------
os.makedirs(VECTOR_STORE_DIR, exist_ok=True)
faiss_index = FAISS.from_texts(texts, embedding_model)
faiss_index.save_local(VECTOR_STORE_FILE)
print(f"✅ FAISS vector store saved at {VECTOR_STORE_FILE}")

print("\n🎉 Vector store (FAISS) and Chroma DB ready! You can now start the RAG model.")
