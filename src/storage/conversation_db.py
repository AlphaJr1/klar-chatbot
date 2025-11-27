import os
import json
import threading
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional

class ConversationDB:
    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            db_path = os.path.join("data", "storage", "conversations.json")
        
        self.db_path = db_path
        self._lock = threading.Lock()
        self._ensure_db_exists()
    
    def _ensure_db_exists(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        if not os.path.exists(self.db_path):
            initial_data = {
                "version": "1.0",
                "lastFullSync": None,
                "conversations": {},
                "stats": {
                    "totalConversations": 0,
                    "totalMessages": 0,
                    "lastSyncDuration": 0
                }
            }
            with open(self.db_path, "w", encoding="utf-8") as f:
                json.dump(initial_data, f, indent=2, ensure_ascii=False)
    
    def _read_db(self) -> Dict[str, Any]:
        with self._lock:
            try:
                with open(self.db_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    data = json.loads(content)
                    return data
            except json.JSONDecodeError as e:
                print(f"[DB] ❌ JSON error in {self.db_path}: {e}")
                backup_path = f"{self.db_path}.corrupted.backup"
                import shutil
                shutil.copy(self.db_path, backup_path)
                print(f"[DB] 📦 Corrupt file backed up to {backup_path}")
                print(f"[DB] 🔄 Reinitializing database...")
                
                initial_data = {
                    "version": "1.0",
                    "lastFullSync": None,
                    "conversations": {},
                    "stats": {
                        "totalConversations": 0,
                        "totalMessages": 0,
                        "lastSyncDuration": 0
                    }
                }
                with open(self.db_path, "w", encoding="utf-8") as f:
                    json.dump(initial_data, f, indent=2, ensure_ascii=False)
                return initial_data
    
    def _write_db(self, data: Dict[str, Any]):
        with self._lock:
            temp_path = f"{self.db_path}.tmp"
            try:
                with open(temp_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                
                with open(temp_path, "r", encoding="utf-8") as f:
                    json.load(f)
                
                import shutil
                shutil.move(temp_path, self.db_path)
            except Exception as e:
                print(f"[DB] ❌ Error writing database: {e}")
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                raise
    
    def get_conversation(self, phone_number: str) -> Optional[Dict[str, Any]]:
        data = self._read_db()
        return data["conversations"].get(phone_number)
    
    def save_conversation(
        self, 
        phone_number: str, 
        metadata: Dict[str, Any],
        messages: List[Dict[str, Any]]
    ):
        data = self._read_db()
        
        now = datetime.now(timezone.utc).isoformat()
        
        existing = data["conversations"].get(phone_number)
        if existing:
            existing_messages = existing.get("messages", [])
            existing_msg_ids = {msg["messageId"] for msg in existing_messages}
            
            new_messages = [
                msg for msg in messages 
                if msg["messageId"] not in existing_msg_ids
            ]
            
            all_messages = existing_messages + new_messages
            all_messages.sort(key=lambda x: x.get("timestamp", "0"))
        else:
            all_messages = sorted(messages, key=lambda x: x.get("timestamp", "0"))
        
        for msg in all_messages:
            if "syncedAt" not in msg:
                msg["syncedAt"] = now
        
        data["conversations"][phone_number] = {
            "phoneNumber": phone_number,
            "metadata": {
                **metadata,
                "lastSyncAt": now,
                "firstSeenAt": existing.get("metadata", {}).get("firstSeenAt", now) if existing else now,
                "messageCount": len(all_messages)
            },
            "messages": all_messages
        }
        
        data["stats"]["totalConversations"] = len(data["conversations"])
        data["stats"]["totalMessages"] = sum(
            len(conv["messages"]) 
            for conv in data["conversations"].values()
        )
        
        self._write_db(data)
    
    def update_messages(self, phone_number: str, new_messages: List[Dict[str, Any]]):
        data = self._read_db()
        
        if phone_number not in data["conversations"]:
            return
        
        conversation = data["conversations"][phone_number]
        existing_messages = conversation.get("messages", [])
        existing_msg_ids = {msg["messageId"] for msg in existing_messages}
        
        messages_to_add = [
            msg for msg in new_messages 
            if msg["messageId"] not in existing_msg_ids
        ]
        
        if not messages_to_add:
            return
        
        now = datetime.now(timezone.utc).isoformat()
        for msg in messages_to_add:
            msg["syncedAt"] = now
        
        all_messages = existing_messages + messages_to_add
        all_messages.sort(key=lambda x: x.get("timestamp", "0"))
        
        conversation["messages"] = all_messages
        conversation["metadata"]["messageCount"] = len(all_messages)
        conversation["metadata"]["lastSyncAt"] = now
        
        data["stats"]["totalMessages"] = sum(
            len(conv["messages"]) 
            for conv in data["conversations"].values()
        )
        
        self._write_db(data)
    
    def get_all_phone_numbers(self) -> List[str]:
        data = self._read_db()
        return list(data["conversations"].keys())
    
    def get_last_sync_time(self) -> Optional[str]:
        data = self._read_db()
        return data.get("lastFullSync")
    
    def set_last_sync_time(self, timestamp: str):
        data = self._read_db()
        data["lastFullSync"] = timestamp
        self._write_db(data)
    
    def get_total_message_count(self) -> int:
        data = self._read_db()
        return data["stats"]["totalMessages"]
    
    def update_sync_stats(self, duration: float):
        data = self._read_db()
        data["stats"]["lastSyncDuration"] = duration
        data["lastFullSync"] = datetime.now(timezone.utc).isoformat()
        self._write_db(data)
    
    def get_messages(self, phone_number: str) -> List[Dict[str, Any]]:
        conversation = self.get_conversation(phone_number)
        if not conversation:
            return []
        return conversation.get("messages", [])
