import os,json, socket, threading, hashlib
from datetime import datetime
from typing import Any, Dict, List, Optional

def _sha8(s: str) -> str:
    if not s:
        return ""
    return hashlib.sha1(s.encode("utf-8")).hexdigest()[:8]

def _preview(s: str, n: int = 160) -> str:
    if not s:
        return ""
    s = s.replace("\n", " ").strip()
    return (s[:n] + "…") if len(s) > n else s

def _today_path(prefix: str = "wa") -> str:
    os.makedirs("data/storage/logs", exist_ok=True)
    day = datetime.utcnow().strftime("%Y-%m-%d")
    return os.path.join("data/storage/logs", f"{prefix}-{day}.jsonl")

class SessionLogger:
    def __init__(self, file_prefix: str = "wa"):
        self.file_prefix = file_prefix
        self._lock = threading.Lock()
        self.host = socket.gethostname()

    def _ts(self) -> str:
        return datetime.utcnow().isoformat(timespec="seconds") + "Z"

    def _write(self, obj: Dict[str, Any]) -> None:
        obj.setdefault("ts", self._ts())
        obj.setdefault("host", self.host)
        path = _today_path(self.file_prefix)
        line = json.dumps(obj, ensure_ascii=False)
        with self._lock:
            if os.path.exists(path) and os.path.getsize(path) > 20_000_000:  # 20MB limit
                old = path.replace(".jsonl", f"-archived-{datetime.utcnow().isoformat(timespec='seconds')}.jsonl")
                os.rename(path, old)
            with open(path, "a", encoding="utf-8") as f:
                f.write(line + "\n")

    def log_in(self, *, jid: str, text: str, chat: str = "dm", raw: Optional[Dict[str, Any]] = None) -> None:
        self._write({"dir": "in", "chat": chat, "jid": jid, "text": text, "raw": raw})

    def log_out(self, *, jid: str, bubble_type: str, text: Optional[str] = None,
                path: Optional[str] = None, caption: Optional[str] = None,
                chat: str = "dm") -> None:
        self._write({
            "dir": "out", "chat": chat, "jid": jid,
            "bubble": bubble_type, "text": text, "path": path, "caption": caption
        })

    def log_suggest(self, *, jid: str, items: List[str], chat: str = "dm") -> None:
        self._write({"dir": "suggest", "chat": chat, "jid": jid, "items": items})

    def log_rag(self, *, jid: str, query: str, topk: List[Dict[str, Any]],
                chosen: Optional[Dict[str, Any]] = None, chat: str = "dm") -> None:
        self._write({"dir": "rag", "chat": chat, "jid": jid, "query": query, "topk": topk, "chosen": chosen})

    def log_guard(self, *, jid: str, rule: str, trigger: str, action: str, chat: str = "dm") -> None:
        self._write({"dir": "guard", "chat": chat, "jid": jid, "rule": rule, "trigger": trigger, "action": action})

    def log_triage(self, *, jid: str, step: int, text: str, chat: str = "dm") -> None:
        self._write({"dir": "triage", "chat": chat, "jid": jid, "step": step, "text": text})

    def log_escalation(self, *, jid: str, reason: str, summary: str, chat: str = "dm") -> None:
        self._write({"dir": "escalate", "chat": chat, "jid": jid, "reason": reason, "summary": summary})

    def log_escalate(self, *, jid: str, summary: str, for_admin: Dict[str, Any], chat: str = "dm") -> None:
        self._write({"dir": "escalate", "chat": chat, "jid": jid, "summary": summary, "for_admin": for_admin})

    def log_llm(self, *, jid: str, model: str, system: str, prompt: str, response: str, chat: str = "dm") -> None:
        self._write({ "dir": "llm", "chat": chat, "jid": jid, "model": model, "system": system, "prompt": prompt, "response": response })

    def log_automation(self, *, event: str, jid: Optional[str] = None, text: Optional[str] = None, detail: Optional[Dict[str, Any]] = None) -> None:
        entry = {"dir": "automation", "event": event}
        if jid:
            entry["jid"] = jid
        if text:
            entry["text"] = text
        if detail:
            entry.update(detail)
        self._write(entry)

    def log_stage(self, *, jid: str, stage: str,
                  info: Optional[Dict[str, Any]] = None,
                  prompt: Optional[str] = None,
                  response: Optional[str] = None,
                  chat: str = "dm") -> None:
        entry = {
            "dir": "stage", "chat": chat, "jid": jid, "stage": stage,
        }
        if info:
            entry["info"] = info

        if prompt is not None:
            entry["prompt_len"] = len(prompt)
            entry["prompt_sha"] = _sha8(prompt)
            entry["prompt_preview"] = _preview(prompt, 120)

        if response is not None:
            entry["response_len"] = len(response)
            entry["response_sha"] = _sha8(response)
            entry["response_preview"] = _preview(response, 160)

        stage_map = {
            "pre_rag": "PRE",
            "router": "ROU",
            "triage": "TRI",
            "rag_context": "RAG",
            "planner": "PLN",
            "composer": "CMP",
            "escalation": "ESC",
            "reply": "REP",
            "followup": "FLW",
        }
        entry["short"] = stage_map.get(stage, stage[:3].upper())

        self._write(entry)

def pre_rag(self, jid: str, info: Dict[str, Any]): self.log_stage(jid=jid, stage="pre_rag", info=info)
def router(self, jid: str, info: Dict[str, Any]): self.log_stage(jid=jid, stage="router", info=info)
def triage_stage(self, jid: str, info: Dict[str, Any]): self.log_stage(jid=jid, stage="triage", info=info)
def rag_context(self, jid: str, info: Dict[str, Any]): self.log_stage(jid=jid, stage="rag_context", info=info)
def planner(self, jid: str, info: Dict[str, Any]): self.log_stage(jid=jid, stage="planner", info=info)
def composer(self, jid: str, info: Dict[str, Any]): self.log_stage(jid=jid, stage="composer", info=info)
def escalate(self, jid: str, info: Dict[str, Any]): self.log_stage(jid=jid, stage="escalation", info=info)

_LOGGER_SINGLETON: Optional[SessionLogger] = None

def get_wa_logger() -> SessionLogger:
    global _LOGGER_SINGLETON
    if _LOGGER_SINGLETON is None:
        _LOGGER_SINGLETON = SessionLogger(file_prefix="wa")
    return _LOGGER_SINGLETON
