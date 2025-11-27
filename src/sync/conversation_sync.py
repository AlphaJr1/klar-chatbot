import os
import time
import requests
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
from src.storage.conversation_db import ConversationDB

class ConversationSync:
    def __init__(self):
        self.node_server_url = os.getenv(
            "NODE_SERVER_URL", 
            "https://unproportionably-subsacral-kecia.ngrok-free.dev"
        )
        self.db = ConversationDB()
        self.timeout = 10
    
    def fetch_all_conversations(self) -> Optional[List[Dict[str, Any]]]:
        try:
            url = f"{self.node_server_url}/api/conversations"
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            try:
                data = response.json()
            except ValueError as json_err:
                print(f"[SYNC] JSON parsing error: {json_err}")
                print(f"[SYNC] Response preview: {response.text[:500]}")
                return None
            
            if data.get("success") and "conversations" in data:
                return data["conversations"]
            
            return None
        
        except Exception as e:
            print(f"[SYNC] Error fetching conversations: {e}")
            return None
    
    def fetch_messages(self, phone_number: str) -> Optional[List[Dict[str, Any]]]:
        try:
            url = f"{self.node_server_url}/api/messages/{phone_number}"
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            try:
                data = response.json()
            except ValueError as json_err:
                print(f"[SYNC] JSON parsing error for {phone_number}: {json_err}")
                print(f"[SYNC] Response preview: {response.text[:500]}")
                return None
            
            if data.get("success") and "messages" in data:
                return data["messages"]
            
            return None
        
        except Exception as e:
            print(f"[SYNC] Error fetching messages for {phone_number}: {e}")
            return None
    
    def sync_conversation(self, phone_number: str) -> bool:
        try:
            messages = self.fetch_messages(phone_number)
            
            if messages is None:
                return False
            
            print(f"[SYNC] Fetched {len(messages)} messages for {phone_number}")
            
            existing = self.db.get_conversation(phone_number)
            
            if existing:
                print(f"[SYNC] Updating existing conversation for {phone_number}")
                self.db.update_messages(phone_number, messages)
            else:
                print(f"[SYNC] Creating new conversation for {phone_number}")
                metadata = {
                    "lastMessage": messages[-1].get("text", "") if messages else "",
                    "lastTimestamp": messages[-1].get("timestamp", "") if messages else "",
                    "messageCount": len(messages)
                }
                self.db.save_conversation(phone_number, metadata, messages)
            
            print(f"[SYNC] ✅ Successfully synced {phone_number}")
            return True
        
        except Exception as e:
            print(f"[SYNC] Error sync conversation {phone_number}: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def sync_all(self) -> Dict[str, Any]:
        start_time = time.time()
        
        conversations = self.fetch_all_conversations()
        
        if conversations is None:
            return {
                "success": False,
                "error": "Failed to fetch conversations from node server",
                "synced_count": 0,
                "duration": time.time() - start_time
            }
        
        synced_count = 0
        failed_count = 0
        
        for conv in conversations:
            phone_number = conv.get("phoneNumber")
            if not phone_number:
                continue
            
            success = self.sync_conversation(phone_number)
            if success:
                synced_count += 1
            else:
                failed_count += 1
        
        duration = time.time() - start_time
        
        self.db.update_sync_stats(duration)
        
        return {
            "success": True,
            "synced_count": synced_count,
            "failed_count": failed_count,
            "total_conversations": len(conversations),
            "duration": round(duration, 2),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def get_conversation_for_summary(self, phone_number: str) -> List[Dict[str, Any]]:
        self.sync_conversation(phone_number)
        
        return self.db.get_messages(phone_number)
