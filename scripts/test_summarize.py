import requests
import json

BASE_URL = "http://localhost:8081"

def test_summarize_with_local_logs():
    print("=" * 60)
    print("TEST: Summarize dengan local logs")
    print("=" * 60)
    
    payload = {
        "session_id": "test-logger-001",
        "use_local_logs": True,
        "send_to_node": False
    }
    
    response = requests.post(f"{BASE_URL}/summarize", json=payload)
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"\nSuccess: {result.get('success')}")
        print(f"Session ID: {result.get('session_id')}")
        print(f"Message Count: {result.get('message_count')}")
        print(f"\n{'='*60}")
        print("SUMMARY:")
        print("="*60)
        print(result.get('summary', 'No summary'))
        print("="*60)
        print(f"\nMetadata: {json.dumps(result.get('metadata'), indent=2)}")
    else:
        print(f"Error: {response.text}")

def test_summarize_with_messages():
    print("\n" + "=" * 60)
    print("TEST: Summarize dengan messages dari payload")
    print("=" * 60)
    
    messages = [
        {
            "direction": "incoming",
            "user_id": "test-user",
            "message": "AC saya mati total",
            "ts": "2025-11-24T07:00:00.000Z"
        },
        {
            "direction": "outgoing",
            "user_id": "test-user",
            "response": "Boleh dicek dulu MCB listriknya kak, apakah sudah ON?",
            "ts": "2025-11-24T07:00:05.000Z"
        },
        {
            "direction": "incoming",
            "user_id": "test-user",
            "message": "Sudah ON tapi tetap mati",
            "ts": "2025-11-24T07:00:10.000Z"
        },
        {
            "direction": "outgoing",
            "user_id": "test-user",
            "response": "Baik kak, sepertinya perlu teknisi. Boleh minta nama lengkapnya?",
            "ts": "2025-11-24T07:00:15.000Z"
        },
        {
            "direction": "incoming",
            "user_id": "test-user",
            "message": "Andi Wijaya",
            "ts": "2025-11-24T07:00:20.000Z"
        },
        {
            "direction": "outgoing",
            "user_id": "test-user",
            "response": "Baik Kak Andi, untuk produknya F57A atau F90A?",
            "ts": "2025-11-24T07:00:25.000Z"
        },
        {
            "direction": "incoming",
            "user_id": "test-user",
            "message": "F57A",
            "ts": "2025-11-24T07:00:30.000Z"
        },
        {
            "direction": "outgoing",
            "user_id": "test-user",
            "response": "Baik, boleh info alamat lengkapnya?",
            "ts": "2025-11-24T07:00:35.000Z"
        },
        {
            "direction": "incoming",
            "user_id": "test-user",
            "message": "Jl. Sudirman No. 123, RT 05/RW 02, Tanah Abang, Jakarta Pusat",
            "ts": "2025-11-24T07:00:40.000Z"
        }
    ]
    
    payload = {
        "session_id": "test-user",
        "messages": messages,
        "use_local_logs": False,
        "send_to_node": False
    }
    
    response = requests.post(f"{BASE_URL}/summarize", json=payload)
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"\nSuccess: {result.get('success')}")
        print(f"Session ID: {result.get('session_id')}")
        print(f"Message Count: {result.get('message_count')}")
        print(f"\n{'='*60}")
        print("SUMMARY:")
        print("="*60)
        print(result.get('summary', 'No summary'))
        print("="*60)
    else:
        print(f"Error: {response.text}")

if __name__ == "__main__":
    print("Testing /summarize endpoint...")
    print(f"Base URL: {BASE_URL}\n")
    
    try:
        health = requests.get(f"{BASE_URL}/health", timeout=3)
        if health.status_code != 200:
            print("Server tidak running! Jalankan dengan: uvicorn src.api:app --host 0.0.0.0 --port 8081")
            exit(1)
    except Exception as e:
        print(f"Server tidak running! Error: {e}")
        print("Jalankan dengan: uvicorn src.api:app --host 0.0.0.0 --port 8081")
        exit(1)
    
    test_summarize_with_local_logs()
    
    test_summarize_with_messages()
    
    print("\n" + "="*60)
    print("Testing selesai!")
    print("="*60)
