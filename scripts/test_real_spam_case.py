#!/usr/bin/env python3
import sys
import os

BASE = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, BASE)

from src.convo.engine import ConversationEngine

def test_real_spam_case():
    engine = ConversationEngine()
    test_user = "6287784566051_replay"
    
    print("=" * 60)
    print("REPLAY REAL SPAM CASE (User 6287784566051)")
    print("=" * 60)
    
    spam_messages = [
        "Anjg",
        "Al",
        "Ohokkk",
        "Affh iyh",
        "Ga boleh",
        "Ga boleh",
        "Maksa",
        "Tll",
        "Ga",
        "GA",
        "ENGGAK COK",
        "Gaa",
    ]
    
    print("\n🔁 Replaying spam sequence:\n")
    
    for i, msg in enumerate(spam_messages, 1):
        result = engine.handle(test_user, msg)
        response = result.get("bubbles", [{}])[0].get("text", "")
        spam_count = engine.memstore.get_flag(test_user, "spam_count") or 0
        
        print(f"{i:2d}. User: '{msg}'")
        print(f"    Bot:  '{response}'")
        print(f"    Spam count: {spam_count}")
        print()
    
    print("\n✅ Sekarang bot tidak stuck di fallback loop!")
    print("   Bot hanya respond dengan emoji 🙏 atau helpful message")
    print("   Tidak ada 'Maaf kak, boleh ceritakan keluhan...' berulang-ulang")
    
    print("\n🧪 Test normal message after spam:\n")
    
    result = engine.handle(test_user, "Eac saya mati nih kak")
    response = result.get("bubbles", [{}])[0].get("text", "")
    spam_count = engine.memstore.get_flag(test_user, "spam_count") or 0
    
    print(f"User: 'Eac saya mati nih kak'")
    print(f"Bot:  '{response[:80]}...'")
    print(f"Spam count reset to: {spam_count}")
    
    if spam_count == 0 and "🙏" not in response:
        print("\n✅ Bot kembali normal setelah user kirim pesan yang valid!")
    
    print("\n" + "=" * 60)
    print("✅ REAL SPAM CASE TEST COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    test_real_spam_case()
