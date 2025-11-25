import os
import json
from typing import List, Dict, Any

from qdrant_client import QdrantClient
from qdrant_client.http import models
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

# ============================================================
# CONFIG
# ============================================================
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333))

DATA_PATH = os.getenv(
    "MANUAL_JSONL",
    "kb/compiled/manual_chunks_final.jsonl"
)

COLLECTION_NAME = "manual_book"

# Path model BGE-base-en-v1.5
EMBED_MODEL_PATH = "/Users/adrianalfajri/Projects/models/bge-base-en-v1.5"

RECREATE = True  # selalu recreate untuk hasil bersih

# ============================================================
# HELPERS
# ============================================================
def load_jsonl(path: str) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]

# ============================================================
# INGEST
# ============================================================
def ingest_manual():
    print(f"[INFO] Loading BGE-base model from: {EMBED_MODEL_PATH}")
    embedder = SentenceTransformer(EMBED_MODEL_PATH)

    client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

    print(f"[INFO] Loading manual JSONL: {DATA_PATH}")
    records = load_jsonl(DATA_PATH)
    if not records:
        raise RuntimeError(f"No records found in {DATA_PATH}")

    # --------------------------------------------------------
    # Build embedding texts (BEST PRACTICE)
    # --------------------------------------------------------
    embed_texts = []
    for r in records:
        content = r.get("content", "") or ""
        summary = r.get("summary", "") or ""
        problem = r.get("problem", "") or ""
        model = r.get("model", "") or ""
        section = r.get("section", "") or ""

        text = (
            content +
            f"\nSummary: {summary}" +
            f"\nProblem: {problem}" +
            f"\nModel: {model}" +
            f"\nSection: {section}"
        ).strip()

        embed_texts.append(text)

    # --------------------------------------------------------
    # ENCODING
    # --------------------------------------------------------
    print(f"[INFO] Generating embeddings for {len(embed_texts)} chunks...")
    embeddings = embedder.encode(embed_texts, batch_size=16, show_progress_bar=True)
    dim = embeddings.shape[1]

    # --------------------------------------------------------
    # RECREATE COLLECTION
    # --------------------------------------------------------
    if RECREATE:
        print(f"[INFO] Dropping old collection '{COLLECTION_NAME}' (if exists)...")
        try:
            client.delete_collection(COLLECTION_NAME)
        except:
            pass

        print(f"[INFO] Creating new collection '{COLLECTION_NAME}' (dim={dim})")
        client.recreate_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=models.VectorParams(
                size=dim,
                distance=models.Distance.COSINE
            )
        )

        # Create metadata indexes (filterable fields)
        for field in ("model", "section", "type", "source"):
            try:
                client.create_payload_index(
                    collection_name=COLLECTION_NAME,
                    field_name=field,
                    field_schema=models.PayloadSchemaType.KEYWORD
                )
            except:
                pass

    # --------------------------------------------------------
    # BUILD PAYLOADS
    # --------------------------------------------------------
    payloads = []
    ids = []

    for i, r in enumerate(records):
        ids.append(i + 1)
        payloads.append({
            "id": i + 1,
            "content": r.get("content", ""),
            "summary": r.get("summary", ""),
            "problem": r.get("problem", ""),
            "model": r.get("model", ""),
            "section": r.get("section", ""),
            "type": r.get("type", ""),
            "source": "manual_book"
        })

    # --------------------------------------------------------
    # UPSERT
    # --------------------------------------------------------
    print("[INFO] Uploading vectors & payloads to Qdrant...")
    client.upsert(
        collection_name=COLLECTION_NAME,
        points=models.Batch(
            ids=ids,
            vectors=embeddings.tolist(),
            payloads=payloads
        ),
        wait=True,
    )

    print(f"[SUCCESS] {len(payloads)} manual book chunks uploaded into '{COLLECTION_NAME}'.")

    # --------------------------------------------------------
    # DEBUG VERIFY
    # --------------------------------------------------------
    print("[INFO] Fetching sample payloads for verification...")
    hits = client.scroll(collection_name=COLLECTION_NAME, limit=3, with_payload=True)[0]

    for h in hits:
        p = h.payload or {}
        print("\n--- SAMPLE ---")
        print(f"ID:      {p.get('id')}")
        print(f"Model:   {p.get('model')}")
        print(f"Section: {p.get('section')}")
        print(f"Summary: {p.get('summary')[:150]}")
        print(f"Content: {(p.get('content') or '')[:150].replace(chr(10),' ')} ...")

# ============================================================
# EXEC
# ============================================================
if __name__ == "__main__":
    ingest_manual()
