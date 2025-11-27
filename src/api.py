import os, time, json, requests, uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from threading import Thread
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from src.convo.engine import ConversationEngine
from src.convo.summarizer import ConversationSummarizer
from src.sync.conversation_sync import ConversationSync

APP_PORT = int(os.getenv("APP_PORT", "8080"))
app = FastAPI(title="KLAR RAG API", version="1.0-clean")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

engine = ConversationEngine()
summarizer = ConversationSummarizer()
sync_service = ConversationSync()

def periodic_sync():
    while True:
        try:
            print("[SYNC] Starting periodic sync...")
            result = sync_service.sync_all()
            print(f"[SYNC] Complete: {result['synced_count']} conversations in {result['duration']}s")
        except Exception as e:
            print(f"[SYNC] Error: {e}")
        
        time.sleep(60)

@app.on_event("startup")
async def startup_event():
    sync_thread = Thread(target=periodic_sync, daemon=True)
    sync_thread.start()
    print("[SYNC] Background sync started (every 60s)")

class ChatIn(BaseModel):
    user_id: str
    text: str

class Bubble(BaseModel):
    type: str = "text"
    text: Optional[str] = None

class ChatOut(BaseModel):
    bubbles: List[Bubble]
    next: str
    status: Optional[str] = "open"
    stage: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None

class FeedbackIn(BaseModel):
    user_id: str
    rating: int = Field(..., ge=1, le=5)
    note: Optional[str] = None

class SummarizeIn(BaseModel):
    session_id: str
    messages: Optional[List[Dict[str, Any]]] = None
    use_local_logs: bool = False
    send_to_node: bool = False

class SummarizeOut(BaseModel):
    success: bool
    session_id: str
    summary: Optional[str] = None
    message_count: Optional[int] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

@app.get("/health")
def health():
    return {
        "ok": True,
        "engine_ready": True,
        "version": app.version,
    }

