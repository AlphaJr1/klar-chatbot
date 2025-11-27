#!/usr/bin/env python3
import sys, os
BASE = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, BASE)

from src.convo.engine import ConversationEngine

engine = ConversationEngine()

test_messages = [
    "sudah dicoba semua",
    "sudah saya coba",
    "sudah rapat",
    "alat sudah menyala kembali kak",
    "sudah menyala",
    "masih mati",
    "sudah coba tapi masih mati",
    "baik",
]

print("Testing _is_explicit_resolution():\n")
for msg in test_messages:
    result = engine._is_explicit_resolution(msg)
    print(f"'{msg}' → {result}")
