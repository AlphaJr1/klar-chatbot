
import os
import sys
import json
from pathlib import Path
from tqdm import tqdm
from qdrant_client import QdrantClient
from qdrant_client.http import models
from sentence_transformers import SentenceTransformer

BASE = os.path.dirname(os.path.dirname(__file__))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

DATA_PATH = Path(BASE) / "kb" / "compiled" / "chat_pairs.jsonl"
COLLECTION_NAME = "chat_history_pairs"

QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333))
client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

print("[INFO] Loading embedding model (Indo E5 v4 lokal)...")

LOCAL_MODEL_DIR = str(Path(BASE).parent / "models" / "all-indo-e5-small-v4")

if not os.path.isdir(LOCAL_MODEL_DIR):
    print(f"[ERROR] Folder model tidak ditemukan: {LOCAL_MODEL_DIR}")
    print("Silakan pastikan kamu mengunduh model ke folder Projects/models/")
    sys.exit(1)

embedder = SentenceTransformer(LOCAL_MODEL_DIR)

def ensure_collection(dim: int):
    print(f"[INFO] Dropping and recreating collection: {COLLECTION_NAME}")

    client.recreate_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=models.VectorParams(size=dim, distance=models.Distance.COSINE),
    )

# Main ingestion
def ingest_chat_pairs():
    if not DATA_PATH.exists():
        print(f"[ERROR] File {DATA_PATH} tidak ditemukan.")
        return

    print(f"[INFO] Membaca data dari {DATA_PATH}")
    records = []
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                try:
                    records.append(json.loads(line))
                except Exception:
                    continue

    print(f"[INFO] Total chat pairs: {len(records)}")

    texts = [
        f"Customer: {r.get('customer','')} Admin: {r.get('admin','')}"
        for r in records
    ]
    embeddings = embedder.encode(
        texts,
        batch_size=16,
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=True
    )

    ensure_collection(dim=embeddings.shape[1])

    print(f"[INFO] Meng-upload data ke Qdrant...")
    payloads = []
    vectors = []
    ids = []

    for i, (r, emb) in enumerate(zip(records, embeddings)):
        ids.append(i + 1)
        vectors.append(emb.tolist())
        payloads.append({
            "topic": r.get("topic"),
            "customer": r.get("customer"),
            "admin": r.get("admin"),
            "summary": r.get("summary"),
            "source": r.get("source", "chat_history"),
        })

    client.upsert(
        collection_name=COLLECTION_NAME,
        points=models.Batch(
            ids=ids,
            vectors=vectors,
            payloads=payloads
        )
    )

    print(f"[✅] {len(records)} records berhasil di-index ke Qdrant collection '{COLLECTION_NAME}'.")

if __name__ == "__main__":
    ingest_chat_pairs()
