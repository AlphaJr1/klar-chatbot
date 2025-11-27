import os
import requests
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
from .ollama_client import OllamaClient
from src.sync.conversation_sync import ConversationSync

class ConversationSummarizer:
    def __init__(self):
        self.ollama = OllamaClient()
        self.node_server_url = os.getenv("NODE_SERVER_URL", "https://unproportionably-subsacral-kecia.ngrok-free.dev")
        self.sync_service = ConversationSync()
    
    def fetch_conversation_from_node(self, session_id: str) -> Optional[List[Dict[str, Any]]]:
        try:
            endpoint = f"{self.node_server_url}/api/get-conversation"
            params = {"session_id": session_id}
            
            response = requests.get(endpoint, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if data.get("success") and "messages" in data:
                return data["messages"]
            
            return None
        
        except Exception as e:
            print(f"[SUMMARIZER] Error fetching from node: {e}")
            return None
    
    def fetch_conversation_from_logs(self, user_id: str, date: Optional[str] = None) -> List[Dict[str, Any]]:
        if date is None:
            date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        
        log_path = os.path.join("data", "storage", "logs", f"chat-{date}.jsonl")
        messages = []
        
        if not os.path.exists(log_path):
            return messages
        
        with open(log_path, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    record = json.loads(line.strip())
                    if record.get("user_id") == user_id:
                        messages.append(record)
                except Exception:
                    continue
        
        return messages
    
    def prepare_conversation_text(self, messages: List[Dict[str, Any]]) -> str:
        conversation_lines = []
        
        for msg in messages:
            if "direction" in msg:
                direction = msg["direction"]
                if direction == "incoming":
                    text = msg.get("message", "")
                    conversation_lines.append(f"Pelanggan: {text}")
                elif direction == "outgoing":
                    text = msg.get("response", "")
                    conversation_lines.append(f"Bot: {text}")
            
            elif "isFromMe" in msg:
                is_from_me = msg.get("isFromMe", False)
                text = msg.get("text", "")
                if is_from_me:
                    conversation_lines.append(f"Bot: {text}")
                else:
                    conversation_lines.append(f"Pelanggan: {text}")
        
        return "\n".join(conversation_lines)
    
    def summarize_with_llm(self, conversation_text: str) -> str:
        system = "Kamu adalah asisten yang meringkas percakapan customer service untuk produk Electronic Air Cleaner Honeywell."
        
        prompt = f"""Percakapan:
{conversation_text}

Buatkan ringkasan yang mencakup:
1. Identitas pelanggan (nama jika disebutkan)
2. Topik/masalah utama
3. Kronologi singkat percakapan (poin-poin penting)
4. Informasi penting: produk yang digunakan, keluhan spesifik, solusi yang sudah dicoba
5. Data pelanggan yang sudah dikumpulkan (nama, produk, alamat)
6. Status: apakah masalah sudah resolved, pending untuk teknisi, atau masih open
7. Tindakan selanjutnya yang perlu dilakukan

Format dalam bahasa Indonesia, ringkas tapi lengkap. Gunakan struktur:

RINGKASAN PERCAKAPAN
Pelanggan: [nama atau "Belum disebutkan"]
Topik: [intent/masalah utama]

KRONOLOGI:
- [step by step singkat]

INFORMASI PENTING:
- Produk: [tipe produk jika disebutkan]
- Masalah: [deskripsi masalah]
- Solusi yang dicoba: [langkah troubleshooting yang sudah dilakukan]

DATA PELANGGAN:
- Nama: [...]
- Produk: [...]
- Alamat: [...]

STATUS & TINDAKAN SELANJUTNYA:
- Status: [open/pending/resolved]
- Tindakan: [apa yang perlu dilakukan admin/teknisi]
"""
        
        try:
            response = self.ollama.generate(system, prompt, temperature=0.2)
            return response.strip()
        except Exception as e:
            print(f"[SUMMARIZER] LLM error: {e}")
            return f"Error generating summary: {str(e)}"
    
    def send_summary_to_node(self, session_id: str, summary: str) -> bool:
        try:
            endpoint = f"{self.node_server_url}/api/receive-summary"
            payload = {
                "session_id": session_id,
                "summary": summary,
                "generated_at": datetime.now(timezone.utc).isoformat()
            }
            
            response = requests.post(endpoint, json=payload, timeout=10)
            response.raise_for_status()
            
            return True
        
        except Exception as e:
            print(f"[SUMMARIZER] Error sending to node: {e}")
            return False
    
    def summarize(
        self, 
        session_id: str, 
        messages: Optional[List[Dict[str, Any]]] = None,
        use_local_logs: bool = False,
        send_to_node: bool = False,
        auto_update: bool = True
    ) -> Dict[str, Any]:
        
        if messages is None:
            if use_local_logs:
                messages = self.fetch_conversation_from_logs(session_id)
            elif auto_update:
                print(f"[SUMMARIZER] Fetching updates for {session_id}...")
                messages = self.sync_service.get_conversation_for_summary(session_id)
            else:
                messages = self.fetch_conversation_from_node(session_id)
        
        if not messages:
            return {
                "success": False,
                "error": "No messages found",
                "session_id": session_id
            }
        
        conversation_text = self.prepare_conversation_text(messages)
        summary = self.summarize_with_llm(conversation_text)
        
        if send_to_node:
            self.send_summary_to_node(session_id, summary)
        
        source = "local_logs" if use_local_logs else ("sync_db" if auto_update else "node_server")
        
        return {
            "success": True,
            "session_id": session_id,
            "summary": summary,
            "message_count": len(messages),
            "metadata": {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "source": source
            }
        }
