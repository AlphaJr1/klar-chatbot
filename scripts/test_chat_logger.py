#!/usr/bin/env python3

import sys
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, "src"))

from convo.engine import ConversationEngine

def test_chat_logging():
    print("Testing Chat Logger...")
    print("=" * 60)
    
    engine = ConversationEngine()
    test_user = "test-logger-001"
    
    # Test 1: Simple complaint
    print("\n1. Testing incoming complaint...")
    result = engine.handle(test_user, "AC saya mati")
    print(f"   Response: {result['bubbles'][0]['text'][:50]}...")
    
    # Test 2: Troubleshooting answer
    print("\n2. Testing troubleshooting answer...")
    result = engine.handle(test_user, "tidak menyala")
    print(f"   Response: {result['bubbles'][0]['text'][:50]}...")
    
    # Test 3: Data collection - name
    print("\n3. Testing data collection...")
    result = engine.handle(test_user, "Budi")
    print(f"   Response: {result['bubbles'][0]['text'][:50]}...")
    
    # Test 4: Product
    print("\n4. Testing product input...")
    result = engine.handle(test_user, "F57A")
    print(f"   Response: {result['bubbles'][0]['text'][:50]}...")
    
    # Test 5: Address
    print("\n5. Testing address input...")
    result = engine.handle(test_user, "Jl. Sudirman 123, Jakarta Selatan")
    print(f"   Response: {result['bubbles'][0]['text'][:50]}...")
    print(f"   Status: {result.get('status', 'unknown')}")
    
    print("\n" + "=" * 60)
    print("✅ Test completed!")
    print("\nCek log file di: data/storage/logs/chat-*.jsonl")
    print("Jalankan: python scripts/view_chat_logs.py --user " + test_user[-4:])

if __name__ == "__main__":
    test_chat_logging()
