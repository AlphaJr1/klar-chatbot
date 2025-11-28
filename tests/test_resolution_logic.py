import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.convo.engine import ConversationEngine
from src.convo.memory_store import MemoryStore

def test_resolution_logic():
    print("=" * 60)
    print("TEST: Resolution Logic - Explicit Confirmation Required")
    print("=" * 60)
    
    engine = ConversationEngine()
    memstore = MemoryStore()
    user_id = "test_resolution_user"
    
    memstore.clear(user_id)
    
    print("\n[SCENARIO 1] User jawab 'iya' tanpa konfirmasi eksplisit")
    print("-" * 60)
    
    memstore.set_flag(user_id, "active_intent", "eac_tidak_menyala")
    memstore.set_flag(user_id, "eac_tidak_menyala_active_step", "check_mcb")
    memstore.set_flag(user_id, "check_mcb_waiting_confirm", True)
    memstore.set_flag(user_id, "check_mcb_confirm_data", {
        "resolve_if_yes": True,
        "next_if_no": None,
        "pending_if_no": True
    })
    
    memstore.append_history(user_id, "bot", "Apakah alatnya sudah berfungsi normal kak?")
    
    response = engine.handle(user_id, "iya")
    
    print(f"User: iya")
    print(f"Bot: {response['bubbles'][0]['text']}")
    print(f"Status: {response.get('status', 'N/A')}")
    print(f"Next: {response.get('next', 'N/A')}")
    
    if response.get('status') == 'resolved':
        print("❌ GAGAL: Sistem langsung resolve tanpa konfirmasi eksplisit")
    else:
        print("✅ BERHASIL: Sistem meminta konfirmasi eksplisit")
    
    print("\n[SCENARIO 2] User jawab 'sudah berfungsi normal' (konfirmasi eksplisit)")
    print("-" * 60)
    
    memstore.clear(user_id)
    memstore.set_flag(user_id, "active_intent", "eac_tidak_menyala")
    memstore.set_flag(user_id, "eac_tidak_menyala_active_step", "check_mcb")
    memstore.set_flag(user_id, "check_mcb_waiting_confirm", True)
    memstore.set_flag(user_id, "check_mcb_confirm_data", {
        "resolve_if_yes": True,
        "next_if_no": None,
        "pending_if_no": True
    })
    
    memstore.append_history(user_id, "bot", "Apakah alatnya sudah berfungsi normal kak?")
    
    response = engine.handle(user_id, "sudah berfungsi normal kak")
    
    print(f"User: sudah berfungsi normal kak")
    print(f"Bot: {response['bubbles'][0]['text']}")
    print(f"Status: {response.get('status', 'N/A')}")
    print(f"Next: {response.get('next', 'N/A')}")
    
    if response.get('status') == 'resolved':
        print("✅ BERHASIL: Sistem resolve karena ada konfirmasi eksplisit")
    else:
        print("❌ GAGAL: Sistem tidak resolve meskipun ada konfirmasi eksplisit")
    
    print("\n[SCENARIO 3] User jawab 'ya' lalu 'sudah normal' (2 step)")
    print("-" * 60)
    
    memstore.clear(user_id)
    memstore.set_flag(user_id, "active_intent", "eac_tidak_menyala")
    memstore.set_flag(user_id, "eac_tidak_menyala_active_step", "check_mcb")
    memstore.set_flag(user_id, "check_mcb_waiting_confirm", True)
    memstore.set_flag(user_id, "check_mcb_confirm_data", {
        "resolve_if_yes": True,
        "next_if_no": None,
        "pending_if_no": True
    })
    
    memstore.append_history(user_id, "bot", "Apakah alatnya sudah berfungsi normal kak?")
    
    response1 = engine.handle(user_id, "ya")
    print(f"User: ya")
    print(f"Bot: {response1['bubbles'][0]['text']}")
    
    response2 = engine.handle(user_id, "sudah normal kak")
    print(f"User: sudah normal kak")
    print(f"Bot: {response2['bubbles'][0]['text']}")
    print(f"Status: {response2.get('status', 'N/A')}")
    
    if response2.get('status') == 'resolved':
        print("✅ BERHASIL: Sistem resolve setelah konfirmasi eksplisit di message kedua")
    else:
        print("❌ GAGAL: Sistem tidak resolve meskipun sudah ada konfirmasi eksplisit")
    
    print("\n[SCENARIO 4] User jawab 'belum' (negative)")
    print("-" * 60)
    
    memstore.clear(user_id)
    memstore.set_flag(user_id, "active_intent", "eac_tidak_menyala")
    memstore.set_flag(user_id, "eac_tidak_menyala_active_step", "check_mcb")
    memstore.set_flag(user_id, "check_mcb_waiting_confirm", True)
    memstore.set_flag(user_id, "check_mcb_confirm_data", {
        "resolve_if_yes": True,
        "next_if_no": None,
        "pending_if_no": True
    })
    
    memstore.append_history(user_id, "bot", "Apakah alatnya sudah berfungsi normal kak?")
    
    response = engine.handle(user_id, "belum kak")
    
    print(f"User: belum kak")
    print(f"Bot: {response['bubbles'][0]['text']}")
    print(f"Status: {response.get('status', 'N/A')}")
    
    if response.get('status') != 'resolved':
        print("✅ BERHASIL: Sistem tidak resolve karena user jawab negatif")
    else:
        print("❌ GAGAL: Sistem resolve meskipun user jawab negatif")
    
    memstore.clear(user_id)
    
    print("\n" + "=" * 60)
    print("TEST SELESAI")
    print("=" * 60)

if __name__ == "__main__":
    test_resolution_logic()
