#!/usr/bin/env python3
import sys, os
BASE = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, BASE)

from src.convo.engine import ConversationEngine

engine = ConversationEngine()
user = "test_clarify_simple"

print("Test 1: EAC berbunyi")
r = engine.handle(user, "EAC saya berbunyi")
print(f"Bot: {r['bubbles'][0]['text'][:60]}")

for i in range(5):
    print(f"\nTest {i+2}: bunyi aneh (unclear #{i+1})")
    r = engine.handle(user, "bunyi aneh gitu")
    count = engine.memstore.get_flag(user, "bunyi_clarify_count") or 0
    status = r.get("status", "unknown")
    print(f"Bot: {r['bubbles'][0]['text'][:80]}")
    print(f"Count: {count}, Status: {status}")
    
    if "teknisi" in r['bubbles'][0]['text'].lower():
        print("✅ ESCALATED!")
        break

print("\nDone!")
