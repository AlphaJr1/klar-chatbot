import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.convo.engine import ConversationEngine

def test_resolution_requires_explicit_confirmation():
    print("=" * 70)
    print("TEST: Resolution Harus Dengan Konfirmasi Eksplisit")
    print("=" * 70)
    
    engine = ConversationEngine()
    user_id = "test_explicit_resolution"
    
    engine.memstore.clear(user_id)
    
    print("\n[SCENARIO 1] User komplain EAC mati")
    print("-" * 70)
    
    r1 = engine.handle(user_id, "EAC saya mati kak")
    print(f"User: EAC saya mati kak")
    print(f"Bot: {r1['bubbles'][0]['text'][:100]}...")
    
    print("\n[SCENARIO 2] User jawab 'sudah rapat'")
    print("-" * 70)
    
    r2 = engine.handle(user_id, "sudah rapat kak")
    print(f"User: sudah rapat kak")
    print(f"Bot: {r2['bubbles'][0]['text'][:100]}...")
    
    print("\n[SCENARIO 3] User jawab 'sudah LOW'")
    print("-" * 70)
    
    r3 = engine.handle(user_id, "sudah saya tekan LOW kak")
    print(f"User: sudah saya tekan LOW kak")
    print(f"Bot: {r3['bubbles'][0]['text'][:100]}...")
    
    print("\n[SCENARIO 4] User jawab 'iya' (TIDAK EKSPLISIT)")
    print("-" * 70)
    
    r4 = engine.handle(user_id, "iya")
    print(f"User: iya")
    print(f"Bot: {r4['bubbles'][0]['text']}")
    print(f"Status: {r4.get('status', 'N/A')}")
    
    if r4.get('status') == 'resolved':
        print("❌ GAGAL: Sistem resolve hanya dengan jawaban 'iya'")
        return False
    else:
        print("✅ BERHASIL: Sistem TIDAK resolve dengan jawaban 'iya' saja")
    
    print("\n[SCENARIO 5] User jawab 'sudah berfungsi normal' (EKSPLISIT)")
    print("-" * 70)
    
    r5 = engine.handle(user_id, "sudah berfungsi normal kak")
    print(f"User: sudah berfungsi normal kak")
    print(f"Bot: {r5['bubbles'][0]['text']}")
    print(f"Status: {r5.get('status', 'N/A')}")
    
    if r5.get('status') == 'resolved':
        print("✅ BERHASIL: Sistem resolve dengan konfirmasi eksplisit")
    else:
        print("❌ GAGAL: Sistem TIDAK resolve meskipun ada konfirmasi eksplisit")
        return False
    
    engine.memstore.clear(user_id)
    
    print("\n" + "=" * 70)
    print("TEST SELESAI - SEMUA PASSED")
    print("=" * 70)
    return True

if __name__ == "__main__":
    success = test_resolution_requires_explicit_confirmation()
    sys.exit(0 if success else 1)
