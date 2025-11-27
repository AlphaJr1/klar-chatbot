#!/usr/bin/env python3
import sys
import os

BASE = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, BASE)

from src.convo.engine import ConversationEngine

def test_spam_filter():
    engine = ConversationEngine()
    test_user = "test_spam_filter_001"
    
    print("=" * 60)
    print("TEST SPAM/PROFANITY FILTER")
    print("=" * 60)
    
    test_cases = [
        ("Anjg", "profanity"),
        ("Al", "spam"),
        ("Ohokkk", "spam"),
        ("Affh iyh", "spam"),
        ("Ga boleh", "normal"),
        ("Maksa", "spam"),
        ("Tll", "spam"),
        ("GA", "spam"),
        ("ENGGAK COK", "profanity"),
        ("Gaa", "spam"),
        ("Jadi gini", "normal"),
        ("Halo", "normal"),
        ("EAC saya mati", "normal"),
    ]
    
    print("\n🧪 Testing spam/profanity detection:\n")
    
    for msg, expected_type in test_cases:
        result = engine.handle(test_user, msg)
        response = result.get("bubbles", [{}])[0].get("text", "")
        
        is_filtered = response == "🙏" or "keluhan EAC" in response
        
        status = "✅" if (
            (expected_type in ["spam", "profanity"] and is_filtered) or
            (expected_type == "normal" and not is_filtered)
        ) else "❌"
        
        print(f"{status} '{msg}' ({expected_type})")
        print(f"   Response: {response[:50]}...")
        print()
    
    print("\n🧪 Testing spam counter (should trigger after 3 spam):\n")
    
    engine.memstore.clear_flag(test_user, "spam_count")
    
    for i in range(5):
        result = engine.handle(test_user, "Al")
        response = result.get("bubbles", [{}])[0].get("text", "")
        spam_count = engine.memstore.get_flag(test_user, "spam_count") or 0
        
        print(f"Spam #{i+1}: count={spam_count}, response='{response}'")
        
        if i == 2:
            if "keluhan EAC" in response:
                print("   ✅ Threshold reached, bot gives helpful message")
            else:
                print("   ❌ Should trigger helpful message at 3rd spam")
    
    print("\n🧪 Testing normal message resets spam counter:\n")
    
    engine.memstore.set_flag(test_user, "spam_count", 2)
    result = engine.handle(test_user, "EAC saya mati")
    spam_count = engine.memstore.get_flag(test_user, "spam_count") or 0
    
    if spam_count == 0:
        print("✅ Spam counter reset after normal message")
    else:
        print(f"❌ Spam counter should be 0, got {spam_count}")
    
    print("\n" + "=" * 60)
    print("✅ SPAM FILTER TEST COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    test_spam_filter()
