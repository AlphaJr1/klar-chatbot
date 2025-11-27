#!/usr/bin/env python3
"""Quick validation - test semua perbaikan"""
import requests
import json

BASE_URL = "http://localhost:8081"

def reset(uid):
    requests.post(f"{BASE_URL}/admin/reset-memory", 
                  params={"user_id": uid, "secret": "dev_reset_2024"})

def chat(uid, msg):
    r = requests.post(f"{BASE_URL}/chat", json={"user_id": uid, "text": msg})
    result = r.json()
    text = " | ".join([b.get("text", "") for b in result.get("bubbles", [])])
    return result.get("status"), text

print("="*70)
print("QUICK VALIDATION - ALL FIXES")
print("="*70)

# Test 1: MATI → Resolved
print("\n[1] Test MATI Flow → RESOLVED")
reset("v1")
s1, t1 = chat("v1", "EAC mati")
print(f"  Step 1: {s1}")
s2, t2 = chat("v1", "sudah rapat")
print(f"  Step 2: {s2} - Lanjut ke LOW mode? {'✓' if 'LOW' in t2 or 'low' in t2 else '✗'}")
s3, t3 = chat("v1", "sudah menyala")
print(f"  Step 3: {s3} - Resolved? {'✓' if s3 == 'resolved' else '✗'}")

# Test 2: BUNYI → Jarang → Resolved
print("\n[2] Test BUNYI Jarang → RESOLVED")
reset("v2")
s1, t1 = chat("v2", "EAC bunyi")
print(f"  Step 1: {s1} - Ask frequency? {'✓' if 'sering' in t1.lower() or 'jarang' in t1.lower() else '✗'}")
s2, t2 = chat("v2", "jarang kok")
print(f"  Step 2: {s2} - Resolved? {'✓' if s2 == 'resolved' else '✗'}")

# Test 3: BUNYI → Sering → Pending + Data
print("\n[3] Test BUNYI Sering → PENDING + DATA COLLECTION")
reset("v3")
chat("v3", "EAC berisik")
s1, t1 = chat("v3", "sering banget")
print(f"  Parse: Sering detected? {'✓' if 'teknisi' in t1.lower() else '✗'}")
s2, t2 = chat("v3", "ya")
print(f"  Trigger: Data collection? {'✓' if 'nama' in t2.lower() else '✗'}")
s3, t3 = chat("v3", "Budi")
print(f"  Name: Gender detect? {'✓' if 'Pak' in t3 or 'produk' in t3.lower() else '✗'}")
s4, t4 = chat("v3", "F90A")
print(f"  Product: Ask address? {'✓' if 'alamat' in t4.lower() else '✗'}")
s5, t5 = chat("v3", "Jl. Sudirman 123, Jakarta Selatan")
print(f"  Address: Pending? {'✓' if s5 == 'pending' else '✗'}")

# Test 4: Parse accuracy
print("\n[4] Test PARSE ACCURACY")
print("  Testing negative context...")
reset("v4")
chat("v4", "EAC tidak menyala")
chat("v4", "sudah rapat")
s, t = chat("v4", "masih tidak nyala juga")
print(f"  'masih tidak nyala' → Lanjut ke MCB? {'✓' if 'mcb' in t.lower() or 'listrik' in t.lower() else '✗'}")

print("\n" + "="*70)
print("✅ VALIDATION COMPLETE")
print("="*70)
