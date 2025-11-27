#!/usr/bin/env python3
import sys, os
BASE = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, BASE)

from src.convo.engine import ConversationEngine

def test_intent_detection():
    print("=" * 60)
    print("TEST INTENT DETECTION IMPROVEMENT")
    print("=" * 60)
    
    engine = ConversationEngine()
    
    test_cases = [
        # EAC cases
        ("EAC saya mati", "mati", "Standard EAC mati"),
        ("EAC tidak menyala", "mati", "EAC tidak menyala"),
        ("EAC saya berbunyi aneh", "bunyi", "EAC bunyi"),
        ("EAC bau tidak sedap", "bau", "EAC bau"),
        
        # Water heater cases (should map to "mati" for "tidak panas")
        ("water heater ku tidak panas", "mati", "Water heater tidak panas"),
        ("pemanas air tidak panas", "mati", "Pemanas air tidak panas"),
        ("water heater mati", "mati", "Water heater mati"),
        
        # Variations
        ("alat tidak hidup", "mati", "Tidak hidup"),
        ("ada bunyi kretek-kretek", "bunyi", "Bunyi kretek"),
        ("bau menyengat dari alat", "bau", "Bau menyengat"),
    ]
    
    print("\n🧪 Testing intent detection:\n")
    
    passed = 0
    failed = 0
    
    for msg, expected_intent, desc in test_cases:
        user = f"test_intent_{passed + failed}"
        
        result = engine.handle(user, msg)
        detected_intent = engine.memstore.get_flag(user, "active_intent")
        response = result.get("bubbles", [{}])[0].get("text", "")
        
        if detected_intent == expected_intent:
            print(f"✅ '{desc}'")
            print(f"   Message: '{msg}'")
            print(f"   Detected: {detected_intent} (expected: {expected_intent})")
            passed += 1
        else:
            print(f"❌ '{desc}'")
            print(f"   Message: '{msg}'")
            print(f"   Detected: {detected_intent} (expected: {expected_intent})")
            print(f"   Response: '{response[:80]}'")
            failed += 1
        print()
    
    print("=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed out of {len(test_cases)} tests")
    print("=" * 60)
    
    if failed == 0:
        print("\n🎉 All tests passed!")
    else:
        print(f"\n⚠️  {failed} test(s) failed - intent detection needs improvement")

if __name__ == "__main__":
    test_intent_detection()
