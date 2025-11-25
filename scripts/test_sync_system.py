import requests
import json
import time

BASE_URL = "http://localhost:8081"

def test_sync_status():
    print("=" * 60)
    print("TEST 1: Sync Status")
    print("=" * 60)
    
    response = requests.get(f"{BASE_URL}/sync/status")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(json.dumps(data, indent=2))
    else:
        print(f"Error: {response.text}")

def test_manual_sync():
    print("\n" + "=" * 60)
    print("TEST 2: Manual Sync")
    print("=" * 60)
    
    response = requests.post(f"{BASE_URL}/sync/now")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(json.dumps(data, indent=2))
    else:
        print(f"Error: {response.text}")

def test_summarize_with_auto_update():
    print("\n" + "=" * 60)
    print("TEST 3: Summarize dengan Auto-Update")
    print("=" * 60)
    
    payload = {
        "session_id": "6282216860317"
    }
    
    response = requests.post(f"{BASE_URL}/summarize", json=payload)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\nSuccess: {data.get('success')}")
        print(f"Session ID: {data.get('session_id')}")
        print(f"Message Count: {data.get('message_count')}")
        print(f"Source: {data.get('metadata', {}).get('source')}")
        print(f"\n{'='*60}")
        print("SUMMARY:")
        print("="*60)
        print(data.get('summary', 'No summary'))
        print("="*60)
    else:
        print(f"Error: {response.text}")

def test_verify_conversations_db():
    print("\n" + "=" * 60)
    print("TEST 4: Verify Conversations DB")
    print("=" * 60)
    
    import os
    db_path = "data/storage/conversations.json"
    
    if os.path.exists(db_path):
        with open(db_path, "r") as f:
            data = json.load(f)
        
        print(f"Database Version: {data.get('version')}")
        print(f"Last Full Sync: {data.get('lastFullSync')}")
        print(f"Total Conversations: {data.get('stats', {}).get('totalConversations')}")
        print(f"Total Messages: {data.get('stats', {}).get('totalMessages')}")
        print(f"Last Sync Duration: {data.get('stats', {}).get('lastSyncDuration')}s")
        
        print(f"\nConversations:")
        for phone, conv in data.get('conversations', {}).items():
            msg_count = len(conv.get('messages', []))
            last_sync = conv.get('metadata', {}).get('lastSyncAt')
            print(f"  - {phone}: {msg_count} messages (synced: {last_sync})")
    else:
        print("Database file not found!")

if __name__ == "__main__":
    print("Testing Conversation Sync System")
    print(f"Base URL: {BASE_URL}\n")
    
    try:
        health = requests.get(f"{BASE_URL}/health", timeout=3)
        if health.status_code != 200:
            print("Server tidak running!")
            exit(1)
    except Exception as e:
        print(f"Server tidak running! Error: {e}")
        exit(1)
    
    test_sync_status()
    
    test_manual_sync()
    
    time.sleep(2)
    
    test_summarize_with_auto_update()
    
    test_verify_conversations_db()
    
    print("\n" + "="*60)
    print("Testing selesai!")
    print("="*60)
