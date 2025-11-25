import os, json, sys
from pathlib import Path
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient

BASE = os.path.dirname(os.path.dirname(__file__))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

from convo.ollama_client import OllamaClient

KB_DIR = Path(os.getenv("KB_DIR", "kb"))
PROJECT_DIR = Path(__file__).resolve().parent.parent
LOCAL_MODEL_DIR = PROJECT_DIR.parent / "models"

E5_PATH  = str(LOCAL_MODEL_DIR / "all-indo-e5-small-v4")
BGE_PATH = str(LOCAL_MODEL_DIR / "bge-base-en-v1.5")

class Retriever:
    def __init__(self, kb_dir: Path = KB_DIR):
        self.kb_dir = kb_dir

        self.e5 = SentenceTransformer(E5_PATH)
        self.bge = SentenceTransformer(BGE_PATH)

        self.llm = OllamaClient(model="qwen2.5:7b-instruct")

        self._connect_qdrant()

        self._load_sources()

    def _connect_qdrant(self):
        try:
            host = os.getenv("QDRANT_URL") or os.getenv("QDRANT_HOST") or "http://127.0.0.1:6333"
            self.qdrant = QdrantClient(url=host, timeout=3.0)
            self.qdrant.get_collections()
            print(f"Connected ({host})")
        except Exception as e:
            print(f"❌ Failed ({e})")
            self.qdrant = None

    def _load_sources(self):
        def load_jsonl(name):
            file = self.kb_dir / "compiled" / name
            if not file.exists():
                print(f"[Retriever] ⚠ Missing file {name}")
                return []

            with open(file, "r", encoding="utf-8") as f:
                return [json.loads(line) for line in f if line.strip()]

        self.manual      = load_jsonl("manual_chunks_final.jsonl")
        self.chat_pairs  = load_jsonl("chat_pairs.jsonl")
        self.style       = load_jsonl("style_index.jsonl")

    def translate_query(self, text: str) -> str:
        try:
            out = self.llm.generate(
                system="Translate the user query into short, clear English.",
                prompt=text,
                temperature=0
            )
            return out.strip()
        except:
            return text
        
    def manual_query_to_summary_style(self, user_query: str) -> str:
        try:
            system_prompt = (
                "You are a technical summarizer for Honeywell Electronic Air Cleaner (EAC) manuals. "
                "Rewrite the user query into a single technical English sentence in the same style "
                "as the 'summary' field found in service manuals.\n\n"
                "Rules:\n"
                "- Start with a verb such as 'Summarizes', 'Describes', 'Explains', or 'Outlines'.\n"
                "- Must be 1 sentence only.\n"
                "- Mention the relevant topic clearly (wiring, installation, airflow, safety, power supply, troubleshooting, mounting, collector cell, ionizer, etc).\n"
                "- Keep it short, direct, and factual.\n"
                "- Do NOT mention user, customer, or chat context.\n"
                "- Do NOT write a question.\n"
                "- Output only the sentence."
            )

            out = self.llm.generate(
                system=system_prompt,
                prompt=user_query,
                temperature=0.1
            )
            return out.strip()
        except:
            return f"Summarizes technical information regarding: {user_query}"

    def retrieve_chat_history(self, query: str, k: int = 3):
        if not self.qdrant:
            return []

        q_emb = self.e5.encode([query])[0]

        res = self.qdrant.search(
            collection_name="chat_history_pairs",
            query_vector=q_emb.tolist(),
            limit=k,
            with_payload=True
        )

        hits = []
        for pt in res:
            p = pt.payload or {}
            hits.append({
                "customer": p.get("customer", ""),
                "admin":    p.get("admin", ""),
                "summary":  p.get("summary", ""),
                "topic":    p.get("topic", ""),
                "score":    float(pt.score)
            })
        return hits

    def retrieve_manual_book(self, user_query: str, k: int = 1):
        if not self.qdrant:
            return []

        # 1) Terjemahkan user query ke bahasa Inggris
        english_q = self.translate_query(user_query)

        # 2) Ubah query ke gaya SUMMARY teknis
        summary_query = self.manual_query_to_summary_style(english_q)

        # 3) Embed menggunakan BGE-base
        q_emb = self.bge.encode([summary_query])[0]

        # 4) Retrieve dari Qdrant
        res = self.qdrant.search(
            collection_name="manual_book",
            query_vector=q_emb.tolist(),
            limit=k,
            with_payload=True
        )

        hits = []
        for pt in res:
            p = pt.payload or {}
            hits.append({
                "summary_query_used": summary_query,
                "summary": p.get("summary", ""),
                "model":   p.get("model", ""),
                "section": p.get("section", ""),
                "content": p.get("content", ""),
                "score":   float(pt.score)
            })
        return hits

    def retrieve_style(self, query: str, k: int = 1):
        if not self.qdrant:
            return []

        formatted = f"Customer: {query}\nAdmin:\nStyleNotes:"
        q_emb = self.e5.encode([formatted])[0]

        res = self.qdrant.search(
            collection_name="style_guide",
            query_vector=q_emb.tolist(),
            limit=k,
            with_payload=True
        )

        hits = []
        for pt in res:
            p = pt.payload or {}
            hits.append({
                "intent":      p.get("intent", ""),
                "customer":    p.get("customer", ""),
                "admin":       p.get("admin", ""),
                "style_notes": p.get("style_notes", ""),
                "score":       float(pt.score)
            })
        return hits

    def retrieve(self, query: str, k: int = 3, man_style_k: int = 1):
        query = query.strip()
        if not query:
            return {"chat_history": [], "manual_book": [], "style": []}

        chat_hits = self.retrieve_chat_history(query, k=k)

        manual_hits = self.retrieve_manual_book(query, k=man_style_k)

        style_hits = self.retrieve_style(query, k=man_style_k)

        return {
            "chat_history": chat_hits,
            "manual_book":  manual_hits,
            "style":        style_hits
        }

if __name__ == "__main__":
    retriever = Retriever()
    print("\n[Retriever] Ready.")

    while True:
        q = input("\n🟢 Query pelanggan: ").strip()
        if not q:
            break

        out = retriever.retrieve(q)
        print(json.dumps(out, indent=2, ensure_ascii=False))