@app.post("/chat", response_model=ChatOut)
def chat(payload: ChatIn):
    start = time.time()
    try:
        if not payload.text.strip():
            return {"bubbles": [], "next": "await_reply", "status": "open", "meta": {"error": "empty message"}}

        ADMIN_SECRET = os.getenv("ADMIN_SECRET_KEY", "dev_reset_2024")
        user_text = payload.text.strip()
        
        if user_text.startswith("/dev reset "):
            parts = user_text.split()
            if len(parts) >= 3 and parts[2] == ADMIN_SECRET:
                try:
                    engine.memstore.clear(payload.user_id)
                    return {
                        "bubbles": [{"type": "text", "text": f"✅ Memory reset berhasil untuk user: {payload.user_id}"}],
                        "next": "await_reply",
                        "status": "open",
                        "meta": {"admin_action": "memory_reset", "user_id": payload.user_id}
                    }
                except Exception as e:
                    return {
                        "bubbles": [{"type": "text", "text": f"❌ Gagal reset memory: {str(e)}"}],
                        "next": "await_reply",
                        "status": "open",
                        "meta": {"error": str(e)}
                    }
            else:
                return {
                    "bubbles": [{"type": "text", "text": "❌ Invalid secret key"}],
                    "next": "await_reply",
                    "status": "open",
                    "meta": {"error": "invalid_secret"}
                }
        
        if user_text.startswith("/dev pending "):
            parts = user_text.split(maxsplit=2)
            if len(parts) >= 3 and parts[2] == ADMIN_SECRET:
                try:
                    engine.memstore.set_flag(payload.user_id, "sop_pending", True)
                    
                    name_question = engine.data_collector.generate_question(payload.user_id, "name")
                    engine.memstore.append_history(payload.user_id, "bot", name_question)
                    
                    return {
                        "bubbles": [{"type": "text", "text": name_question}],
                        "next": "await_reply",
                        "status": "open",
                        "meta": {"admin_action": "force_pending", "user_id": payload.user_id}
                    }
                except Exception as e:
                    return {
                        "bubbles": [{"type": "text", "text": f"❌ Gagal trigger pending: {str(e)}"}],
                        "next": "await_reply",
                        "status": "open",
                        "meta": {"error": str(e)}
                    }
            else:
                return {
                    "bubbles": [{"type": "text", "text": "❌ Invalid secret key"}],
                    "next": "await_reply",
                    "status": "open",
                    "meta": {"error": "invalid_secret"}
                }
        
        result = engine.handle(payload.user_id, payload.text)
        
        if "status" not in result:
            result["status"] = "open"

        try:
            reply_text = result["bubbles"][0]["text"]
            request_id = str(uuid.uuid4())
            
            webhook_payload = {
                "request_id": request_id,
                "user_id": payload.user_id,
                "text": payload.text,
                "reply": reply_text,
                "status": result.get("status", "open"),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            max_retries = 2
            for attempt in range(max_retries):
                try:
                    response = requests.post(
                        "https://unproportionably-subsacral-kecia.ngrok-free.dev/api/send-from-engine",
                        json=webhook_payload,
                        timeout=5,
                    )
                    response.raise_for_status()
                    print(f"[BRIDGE] Sent to NodeJS: request_id={request_id}, user_id={payload.user_id}, status={result.get('status', 'open')}")
                    break
                except requests.exceptions.RequestException as e:
                    if attempt == max_retries - 1:
                        print(f"[BRIDGE ERROR] Failed after {max_retries} attempts: {e}")
                    else:
                        time.sleep(0.5 * (attempt + 1))
        except Exception as e:
            print("[BRIDGE ERROR]", e)

        duration = round((time.time() - start) * 1000, 2)
        print(f"[CHAT] {payload.user_id} | {payload.text[:60]} ({duration}ms)")

        result["meta"] = {"took_ms": duration}
        return result

    except Exception as e:
        print(f"[ERROR] chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class SendIn(BaseModel):
    to: str
    text: str

NODE_SERVER_URL = os.getenv("NODE_SERVER_URL", "https://unproportionably-subsacral-kecia.ngrok-free.dev/api/send")

@app.post("/send")
def send_message(payload: SendIn):
    try:
        node_payload = {
            "to": payload.to,
            "message": payload.text,
            "type": "text"
        }

        print(f"[SEND] Forwarding to NodeJS {NODE_SERVER_URL}: {node_payload}")

        r = requests.post(NODE_SERVER_URL, json=node_payload, timeout=10)
        r.raise_for_status()

        return {
            "ok": True,
            "sent_to": payload.to,
            "node_response": r.json()
        }

    except Exception as e:
        print(f"[ERROR] send_message: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/feedback")
def feedback(payload: FeedbackIn):
    os.makedirs("data/storage/logs", exist_ok=True)
    fb_path = os.path.join("data/storage/logs", "feedback.jsonl")

    entry = {
        "user_id": payload.user_id,
        "rating": payload.rating,
        "note": payload.note,
        "ts": datetime.utcnow().isoformat(),
    }
    with open(fb_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    print(f"[FEEDBACK] {payload.user_id} → {payload.rating}")
    return {"ok": True}

@app.get("/admin/logs")
def admin_logs(
    limit: int = Query(200, ge=1, le=2000),
):
    folder = "data/storage/logs"
    files = sorted(
        [f for f in os.listdir(folder) if f.startswith("wa-") and f.endswith(".jsonl")],
        reverse=True,
    )
    if not files:
        return {"ok": True, "items": []}

    path = os.path.join(folder, files[0])
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                rows.append(json.loads(line.strip()))
            except Exception:
                continue
    rows = rows[-limit:]
    return {"ok": True, "count": len(rows), "items": rows}

@app.post("/summarize", response_model=SummarizeOut)
def summarize(payload: SummarizeIn):
    try:
        result = summarizer.summarize(
            session_id=payload.session_id,
            messages=payload.messages,
            use_local_logs=payload.use_local_logs,
            send_to_node=payload.send_to_node,
            auto_update=True
        )
        return result
    except Exception as e:
        print(f"[ERROR] summarize: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/sync/now")
def sync_now():
    try:
        result = sync_service.sync_all()
        return result
    except Exception as e:
        print(f"[ERROR] sync_now: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/sync/status")
def sync_status():
    try:
        return {
            "ok": True,
            "last_sync": sync_service.db.get_last_sync_time(),
            "conversation_count": len(sync_service.db.get_all_phone_numbers()),
            "total_messages": sync_service.db.get_total_message_count(),
            "phone_numbers": sync_service.db.get_all_phone_numbers()
        }
    except Exception as e:
        print(f"[ERROR] sync_status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/admin/reset-memory")
def admin_reset_memory(user_id: str, secret: str = Query(...)):
    ADMIN_SECRET = os.getenv("ADMIN_SECRET_KEY", "dev_reset_2024")
    
    if secret != ADMIN_SECRET:
        raise HTTPException(status_code=403, detail="Invalid secret key")
    
    try:
        engine.memstore.clear(user_id)
        return {
            "ok": True,
            "message": f"Memory reset berhasil untuk user: {user_id}",
            "user_id": user_id
        }
    except Exception as e:
        print(f"[ERROR] admin_reset_memory: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/admin/memory-stats")
def admin_memory_stats(secret: str = Query(...)):
    ADMIN_SECRET = os.getenv("ADMIN_SECRET_KEY", "dev_reset_2024")
    
    if secret != ADMIN_SECRET:
        raise HTTPException(status_code=403, detail="Invalid secret key")
    
    try:
        stats = engine.memstore.stats()
        all_users = list(engine.memstore._records.keys())
        return {
            "ok": True,
            "stats": stats,
            "user_ids": all_users,
            "total_users": len(all_users)
        }
    except Exception as e:
        print(f"[ERROR] admin_memory_stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# === Run manual ===
# uvicorn src.api:app --host 0.0.0.0 --port 8080 --reload