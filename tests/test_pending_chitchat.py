import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.convo.engine import ConversationEngine

def test_pending_chitchat_handling():
    print("=" * 70)
    print("TEST: Pending State - Chitchat Handling")
    print("=" * 70)
    
    engine = ConversationEngine()
    user_id = "test_pending_chitchat"
    
    engine.memstore.clear(user_id)
    
    print("\n[SCENARIO 1] User komplain bunyi sering")
    print("-" * 70)
    
    r1 = engine.handle(user_id, "EAC saya bunyi kretek kretek terus kak, sering banget")
    print(f"User: EAC saya bunyi kretek kretek terus kak, sering banget")
    print(f"Bot: {r1['bubbles'][0]['text'][:100]}...")
    print(f"Pending: {engine.memstore.get_flag(user_id, 'sop_pending')}")
    
    print("\n[SCENARIO 2] Bot minta nama")
    print("-" * 70)
    
    r2 = engine.handle(user_id, "bunyi kretek kretek")
    print(f"User: bunyi kretek kretek")
    print(f"Bot: {r2['bubbles'][0]['text']}")
    
    print("\n[SCENARIO 3] User chitchat 'Iya, cukup mengganggu' (HARUS ACKNOWLEDGE SAJA)")
    print("-" * 70)
    
    r3 = engine.handle(user_id, "Iya, cukup mengganggu")
    print(f"User: Iya, cukup mengganggu")
    print(f"Bot: {r3['bubbles'][0]['text']}")
    
    if "nama" in r3['bubbles'][0]['text'].lower() or "data" in r3['bubbles'][0]['text'].lower():
        print("❌ GAGAL: Bot masih minta data saat user chitchat")
        return False
    else:
        print("✅ BERHASIL: Bot hanya acknowledge tanpa minta data")
    
    print("\n[SCENARIO 4] User chitchat lagi 'Waktu dinyalakan suka ada bunyi' (HARUS ACKNOWLEDGE SAJA)")
    print("-" * 70)
    
    r4 = engine.handle(user_id, "Waktu dinyalakan suka ada bunyi kretek kretek gitu")
    print(f"User: Waktu dinyalakan suka ada bunyi kretek kretek gitu")
    print(f"Bot: {r4['bubbles'][0]['text']}")
    
    if "nama" in r4['bubbles'][0]['text'].lower() or "data" in r4['bubbles'][0]['text'].lower():
        print("❌ GAGAL: Bot masih minta data saat user chitchat")
        return False
    else:
        print("✅ BERHASIL: Bot hanya acknowledge tanpa minta data")
    
    print("\n[SCENARIO 5] User kasih nama 'Budi'")
    print("-" * 70)
    
    r5 = engine.handle(user_id, "Budi")
    print(f"User: Budi")
    print(f"Bot: {r5['bubbles'][0]['text']}")
    
    if "produk" in r5['bubbles'][0]['text'].lower() or "alamat" in r5['bubbles'][0]['text'].lower():
        print("✅ BERHASIL: Bot lanjut ke field berikutnya")
    else:
        print("⚠️  Bot response: {r5['bubbles'][0]['text']}")
    
    engine.memstore.clear(user_id)
    
    print("\n" + "=" * 70)
    print("TEST SELESAI")
    print("=" * 70)
    return True

if __name__ == "__main__":
    success = test_pending_chitchat_handling()
    sys.exit(0 if success else 1)
