#!/usr/bin/env python3
import sys, os
BASE = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, BASE)

from src.convo.engine import ConversationEngine

engine = ConversationEngine()
user = "test_resolve_2"

print("=" * 60)
print("TEST PREMATURE RESOLUTION - Case 2")
print("=" * 60)

messages = [
    "EAC saya mati",
    "sudah rapat",
    "sudah dicoba semua",
    "alat sudah menyala kembali kak",
    "baik",
]

for i, msg in enumerate(messages, 1):
    print(f"\n{i}. User: '{msg}'")
    
    result = engine.handle(user, msg)
    response = result.get("bubbles", [{}])[0].get("text", "")
    status = result.get("status", "unknown")
    resolved = engine.memstore.get_flag(user, "sop_resolved")
    
    print(f"   Bot: '{response[:80]}'")
    print(f"   Status: {status}, Resolved: {resolved}")
    
    # Check if bot resolved prematurely
    if i < 4 and status == "resolved":
        print(f"   ❌ PREMATURE: Resolved at step {i} before user confirm!")
    elif i == 4 and status == "resolved":
        print(f"   ✅ CORRECT: Resolved after user confirm 'alat sudah menyala'")
    elif i == 5 and "keluhan" in response.lower():
        print(f"   ❌ BUG: Bot ask for new complaint after resolved+ack")

print("\n" + "=" * 60)
