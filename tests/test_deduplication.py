#!/usr/bin/env python3
import requests
import json
import time
from datetime import datetime

API_URL = "http://localhost:8080"

def test_single_message():
    print("\n" + "="*60)
    print("TEST 1: Single Message (No Duplication Expected)")
    print("="*60)
    
    payload = {
        "user_id": "test-dedupe-001",
        "text": "halo, alat EAC saya mati"
    }
    
    print(f"Sending message: {payload['text']}")
    start_time = time.time()
    
    response = requests.post(f"{API_URL}/chat", json=payload)
    elapsed = (time.time() - start_time) * 1000
    
    print(f"✓ Response received in {elapsed:.2f}ms")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Bubbles: {len(data.get('bubbles', []))}")
        for bubble in data.get('bubbles', []):
            print(f"  → {bubble.get('text', '')[:80]}...")
        print(f"✓ Status: {data.get('status', 'unknown')}")
    else:
        print(f"✗ Error: {response.text}")
    
    print("\nCHECK: Lihat log Node.js, harus ada HANYA 1x [WEBHOOK-RECV]")
    print("="*60)

def test_rapid_messages():
    print("\n" + "="*60)
    print("TEST 2: Rapid Messages (Each Should Have Unique ID)")
    print("="*60)
    
    user_id = "test-dedupe-002"
    messages = [
        "alat saya mati",
        "bunyi berisik sekali",
        "bau tidak sedap"
    ]
    
    for i, msg in enumerate(messages, 1):
        print(f"\n[{i}/{len(messages)}] Sending: {msg}")
        
        payload = {
            "user_id": user_id,
            "text": msg
        }
        
        start_time = time.time()
        response = requests.post(f"{API_URL}/chat", json=payload)
        elapsed = (time.time() - start_time) * 1000
        
        print(f"  ✓ Response in {elapsed:.2f}ms, Status: {response.status_code}")
        
        time.sleep(0.3)
    
    print("\nCHECK: Lihat log Node.js, harus ada 3x [WEBHOOK-RECV] dengan request_id berbeda")
    print("="*60)

def test_duplicate_detection():
    print("\n" + "="*60)
    print("TEST 3: Manual Duplicate Detection Test")
    print("="*60)
    print("INFO: Untuk test ini, jalankan 2x curl command yang sama:")
    print()
    print("curl -X POST http://localhost:8080/chat \\")
    print("  -H 'Content-Type: application/json' \\")
    print("  -d '{\"user_id\": \"test-dedupe-003\", \"text\": \"halo\"}'")
    print()
    print("Expected: Node.js harus log [DEDUPE] di request kedua")
    print("="*60)

def test_webhook_payload_format():
    print("\n" + "="*60)
    print("TEST 4: Webhook Payload Format Validation")
    print("="*60)
    
    payload = {
        "user_id": "test-dedupe-004",
        "text": "test payload format"
    }
    
    response = requests.post(f"{API_URL}/chat", json=payload)
    
    print("Expected payload yang dikirim ke webhook harus punya:")
    print("  ✓ request_id (UUID)")
    print("  ✓ user_id")
    print("  ✓ text (original message)")
    print("  ✓ reply (bot response)")
    print("  ✓ status (open/pending/resolved)")
    print("  ✓ timestamp (ISO format)")
    print()
    print("CHECK: Lihat log FastAPI untuk konfirmasi format")
    print("="*60)

def check_server_health():
    print("\n" + "="*60)
    print("Checking Server Health...")
    print("="*60)
    
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✓ FastAPI server is running")
            print(f"  - Version: {data.get('version', 'unknown')}")
            print(f"  - Engine ready: {data.get('engine_ready', False)}")
            return True
        else:
            print(f"✗ Server returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("✗ Cannot connect to server. Is it running?")
        print("  Run: uvicorn src.api:app --host 0.0.0.0 --port 8080")
        return False

def main():
    print("\n" + "="*60)
    print("DEDUPLICATION TEST SUITE")
    print("="*60)
    print(f"Target: {API_URL}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    if not check_server_health():
        print("\n✗ Server health check failed. Exiting.")
        return
    
    print("\nPastikan Node.js server sudah diupdate dengan deduplication logic!")
    print("Lihat: .agent/guides/nodejs_deduplication_guide.js")
    
    input("\nPress Enter to start tests...")
    
    # Run tests
    test_single_message()
    time.sleep(1)
    
    test_rapid_messages()
    time.sleep(1)
    
    test_webhook_payload_format()
    time.sleep(1)
    
    test_duplicate_detection()
    
    print("\n" + "="*60)
    print("TESTING COMPLETE")
    print("="*60)
    print("\nNext steps:")
    print("1. Check FastAPI logs untuk [BRIDGE] messages")
    print("2. Check Node.js logs untuk [WEBHOOK-RECV] dan [DEDUPE]")
    print("3. Verify tidak ada pesan ganda terkirim ke user")
    print("="*60)

if __name__ == "__main__":
    main()
