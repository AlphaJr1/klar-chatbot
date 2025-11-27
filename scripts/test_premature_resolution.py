#!/usr/bin/env python3
import sys, os
BASE = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, BASE)

from src.convo.engine import ConversationEngine

def test_premature_resolution():
    print("=" * 60)
    print("TEST PREMATURE RESOLUTION FIX")
    print("=" * 60)
    
    print("\n🧪 Test Case 1: 'sudah dicoba semua' should NOT resolve\n")
    
    engine = ConversationEngine()
    user = "test_resolve_case1"
    
    messages = [
        ("EAC saya mati", "Initial complaint"),
        ("sudah rapat", "Answer: cover tight"),
        ("sudah dicoba semua", "Ambiguous - should ask for clarification"),
    ]
    
    for i, (msg, desc) in enumerate(messages, 1):
        result = engine.handle(user, msg)
        response = result.get("bubbles", [{}])[0].get("text", "")
        status = result.get("status", "unknown")
        resolved = engine.memstore.get_flag(user, "sop_resolved")
        
        print(f"{i}. User: '{msg}'")
        print(f"   ({desc})")
        print(f"   Bot: '{response[:80]}'")
        print(f"   Status: {status}, Resolved: {resolved}")
        
        if i == 3:
            if status != "resolved" and not resolved:
                print("   ✅ CORRECT: Not resolved, asking for clarification")
            else:
                print("   ❌ BUG: Should not resolve yet!")
        print()
    
    print("=" * 60)
    print("\n🧪 Test Case 2: Explicit resolution should work\n")
    
    engine2 = ConversationEngine()
    user2 = "test_resolve_case2"
    
    messages2 = [
        ("EAC saya mati", "Initial complaint"),
        ("sudah rapat", "Answer"),
        ("alat sudah menyala kembali kak", "Explicit resolution"),
    ]
    
    for i, (msg, desc) in enumerate(messages2, 1):
        result = engine2.handle(user2, msg)
        response = result.get("bubbles", [{}])[0].get("text", "")
        status = result.get("status", "unknown")
        resolved = engine2.memstore.get_flag(user2, "sop_resolved")
        
        print(f"{i}. User: '{msg}'")
        print(f"   ({desc})")
        print(f"   Bot: '{response[:80]}'")
        print(f"   Status: {status}, Resolved: {resolved}")
        
        if i == 3:
            if status == "resolved" and resolved:
                print("   ✅ CORRECT: Resolved after explicit confirmation")
            else:
                print("   ❌ Should resolve after explicit confirmation")
        print()
    
    print("=" * 60)
    print("\n🧪 Test Case 3: 'masih tidak nyala' should NOT resolve\n")
    
    engine3 = ConversationEngine()
    user3 = "test_resolve_case3"
    
    messages3 = [
        ("EAC saya mati", "Initial"),
        ("sudah rapat", "Answer"),
        ("Apakah sudah berfungsi?", "Bot asks"),  # Simulate bot asking
        ("sudah saya coba namun masih tetap tidak nyala", "Should NOT resolve"),
    ]
    
    # Skip message 3 (bot's question)
    engine3.handle(user3, messages3[0][0])
    engine3.handle(user3, messages3[1][0])
    
    result = engine3.handle(user3, messages3[3][0])
    response = result.get("bubbles", [{}])[0].get("text", "")
    status = result.get("status", "unknown")
    resolved = engine3.memstore.get_flag(user3, "sop_resolved")
    
    print(f"User: '{messages3[3][0]}'")
    print(f"Bot: '{response[:80]}'")
    print(f"Status: {status}, Resolved: {resolved}")
    
    if status != "resolved" and not resolved:
        print("✅ CORRECT: Not resolved when user says 'masih tidak nyala'")
    else:
        print("❌ BUG: Should not resolve!")
    
    print("\n" + "=" * 60)
    print("✅ PREMATURE RESOLUTION TEST COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    test_premature_resolution()
