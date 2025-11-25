import os
import json
import threading
from datetime import datetime, timezone
from typing import Any, Dict, Optional

class ChatLogger:
    def __init__(self):
        self._lock = threading.Lock()
        self.log_dir = os.path.join("data", "storage", "logs")
        os.makedirs(self.log_dir, exist_ok=True)
    
    def _get_log_path(self) -> str:
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        return os.path.join(self.log_dir, f"chat-{today}.jsonl")
    
    def _write_log(self, record: Dict[str, Any]) -> None:
        path = self._get_log_path()
        line = json.dumps(record, ensure_ascii=False)
        
        with self._lock:
            with open(path, "a", encoding="utf-8") as f:
                f.write(line + "\n")
    
    def log_incoming(
        self,
        user_id: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        record = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "direction": "incoming",
            "user_id": user_id,
            "message": message,
            "message_length": len(message),
            "metadata": metadata or {}
        }
        self._write_log(record)
    
    def log_outgoing(
        self,
        user_id: str,
        response: str,
        status: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        record = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "direction": "outgoing",
            "user_id": user_id,
            "response": response,
            "response_length": len(response),
            "status": status,
            "metadata": metadata or {}
        }
        self._write_log(record)

_CHAT_LOGGER_SINGLETON: Optional[ChatLogger] = None

def get_chat_logger() -> ChatLogger:
    global _CHAT_LOGGER_SINGLETON
    if _CHAT_LOGGER_SINGLETON is None:
        _CHAT_LOGGER_SINGLETON = ChatLogger()
    return _CHAT_LOGGER_SINGLETON
