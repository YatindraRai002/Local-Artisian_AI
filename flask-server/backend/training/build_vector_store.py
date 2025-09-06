import os
import json
from langchain_community.vectorstores import Chroma, FAISS
from langchain_community.embeddings import SentenceTransformerEmbeddings

# ----------------------------------------------------------------
# Build absolute paths
# ----------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # folder of this script
TRAINING_DATA_DIR = os.path.join(BASE_DIR, "training_data")
VECTOR_STORE_DIR = os.path.join(BASE_DIR, "vector_stores")

# ----------------------------------------------------------------
# Ensure output dir exists
# ----------------------------------------------------------------
os.makedirs(VECTOR_STORE_DIR, exist_ok=True)

# ----------------------------------------------------------------
# Load JSON files
# ----------------------------------------------------------------
json_files = [f for f in os.listdir(TRAINING_DATA_DIR) if f.endswith(".json")]
documents = []

for file in json_files:
    file_path = os.path.join(TRAINING_DATA_DIR, file)
    with open(file_path, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except Exception as e:
            print(f"⚠️ Failed to read {file}: {e}")
            continue

        for item in data:
            if isinstance(item, dict):
                text = item.get("content") or item.get("text") or ""
                metadata = {k: v for k, v in item.items() if k not in ("content", "text")}
            elif isinstance(item, str):
                text = item
                metadata = {}
            else:
                text = ""
                metadata = {}

            if text.strip():
                documents.append((text.strip(), metadata))

print(f"✅ Loaded {len(documents)} documents from {len(json_files)} files.")

# ----------------------------------------------------------------
# Create embeddings
# ----------------------------------------------------------------
embedding_model = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")

# ----------------------------------------------------------------
# Separate texts & metadata
# ----------------------------------------------------------------
texts = [doc[0] for doc in documents]
metadatas = [doc[1] for doc in documents]

# ----------------------------------------------------------------
# Try Chroma first, fallback to FAISS
# ----------------------------------------------------------------
try:
    print("Trying to build Chroma DB...")
    vectorstore = Chroma.from_texts(
        texts=texts,
        embedding=embedding_model,
        metadatas=metadatas,
        persist_directory=VECTOR_STORE_DIR
    )
    vectorstore.persist()
    print("✅ Chroma DB created successfully!")
except Exception as e:
    print(f"⚠️ Chroma failed: {e}")
    print("Falling back to FAISS...")
    vectorstore = FAISS.from_texts(texts, embedding_model, metadatas=metadatas)
    faiss_path = os.path.join(VECTOR_STORE_DIR, "faiss_index")
    vectorstore.save_local(faiss_path)
    print("✅ FAISS index created successfully!") 
