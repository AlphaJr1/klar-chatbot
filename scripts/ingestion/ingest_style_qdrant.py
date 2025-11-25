import os, sys, json
from pathlib import Path
from tqdm import tqdm
from qdrant_client import QdrantClient
from qdrant_client.http import models
from sentence_transformers import SentenceTransformer

# ============================================================
# PATH SETUP
# ============================================================
# Lokasi project root: Projects/klar-rag/
BASE = Path(__file__).resolve().parents[1]

DATA_PATH = BASE / "kb" / "compiled" / "style_index.jsonl"
COLLECTION_NAME = "style_guide"

# Lokasi model embed lokal (Projects/models/all-indo-e5-small-v4)
EMBED_MODEL_PATH = BASE.parent / "models" / "all-indo-e5-small-v4"

# ============================================================
# LOAD MODEL + CLIENT
# ============================================================
print(f"[INFO] Loading embedding model: {EMBED_MODEL_PATH}")
embedder = SentenceTransformer(str(EMBED_MODEL_PATH))

QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333))

client = QdrantClient(
    host=QDRANT_HOST,
    port=QDRANT_PORT
)

# ============================================================
# COLLECTION SETUP
# ============================================================
def recreate_collection(dimension: int):
    print(f"[WARN] Dropping old collection '{COLLECTION_NAME}'...")
    try:
        client.delete_collection(collection_name=COLLECTION_NAME)
    except:
        pass

    print(f"[INFO] Creating fresh collection '{COLLECTION_NAME}' (dim={dimension})")
    client.recreate_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=models.VectorParams(
            size=dimension,
            distance=models.Distance.COSINE
        )
    )

# ============================================================
# MAIN INGEST FUNCTION
# ============================================================
def ingest_style():
    if not DATA_PATH.exists():
        print(f"[ERROR] File not found: {DATA_PATH}")
        return

    # ----------------------------------------
    # LOAD JSONL
    # ----------------------------------------
    records = []
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))

    print(f"[INFO] Loaded {len(records)} style records from {DATA_PATH}")

    # ----------------------------------------
    # BUILD TEXTS FOR EMBEDDING
    # customer + admin + style notes
    # ----------------------------------------
    embed_texts = []
    for r in records:
        c = (r.get("customer") or "").strip()
        a = (r.get("admin") or "").strip()
        s = (r.get("style_notes") or "").strip()

        # Jika admin kosong (jarang, tapi aman)
        if not a:
            a = "Admin response unavailable"

        text = f"Customer: {c}\nAdmin: {a}\nStyleNotes: {s}"
        embed_texts.append(text)

    # ----------------------------------------
    # GENERATE EMBEDDINGS
    # ----------------------------------------
    print("[INFO] Generating embeddings...")
    vectors = embedder.encode(embed_texts, batch_size=16, show_progress_bar=True)
    dim = vectors.shape[1]

    # ----------------------------------------
    # RECREATE COLLECTION
    # ----------------------------------------
    recreate_collection(dim)

    # ----------------------------------------
    # PREPARE PAYLOADS
    # ----------------------------------------
    ids = []
    payloads = []
    for i, r in enumerate(records):
        ids.append(i + 1)

        payloads.append({
            "id": r.get("id"),
            "intent": r.get("intent"),
            "customer": r.get("customer"),
            "admin": r.get("admin"),
            "dialogue": r.get("dialogue"),
            "style_notes": r.get("style_notes"),
            "embedding_target": "all-indo-e5-small-v4",
            "source": "style_chat"
        })

    # ----------------------------------------
    # UPSERT TO QDRANT
    # ----------------------------------------
    print("[DEBUG] Sample Embedding Text:")
    print(embed_texts[0][:500], "...")

    print("[DEBUG] Sample Payload:")
    print(json.dumps(payloads[0], indent=2, ensure_ascii=False))

    print("[INFO] Uploading to Qdrant...")
    client.upsert(
        collection_name=COLLECTION_NAME,
        points=models.Batch(
            ids=ids,
            vectors=vectors.tolist(),
            payloads=payloads
        )
    )

    print(f"[SUCCESS] Indexed {len(records)} style chat entries into '{COLLECTION_NAME}'")
    print("[INFO] Example record:")
    print(json.dumps(payloads[0], indent=2, ensure_ascii=False))

# ============================================================
# ENTRY POINT
# ============================================================
if __name__ == "__main__":
    ingest_style()