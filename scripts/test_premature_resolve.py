#!/usr/bin/env python3
import sys, os
BASE = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, BASE)

from src.convo.engine import ConversationEngine

engine = ConversationEngine()
user = "test_premature_resolve"

print("=" * 60)
print("TEST PREMATURE RESOLUTION BUG")
print("=" * 60)

print("\n🧪 Test Case: User says problem still exists\n")

# Simulate troubleshooting flow
messages = [
    ("EAC saya mati", "Initial complaint"),
    ("sudah rapat kok kak", "Answer: cover already tight"),
    ("sudah saya tekan LOW tapi masih mati", "Answer: still not working"),
    ("sudah ON kak MCBnya", "Answer: MCB already ON"),
    ("Baik ka, saya sudah coba namun masih tetap tidak nyala", "Should NOT resolve!"),
]

for i, (msg, desc) in enumerate(messages, 1):
    print(f"\n{i}. User: '{msg}'")
    print(f"   ({desc})")
    
    result = engine.handle(user, msg)
    response = result.get("bubbles", [{}])[0].get("text", "")
    status = result.get("status", "unknown")
    resolved = engine.memstore.get_flag(user, "sop_resolved")
    
    print(f"   Bot: '{response[:80]}...'")
    print(f"   Status: {status}, Resolved flag: {resolved}")
    
    if "masih" in msg and "tidak" in msg and status == "resolved":
        print("   ❌ BUG: Bot resolved padahal user bilang masih tidak nyala!")
    elif "masih" in msg and "tidak" in msg and status != "resolved":
        print("   ✅ CORRECT: Bot tidak resolve, lanjut troubleshoot")

print("\n" + "=" * 60)
print("✅ TEST COMPLETE")
print("=" * 60)
