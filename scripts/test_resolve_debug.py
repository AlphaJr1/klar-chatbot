#!/usr/bin/env python3
import sys, os
BASE = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, BASE)

from src.convo.engine import ConversationEngine

engine = ConversationEngine()
user = "test_resolve_3"

print("Test: sudah dicoba semua\n")

# Step 1
r = engine.handle(user, "EAC saya mati")
print(f"1. User: 'EAC saya mati'")
print(f"   Bot: '{r['bubbles'][0]['text'][:60]}'")
print(f"   Status: {r.get('status')}, Resolved: {engine.memstore.get_flag(user, 'sop_resolved')}")

# Step 2
r = engine.handle(user, "sudah rapat")
print(f"\n2. User: 'sudah rapat'")
print(f"   Bot: '{r['bubbles'][0]['text'][:60]}'")
print(f"   Status: {r.get('status')}, Resolved: {engine.memstore.get_flag(user, 'sop_resolved')}")

# Step 3 - This is where premature resolve happens
print(f"\n3. User: 'sudah dicoba semua'")
print(f"   BEFORE handle:")
print(f"     Resolved flag: {engine.memstore.get_flag(user, 'sop_resolved')}")

r = engine.handle(user, "sudah dicoba semua")

print(f"   AFTER handle:")
print(f"     Bot: '{r['bubbles'][0]['text']}'")
print(f"     Status: {r.get('status')}")
print(f"     Resolved flag: {engine.memstore.get_flag(user, 'sop_resolved')}")
print(f"     Waiting confirm: {engine.memstore.get_flag(user, 'mati_active_step')}")

if r.get('status') == 'resolved':
    print("   ❌ BUG: Status is 'resolved' but should be 'unknown' (waiting confirm)")
elif "sudah" in r['bubbles'][0]['text'].lower() and "normal" in r['bubbles'][0]['text'].lower():
    print("   ✅ CORRECT: Bot asking confirmation, not resolving yet")
