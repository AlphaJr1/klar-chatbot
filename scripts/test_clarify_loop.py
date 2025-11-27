#!/usr/bin/env python3
import sys
import os

BASE = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, BASE)

from src.convo.engine import ConversationEngine

def test_clarification_loop():
    engine = ConversationEngine()
    test_user = "test_clarify_loop_001"
    
    print("=" * 60)
    print("TEST CLARIFICATION LOOP LIMITER")
    print("=" * 60)
    
    print("\n🧪 Test Case 1: Unclear answers should trigger escalation after 3x\n")
    
    result = engine.handle(test_user, "EAC saya berbunyi")
    print(f"1. User: 'EAC saya berbunyi'")
    print(f"   Bot: '{result['bubbles'][0]['text'][:60]}...'")
    
    for i in range(5):
        result = engine.handle(test_user, "bunyi aneh gitu")
        response = result.get("bubbles", [{}])[0].get("text", "")
        clarify_count = engine.memstore.get_flag(test_user, "bunyi_clarify_count") or 0
        status = result.get("status", "unknown")
        
        print(f"\n{i+2}. User: 'bunyi aneh gitu' (unclear answer #{i+1})")
        print(f"   Bot: '{response[:80]}...'")
        print(f"   Clarify count: {clarify_count}, Status: {status}")
        
        if i == 2:
            if "teknisi" in response.lower() and status == "open":
                print("   ✅ Auto-escalated to pending after 3 clarifications!")
            else:
                print("   ❌ Should auto-escalate after 3 clarifications")
        
        if i >= 3 and "teknisi" not in response.lower():
            print("   ❌ Should have escalated already")
    
    print("\n" + "=" * 60)
    
    print("\n🧪 Test Case 2: Clear answer should reset counter\n")
    
    engine.memstore.clear_flag(test_user, "bunyi_clarify_count")
    engine.memstore.clear_flag(test_user, "sop_pending")
    engine.memstore.clear_flag(test_user, "active_intent")
    
    result = engine.handle(test_user, "EAC saya berbunyi")
    print(f"1. User: 'EAC saya berbunyi'")
    print(f"   Bot: '{result['bubbles'][0]['text'][:60]}...'")
    
    result = engine.handle(test_user, "bunyi aneh")
    clarify_count = engine.memstore.get_flag(test_user, "bunyi_clarify_count") or 0
    print(f"\n2. User: 'bunyi aneh' (unclear #1)")
    print(f"   Bot: '{result['bubbles'][0]['text'][:60]}...'")
    print(f"   Clarify count: {clarify_count}")
    
    result = engine.handle(test_user, "bunyi aneh lagi")
    clarify_count = engine.memstore.get_flag(test_user, "bunyi_clarify_count") or 0
    print(f"\n3. User: 'bunyi aneh lagi' (unclear #2)")
    print(f"   Bot: '{result['bubbles'][0]['text'][:60]}...'")
    print(f"   Clarify count: {clarify_count}")
    
    result = engine.handle(test_user, "sering kak")
    clarify_count = engine.memstore.get_flag(test_user, "bunyi_clarify_count") or 0
    response = result.get("bubbles", [{}])[0].get("text", "")
    print(f"\n4. User: 'sering kak' (CLEAR answer)")
    print(f"   Bot: '{response[:80]}...'")
    print(f"   Clarify count: {clarify_count}")
    
    if clarify_count == 0:
        print("   ✅ Counter reset after clear answer!")
    else:
        print(f"   ❌ Counter should be 0, got {clarify_count}")
    
    print("\n" + "=" * 60)
    
    print("\n🧪 Test Case 3: Real case from chat log (6282216860317)\n")
    
    test_user_real = "6282216860317_replay"
    
    messages = [
        ("Kak EAC saya kok muncul bunyi terus yaa?", "Initial complaint"),
        ("Iya, cukup mengganggu", "Unclear #1"),
        ("Waktu dinyalakan suka ada bunyi kretek kretek gitu", "Unclear #2"),
        ("Yaaa gitu, dinyalakan sebentar langsung ada bunyi2 nya, terus tu lumayan sering juga", "Unclear #3"),
        ("Bunyi kretek kretek", "Should escalate here"),
    ]
    
    for i, (msg, desc) in enumerate(messages, 1):
        result = engine.handle(test_user_real, msg)
        response = result.get("bubbles", [{}])[0].get("text", "")
        clarify_count = engine.memstore.get_flag(test_user_real, "bunyi_clarify_count") or 0
        status = result.get("status", "unknown")
        
        print(f"\n{i}. User: '{msg[:50]}...'")
        print(f"   ({desc})")
        print(f"   Bot: '{response[:80]}...'")
        print(f"   Clarify count: {clarify_count}, Status: {status}")
        
        if i == 4 and "teknisi" in response.lower():
            print("   ✅ Auto-escalated instead of asking clarification again!")
    
    print("\n" + "=" * 60)
    print("✅ CLARIFICATION LOOP LIMITER TEST COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    test_clarification_loop()
