#!/usr/bin/env python3
import sys, os
BASE = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, BASE)

from src.convo.engine import ConversationEngine

def test_pending_reminder_spam():
    print("=" * 60)
    print("TEST PENDING REMINDER SPAM FIX")
    print("=" * 60)
    
    engine = ConversationEngine()
    user = "test_pending_spam"
    
    print("\n🧪 Simulate pending flow with data collection\n")
    
    # Trigger pending
    engine.handle(user, "EAC saya mati")
    engine.handle(user, "sudah dicoba semua")
    engine.handle(user, "sudah dicoba semua")
    result = engine.handle(user, "sudah dicoba semua")
    
    print(f"1. After 3x unclear → Auto-escalate to pending")
    print(f"   Bot: '{result['bubbles'][0]['text'][:60]}'")
    print(f"   Status: {result.get('status')}")
    
    # Provide data
    print(f"\n2. Provide name")
    result = engine.handle(user, "Budi")
    print(f"   User: 'Budi'")
    print(f"   Bot: '{result['bubbles'][0]['text'][:60]}'")
    
    print(f"\n3. Provide product")
    result = engine.handle(user, "EAC 123")
    print(f"   User: 'EAC 123'")
    print(f"   Bot: '{result['bubbles'][0]['text'][:60]}'")
    
    print(f"\n4. Provide address")
    result = engine.handle(user, "Jakarta Selatan")
    print(f"   User: 'Jakarta Selatan'")
    print(f"   Bot: '{result['bubbles'][0]['text']}'")
    print(f"   Status: {result.get('status')}")
    
    pending_sent = engine.memstore.get_flag(user, "pending_closing_sent")
    print(f"   pending_closing_sent flag: {pending_sent}")
    
    if "Data" in result['bubbles'][0]['text'] and "sudah kami terima" in result['bubbles'][0]['text']:
        print("   ✅ Closing message sent")
    
    # Now test simple acknowledgments
    print(f"\n5. User sends simple acknowledgment: 'Baik kak'")
    result = engine.handle(user, "Baik kak")
    response = result['bubbles'][0]['text']
    print(f"   Bot: '{response}'")
    
    if response in ["🙏", "Siap kak 👍", "Terima kasih kak 😊"]:
        print("   ✅ CORRECT: Minimal response, no reminder spam")
    elif "Data" in response and "sudah kami terima" in response:
        print("   ❌ BUG: Repeating closing message!")
    
    print(f"\n6. User sends emoji: '👍'")
    result = engine.handle(user, "👍")
    response = result['bubbles'][0]['text']
    print(f"   Bot: '{response}'")
    
    if response in ["🙏", "Siap kak 👍", "Terima kasih kak 😊"]:
        print("   ✅ CORRECT: Minimal response")
    elif "Data" in response:
        print("   ❌ BUG: Repeating closing message!")
    
    print(f"\n7. User sends another emoji: '🙏'")
    result = engine.handle(user, "🙏")
    response = result['bubbles'][0]['text']
    print(f"   Bot: '{response}'")
    
    if response in ["🙏", "Siap kak 👍", "Terima kasih kak 😊"]:
        print("   ✅ CORRECT: Minimal response")
    elif "Data" in response:
        print("   ❌ BUG: Repeating closing message!")
    
    print("\n" + "=" * 60)
    print("✅ PENDING REMINDER SPAM TEST COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    test_pending_reminder_spam()
