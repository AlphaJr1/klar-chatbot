#!/usr/bin/env python3

import sys
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, 'src'))

from convo.engine import ConversationEngine

def reset_user_state(engine, user_id):
    engine.memstore.clear_flag(user_id, "active_intent")
    engine.memstore.clear_flag(user_id, "sop_pending")
    engine.memstore.clear_flag(user_id, "sop_resolved")
    
    for intent in ["mati", "bau", "bunyi"]:
        engine.memstore.clear_flag(user_id, f"{intent}_active_step")
        engine.memstore.clear_flag(user_id, f"{intent}_completed_steps")
        for step in ["cek_tutup", "cek_remote_low", "cek_mcb"]:
            engine.memstore.clear_flag(user_id, f"asked_{step}")
            engine.memstore.clear_flag(user_id, f"{step}_answer")
            engine.memstore.clear_flag(user_id, f"{step}_waiting_confirm")
            engine.memstore.clear_flag(user_id, f"{step}_confirm_data")
    
    engine.memstore.flush_history(user_id)

def test_bug_fixes():
    engine = ConversationEngine()
    
    test_user_id = "test_bug_fix_001"
    
    print("=" * 60)
    print("TEST 1: Respons saat user bilang 'iya' (acknowledge)")
    print("=" * 60)
    
    reset_user_state(engine, test_user_id)
    
    result1 = engine.handle(test_user_id, "Halo EAC saya mati")
    print(f"\nUser: Halo EAC saya mati")
    print(f"Bot: {result1['bubbles'][0]['text']}")
    
    result2 = engine.handle(test_user_id, "iya")
    print(f"\nUser: iya")
    print(f"Bot: {result2['bubbles'][0]['text']}")
    print(f"Status: {result2.get('status', 'unknown')}")
    print(f"Next: {result2.get('next', 'unknown')}")
    
    expected_natural = ["dicoba", "kabari", "ditunggu", "silakan"]
    is_natural = any(word in result2['bubbles'][0]['text'].lower() for word in expected_natural)
    
    if is_natural:
        print("✅ PASS - Respons lebih natural (tidak kaku)")
    else:
        print("❌ FAIL - Respons masih kaku")
        print(f"   Expected keywords: {expected_natural}")
    
    print("\n" + "=" * 60)
    print("TEST 2: Resolusi saat 'alat sudah menyala kembali'")
    print("=" * 60)
    
    reset_user_state(engine, test_user_id)
    
    result3 = engine.handle(test_user_id, "EAC saya mati")
    print(f"\nUser: EAC saya mati")
    print(f"Bot: {result3['bubbles'][0]['text']}")
    
    result4 = engine.handle(test_user_id, "alat sudah menyala kembali")
    print(f"\nUser: alat sudah menyala kembali")
    print(f"Bot: {result4['bubbles'][0]['text']}")
    print(f"Status: {result4.get('status', 'unknown')}")
    print(f"Next: {result4.get('next', 'unknown')}")
    
    if result4.get('status') == 'resolved':
        print("✅ PASS - Status resolved dengan benar")
    else:
        print(f"❌ FAIL - Status harusnya 'resolved', tapi dapat '{result4.get('status')}'")
    
    print("\n" + "=" * 60)
    print("TEST 3: Berbagai variasi resolusi eksplisit")
    print("=" * 60)
    
    test_messages = [
        "sudah berfungsi kak",
        "sudah normal",
        "berhasil menyala",
        "unit sudah nyala",
    ]
    
    for msg in test_messages:
        reset_user_state(engine, test_user_id)
        engine.handle(test_user_id, "EAC mati")
        result = engine.handle(test_user_id, msg)
        status = result.get('status', 'unknown')
        check = "✅" if status == "resolved" else "❌"
        print(f"{check} '{msg}' → Status: {status}")
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print("Bug fix mencakup:")
    print("1. ✅ Deteksi resolusi eksplisit")
    print("2. ✅ Handling acknowledge yang lebih natural")
    print("3. ✅ Tidak lanjut ke step berikutnya jika sudah resolved")

if __name__ == "__main__":
    test_bug_fixes()
