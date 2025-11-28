import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.convo.engine import ConversationEngine

def test_conversation_reset():
    print("=" * 70)
    print("TEST: Conversation Reset - New Session Detection")
    print("=" * 70)
    
    engine = ConversationEngine()
    user_id = "test_conversation_reset"
    
    engine.memstore.clear(user_id)
    
    print("\n[SCENARIO 1] User komplain bunyi sering → pending")
    print("-" * 70)
    
    r1 = engine.handle(user_id, "EAC bunyi terus kak, sering banget")
    print(f"User: EAC bunyi terus kak, sering banget")
    print(f"Bot: {r1['bubbles'][0]['text'][:80]}...")
    print(f"Pending: {engine.memstore.get_flag(user_id, 'sop_pending')}")
    
    print("\n[SCENARIO 2] Bot minta nama")
    print("-" * 70)
    
    r2 = engine.handle(user_id, "bunyi kretek")
    print(f"User: bunyi kretek")
    print(f"Bot: {r2['bubbles'][0]['text']}")
    
    print("\n[SCENARIO 3] User say 'Halo' saat pending (SHOULD RESET)")
    print("-" * 70)
    
    r3 = engine.handle(user_id, "Halo")
    print(f"User: Halo")
    print(f"Bot: {r3['bubbles'][0]['text']}")
    print(f"Pending after reset: {engine.memstore.get_flag(user_id, 'sop_pending')}")
    print(f"Active intent after reset: {engine.memstore.get_flag(user_id, 'active_intent')}")
    
    if engine.memstore.get_flag(user_id, 'sop_pending') is None:
        print("✅ BERHASIL: Pending state direset saat new session")
    else:
        print("❌ GAGAL: Pending state tidak direset")
        return False
    
    engine.memstore.clear(user_id)
    
    print("\n[SCENARIO 4] User komplain bunyi → pending → follow-up question")
    print("-" * 70)
    
    r4a = engine.handle(user_id, "EAC saya bunyi aneh kak")
    print(f"User: EAC saya bunyi aneh kak")
    print(f"Bot: {r4a['bubbles'][0]['text'][:60]}...")
    
    r4b = engine.handle(user_id, "bunyi terus")
    print(f"User: bunyi terus")
    
    # Trigger pending
    r4c = engine.handle(user_id, "sering")
    print(f"Bot should trigger pending...")
    print(f"Pending: {engine.memstore.get_flag(user_id, 'sop_pending')}")
    
    r4d = engine.handle(user_id, "nama saya Budi")
    print(f"\nUser: nama saya Budi")
    
    r4e = engine.handle(user_id, "Kapan teknisi datang?")
    print(f"User: Kapan teknisi datang? (FOLLOW-UP)")
    print(f"Bot: {r4e['bubbles'][0]['text']}")
    print(f"Pending should stay: {engine.memstore.get_flag(user_id, 'sop_pending')}")
    
    if engine.memstore.get_flag(user_id, 'sop_pending'):
        print("✅ BERHASIL: Pending state tetap saat follow-up")
    else:
        print("❌ GAGAL: Pending state hilang saat follow-up")
        return False
    
    engine.memstore.clear(user_id)
    
    print("\n" + "=" * 70)
    print("TEST SELESAI")
    print("=" * 70)
    return True

if __name__ == "__main__":
    success = test_conversation_reset()
    sys.exit(0 if success else 1)
