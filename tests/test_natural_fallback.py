#!/usr/bin/env python3
import sys
import os

BASE = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, os.path.join(BASE, "src"))

from convo.engine import ConversationEngine

def test_fallback_responses():
    engine = ConversationEngine()
    test_user = "test_fallback_001"
    
    print("🧪 Testing Natural Fallback Responses\n")
    
    test_cases = [
        ("halo", "Greeting tanpa keluhan"),
        ("gimana nih", "Chitchat tidak jelas"),
        ("ac saya", "Keluhan tidak lengkap"),
        ("rusak", "Keluhan sangat singkat"),
        ("panas banget ya", "Chitchat cuaca"),
    ]
    
    for i, (msg, desc) in enumerate(test_cases, 1):
        print(f"\n{'='*60}")
        print(f"Test {i}: {desc}")
        print(f"User: {msg}")
        print(f"{'='*60}")
        
        result = engine.handle(test_user, msg)
        
        for bubble in result.get("bubbles", []):
            print(f"Bot: {bubble.get('text')}")
        
        engine.memstore.clear(test_user)
    
    print(f"\n{'='*60}")
    print("✅ Test selesai")

if __name__ == "__main__":
    test_fallback_responses()
