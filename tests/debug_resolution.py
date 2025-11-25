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

def test_simple_case():
    engine = ConversationEngine()
    test_user_id = "test_simple"
    
    print("=" * 60)
    print("DEBUG: Simple Resolution Test")
    print("=" * 60)
    
    reset_user_state(engine, test_user_id)
    
    # Message 1
    print("\n[Message 1: EAC saya mati]")
    result1 = engine.handle(test_user_id, "EAC saya mati")
    print(f"Bot: {result1['bubbles'][0]['text'][:100]}...")
    
    # Check state
    active = engine.memstore.get_flag(test_user_id, "active_intent")
    pending = engine.memstore.get_flag(test_user_id, "sop_pending")
    print(f"State after message 1: active_intent={active}, sop_pending={pending}")
    
    # Message 2
    print("\n[Message 2: alat sudah menyala kembali]")
    result2 = engine.handle(test_user_id, "alat sudah menyala kembali")
    print(f"Bot: {result2['bubbles'][0]['text'][:100]}...")
    print(f"Status: {result2.get('status', 'None')}")
    print(f"Next: {result2.get('next', 'None')}")
    
    # Check state
    active = engine.memstore.get_flag(test_user_id, "active_intent")
    pending = engine.memstore.get_flag(test_user_id, "sop_pending")
    resolved = engine.memstore.get_flag(test_user_id, "sop_resolved")
    print(f"State after message 2: active_intent={active}, sop_pending={pending}, sop_resolved={resolved}")
    
    if result2.get('status') == 'resolved':
        print("\n✅ PASS - Resolusi terdeteksi dengan benar")
    else:
        print("\n❌ FAIL - Resolusi tidak terdeteksi")

if __name__ == "__main__":
    test_simple_case()
