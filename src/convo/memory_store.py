import os, json, threading, secrets
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

def _now_iso() -> str:
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"

def _ensure_dir(path: str) -> None:
    dir_path = os.path.dirname(path)
    if dir_path and not os.path.exists(dir_path):
        os.makedirs(dir_path, exist_ok=True)

def _atomic_write(path: str, data: str):
    tmp = f"{path}.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)

# UserRecord Object
class UserRecord:
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.session_token: str = secrets.token_hex(8)
        self.name: Optional[str] = None
        self.gender: Optional[str] = None
        self.product: Optional[str] = None
        self.serial: Optional[str] = None
        self.address: Optional[str] = None
        self.summary_context: List[str] = []
        self.history: List[Dict[str, Any]] = []
        self.last_answer: Optional[str] = None
        self.flags: Dict[str, Any] = {
            "last_activity": _now_iso(),
        }
        self.slots: Dict[str, Any] = {}
        self.created_at = _now_iso()
        self.updated_at = self.created_at

    def touch(self):
        self.updated_at = _now_iso()

    def regenerate_token(self):
        self.session_token = secrets.token_hex(8)
        self.touch()

    def to_dict(self) -> Dict[str, Any]:
        return self.__dict__

# MemoryStore Class
class MemoryStore:
    def __init__(self, path: str = "data/storage/memory.json", autosave: bool = True, max_history: int = 50, debug: bool = False):
        self.path = os.path.abspath(path)
        self.autosave = autosave
        self.max_history = max_history
        self.debug = debug
        self._lock = threading.RLock()
        self._user_locks: Dict[str, threading.RLock] = {}

        if not os.path.exists(self.path):
            with open(self.path, "w", encoding="utf-8") as f:
                f.write("{}")

        if self.debug:
            print(f"[MemoryStore] Using path: {self.path}")

        self._records: Dict[str, UserRecord] = {}
        self._load()

    # Core I/O
    def _load(self):
        if not os.path.exists(self.path):
            self._records = {}
            return

        try:
            with open(self.path, "r", encoding="utf-8") as f:
                raw = f.read().strip()

            if not raw:
                data = {}
            else:
                data = json.loads(raw)

            for uid, v in data.items():
                try:
                    rec = UserRecord(uid)
                    if isinstance(v, dict):
                        CLEAN_KEYS = {
                            "user_id", "session_token",
                            "name", "gender", "product", "serial", "address",
                            "summary_context", "history", "last_answer",
                            "flags", "slots",
                            "created_at", "updated_at",
                        }
                        for key, val in v.items():
                            if key in CLEAN_KEYS:
                                setattr(rec, key, val)
                    self._records[uid] = rec
                except Exception as e:
                    print(f"[MemoryStore] Skip corrupted record for {uid}: {e}")

        except Exception as e:
            print(f"[MemoryStore] Failed to load: {e}. Resetting {self.path} to empty {{}}.")
            self._records = {}
            try:
                _atomic_write(self.path, "{}")
            except Exception as ew:
                print(f"[MemoryStore] Failed to reset file: {ew}")

    def set_debug(self, flag: bool):
        self.debug = bool(flag)

    def stats(self) -> Dict[str, Any]:
        return {
            "total_users": len(self._records),
            "total_messages": sum(len(r.history) for r in self._records.values()),
            "last_updated": max((r.updated_at for r in self._records.values()), default="N/A"),
        }

    def _save(self):
        try:
            _ensure_dir(self.path)
            data = {uid: r.to_dict() for uid, r in self._records.items()}
            _atomic_write(self.path, json.dumps(data, ensure_ascii=False, indent=2))
        except Exception as e:
            print(f"[MemoryStore] Failed to save: {e}")

    def _get_or_create(self, uid: str) -> UserRecord:
        with self._lock:
            if uid not in self._records:
                self._records[uid] = UserRecord(uid)
            return self._records[uid]
        
    def _get_user_lock(self, uid: str) -> threading.RLock:
        if uid not in self._user_locks:
            self._user_locks[uid] = threading.RLock()
        if self.debug:
            print(f"[MemoryStore] Lock acquired for user: {uid}")
        return self._user_locks[uid]

    def get(self, uid: str) -> Dict[str, Any]:
        return self._get_or_create(uid).to_dict()

    def update(self, uid: str, patch: Dict[str, Any]) -> Dict[str, Any]:
        rec = self._get_or_create(uid)

        if rec.user_id != uid:
            raise ValueError(f"[MemoryStore] Mismatch user_id: record={rec.user_id}, expected={uid}")

        with self._get_user_lock(uid):
            for k, v in patch.items():
                if k == "history":
                    for h in v or []:
                        if isinstance(h, dict) and "role" in h and "text" in h:
                            entry = {
                                "role": h["role"],
                                "text": h["text"],
                                "ts": h.get("ts") or _now_iso(),
                            }
                            rec.history.append(entry)
                    rec.history = rec.history[-self.max_history:]
                elif hasattr(rec, k):
                    setattr(rec, k, v)
            rec.touch()
            if self.autosave:
                self._save()
            return rec.to_dict()

    def clear(self, uid: str):
        with self._get_user_lock(uid):
            if uid in self._records:
                rec = self._records[uid]
                rec.regenerate_token()
                del self._records[uid]
                self._save()

    def reset_all(self):
        with self._lock:
            self._records.clear()
            self._save()

    # Section 2 — History Management
    def append_history(self, uid: str, role: str, text: str, meta: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        rec = self._get_or_create(uid)
        entry = {
            "role": role,
            "text": (text or "").strip(),
            "ts": _now_iso(),
        }
        if meta:
            entry["meta"] = dict(meta)

        with self._get_user_lock(uid):
            rec.history.append(entry)
            rec.history = rec.history[-self.max_history:]

            if role == "user":
                rec.last_answer = (text or "").strip()

            rec.touch()
            if self.autosave:
                self._save()
            return rec.to_dict()

    def get_history(self, uid: str) -> List[Dict[str, str]]:
        return list(self._get_or_create(uid).history)

    def get_chat_context(self, uid: str, n: int = 30) -> str:
        rec = self._get_or_create(uid)
        if not rec.history:
            return "(belum ada percakapan)"
        logs = rec.history[-n:]
        return "\n".join(
            f"[{h.get('ts')}] {h.get('role','user').capitalize()}: {h.get('text','').strip()}"
            for h in logs
        )

    def truncate_history(self, uid: str, keep_last: int = 5) -> Dict[str, Any]:
        rec = self._get_or_create(uid)
        with self._get_user_lock(uid):
            rec.history = rec.history[-keep_last:]
            rec.touch()
            self._save()
            return rec.to_dict()

    def export_chat_history(self, uid: str, n: int = 50) -> List[Dict[str, Any]]:
        rec = self._get_or_create(uid)
        logs = rec.history[-n:]
        return [
            {
                "timestamp": h.get("ts"),
                "role": h.get("role"),
                "text": h.get("text"),
                "user_id": uid,
                "session_id": rec.created_at,
            }
            for h in logs
        ]
    
    def flush_history(self, uid: str):
        with self._lock:
            self._save()

    # Section 3 — Context / Summary
    def add_context_entry(self, uid: str, text: str, max_items: int = 15) -> Dict[str, Any]:
        s = (text or "").strip()
        if not s:
            return self.get(uid)
        rec = self._get_or_create(uid)
        with self._get_user_lock(uid):
            if s not in rec.summary_context:
                rec.summary_context.append(s)
            rec.summary_context = rec.summary_context[-max_items:]
            rec.touch()
            if self.autosave:
                self._save()
            self.ensure_product_from_text(uid, s)
            return rec.to_dict()

    # Section 4 — Identity / Flags / State
    def set_flag(self, uid: str, key: str, value: Any) -> Dict[str, Any]:
        rec = self._get_or_create(uid)
        with self._get_user_lock(uid):
            rec.flags[key] = value

            if self.debug:
                print(f"[MemoryStore] set_flag → {uid} | {key} = {value}")

            rec.touch()
            if self.autosave:
                self._save()
            return rec.to_dict()
    
    def clear_flag(self, uid: str, key: str) -> Dict[str, Any]:
        rec = self._get_or_create(uid)
        with self._get_user_lock(uid):
            if key in rec.flags:
                del rec.flags[key]
            rec.touch()
            if self.autosave:
                self._save()
            return rec.to_dict()

    def get_flag(self, uid: str, key: str, default: Any = None) -> Any:
        return self._get_or_create(uid).flags.get(key, default)

    def set_name(self, uid: str, name: str) -> Dict[str, Any]:
        rec = self._get_or_create(uid)
        with self._get_user_lock(uid):
            rec.name = name.strip().title()
            rec.touch()
            self._save()
            return rec.to_dict()

    def set_gender(self, uid: str, gender: str) -> Dict[str, Any]:
        rec = self._get_or_create(uid)
        with self._get_user_lock(uid):
            rec.gender = gender.lower()
            rec.touch()
            self._save()
            return rec.to_dict()

    def set_product(self, uid: str, product: str) -> Dict[str, Any]:
        rec = self._get_or_create(uid)
        with self._get_user_lock(uid):
            rec.product = product.strip()
            rec.touch()
            self._save()
            return rec.to_dict()

    def set_last_step(self, uid: str, step: str) -> Dict[str, Any]:
        rec = self._get_or_create(uid)
        with self._get_user_lock(uid):
            rec.last_step = step
            rec.touch()
            self._save()
            return rec.to_dict()

    def get_identity(self, uid: str) -> Dict[str, Any]:
        rec = self._get_or_create(uid)
        return {
            "name": rec.name,
            "gender": rec.gender,
            "product": rec.product,
            "address": rec.address,
        }

    # Section 5 — Slots
    def get_slots(self, uid: str) -> Dict[str, Any]:
        return self._get_or_create(uid).slots

    def get_slot(self, uid: str, key: str, default: Any = None) -> Any:
        return self._get_or_create(uid).slots.get(key, default)

    def set_slot(self, uid: str, key: str, value: Any) -> Dict[str, Any]:
        rec = self._get_or_create(uid)
        with self._get_user_lock(uid):
            rec.slots[key] = value
            rec.touch()
            self._save()
            return rec.to_dict()

    def fill_slots(self, uid: str, new_slots: Dict[str, Any]) -> Dict[str, Any]:
        rec = self._get_or_create(uid)
        with self._get_user_lock(uid):
            rec.slots.update(new_slots)
            rec.touch()
            self._save()
            return rec.to_dict()

    def clear_slots(self, uid: str) -> Dict[str, Any]:
        rec = self._get_or_create(uid)
        with self._get_user_lock(uid):
            rec.slots.clear()
            rec.touch()
            self._save()
            return rec.to_dict()

    # Section 6 — Product Inference
    def ensure_product_from_text(self, uid: str, text: str):
        rec = self._get_or_create(uid)
        text_low = text.lower()

        product_map = {
            "eac": "Electronic Air Cleaner",
            "electronic air cleaner": "Electronic Air Cleaner"
        }
        serials = ["f57a", "f90a"]

        found_product = None
        found_serials = []

        for key, name in product_map.items():
            if key in text_low:
                found_product = name
                break

        for s in serials:
            if s in text_low:
                found_serials.append(s.upper())

        if not found_product and not found_serials:
            return  # tidak ada yang dikenali

        with self._get_user_lock(uid):
            if found_product:
                rec.product = found_product
            if found_serials:
                if rec.serial:
                    existing = set(rec.serial.split(","))
                    merged = existing.union(set(found_serials))
                    rec.serial = ", ".join(sorted(merged))
                else:
                    rec.serial = ", ".join(found_serials)
            rec.touch()
            if self.autosave:
                self._save()

    # Section 6 — Retrieve Last Bot Message
    def get_last_bot_message(self, uid: str) -> Optional[str]:
        rec = self._get_or_create(uid)
        if not rec.history:
            return None
        for h in reversed(rec.history):
            if h.get("role") == "assistant" and h.get("text"):
                return h.get("text")
        return None
    
    def get_last_user_answer(self, uid: str) -> Optional[str]:
        rec = self._get_or_create(uid)
        return rec.last_answer
    
    # Section 6 — Session Token Refresh
    def refresh_session_token(self, uid: str) -> str:
        rec = self._get_or_create(uid)
        with self._get_user_lock(uid):
            old_token = rec.session_token
            rec.session_token = secrets.token_hex(8)
            rec.touch()
            if self.autosave:
                self._save()
            print(f"[MemoryStore] Session token refreshed for {uid}: {old_token} → {rec.session_token}")
            return rec.session_token

    # Section 7 — Search
    def search(self, keyword: str) -> List[Dict[str, Any]]:
        q = keyword.lower().strip()
        results = []
        for rec in self._records.values():
            if any([
                q in (rec.product or "").lower(),
                any(q in s.lower() for s in rec.summary_context),
                any(q in (h.get("text", "").lower()) for h in rec.history),
            ]):
                results.append(rec.to_dict())
        return results