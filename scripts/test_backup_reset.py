#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.convo.memory_store import MemoryStore

store = MemoryStore(path="data/storage/memory.json", autosave=True)

test_user_id = "test_user_backup_123"

print(f"📝 Adding test data for user: {test_user_id}")
store.set_name(test_user_id, "Test User")
store.set_product(test_user_id, "Electronic Air Cleaner F57A")
store.set_flag(test_user_id, "active_intent", "tidak_nyala")
store.append_history(test_user_id, "user", "Halo, alat saya tidak menyala")
store.append_history(test_user_id, "bot", "Baik kak, saya akan bantu cek.")

print(f"\n📊 Data sebelum reset:")
data = store.get(test_user_id)
print(f"- Name: {data.get('name')}")
print(f"- Product: {data.get('product')}")
print(f"- History: {len(data.get('history', []))} messages")
print(f"- Active Intent: {data.get('flags', {}).get('active_intent')}")

print(f"\n🔄 Melakukan reset dengan backup...")
store.clear(test_user_id)

print(f"\n✅ Selesai! Cek folder data/storage/backups/")
print(f"\n📊 Data setelah reset:")
data_after = store.get(test_user_id)
print(f"- Name: {data_after.get('name')}")
print(f"- Product: {data_after.get('product')}")
print(f"- History: {len(data_after.get('history', []))} messages")
