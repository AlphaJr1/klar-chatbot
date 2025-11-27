#!/usr/bin/env python3
import sys, os
BASE = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, BASE)

from src.convo.engine import ConversationEngine

# Create fresh engine for each test
def test_pending_reminder():
    engine = ConversationEngine()
    user = "test_pending_fresh"
    
    print("=" * 60)
    print("PENDING REMINDER TEST (Fresh State)")
    print("=" * 60)
    
    # Set pending state
    engine.memstore.set_flag(user, "sop_pending", True)
    
    # Set identity using proper methods
    engine.memstore.set_name(user, "Budi")
    engine.memstore.set_product(user, "EAC F57A")
    engine.memstore.update(user, {"address": "Jakarta", "gender": "male"})
    
    # Mark data collection as complete
    engine.memstore.update(user, {"data_collection_complete": True})
    
    print("\n1. First message after pending complete (should send closing)")
    result = engine.handle(user, "ok")
    print(f"   User: 'ok'")
    print(f"   Bot: '{result['bubbles'][0]['text']}'")
    closing_sent = engine.memstore.get_flag(user, "pending_closing_sent")
    print(f"   pending_closing_sent: {closing_sent}")
    
    if "Data" in result['bubbles'][0]['text'] and "sudah kami terima" in result['bubbles'][0]['text']:
        print("   ✅ Closing message sent")
        if closing_sent:
            print("   ✅ Flag set correctly")
    else:
        print("   ❌ Should send closing message first")
    
    print("\n2. User sends 'Baik kak' (should be minimal)")
    result = engine.handle(user, "Baik kak")
    response = result['bubbles'][0]['text']
    print(f"   Bot: '{response}'")
    
    if response in ["🙏", "Siap kak 👍", "Terima kasih kak 😊"]:
        print("   ✅ CORRECT: Minimal response, no spam")
    elif "Data" in response:
        print("   ❌ BUG: Repeating closing message")
    
    print("\n3. User sends '👍'")
    result = engine.handle(user, "👍")
    response = result['bubbles'][0]['text']
    print(f"   Bot: '{response}'")
    
    if response in ["🙏", "Siap kak 👍", "Terima kasih kak 😊"]:
        print("   ✅ CORRECT: Minimal response")
    elif "Data" in response:
        print("   ❌ BUG: Repeating closing message")
    
    print("\n4. User sends '🙏'")
    result = engine.handle(user, "🙏")
    response = result['bubbles'][0]['text']
    print(f"   Bot: '{response}'")
    
    if response in ["🙏", "Siap kak 👍", "Terima kasih kak 😊"]:
        print("   ✅ CORRECT: Minimal response")
    elif "Data" in response:
        print("   ❌ BUG: Repeating closing message")
    
    print("\n" + "=" * 60)
    print("✅ TEST COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    test_pending_reminder()
