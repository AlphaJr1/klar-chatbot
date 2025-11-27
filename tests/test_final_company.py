#!/usr/bin/env python3
import requests

API_URL = "http://localhost:8080/chat"
SECRET = "dev_reset_2024"

def test_final():
    print("=" * 70)
    print("Test Final: Deteksi Nama Perusahaan (LLM-based)")
    print("=" * 70)
    
    tests = [
        ("Sejahtera Abadi", True, "Perusahaan tanpa PT/CV"),
        ("Toko Makmur Jaya", True, "Perusahaan dengan Toko"),
        ("PT Karya Mandiri", True, "Perusahaan dengan PT"),
        ("Budi Santoso", False, "Nama personal male"),
        ("Siti Nurhaliza", False, "Nama personal female"),
    ]
    
    for nama, is_company, desc in tests:
        user_id = f"test_{nama.replace(' ', '_').lower()}"
        
        print(f"\n{'='*70}")
        print(f"Test: {desc}")
        print(f"Nama: {nama}")
        print(f"Expected: {'Perusahaan' if is_company else 'Personal'}")
        print(f"{'='*70}\n")
        
        requests.post(API_URL, json={"user_id": user_id, "text": f"/dev pending {SECRET}"})
        
        r1 = requests.post(API_URL, json={"user_id": user_id, "text": nama})
        print(f"[Nama] Bot: {r1.json()['bubbles'][0]['text'][:80]}...")
        
        r2 = requests.post(API_URL, json={"user_id": user_id, "text": "F57A"})
        print(f"[Prod] Bot: {r2.json()['bubbles'][0]['text'][:80]}...")
        
        r3 = requests.post(API_URL, json={"user_id": user_id, "text": "Jl. Sudirman No. 123 RT 01 RW 02, Jakarta Selatan"})
        final_msg = r3.json()['bubbles'][0]['text']
        print(f"[Addr] Bot: {final_msg[:80]}...")
        
        print(f"\n📝 Pesan Lengkap:")
        print(f"   {final_msg}")
        
        if is_company:
            has_salutation = any(x in final_msg for x in [f"Kak {nama}", f"Pak {nama}", f"Bu {nama}"])
            if has_salutation:
                print(f"\n❌ GAGAL: Perusahaan pakai sapaan")
            else:
                print(f"\n✅ PASS: Perusahaan tanpa sapaan")
        else:
            has_salutation = any(x in final_msg for x in [f"Pak {nama}", f"Bu {nama}", f"Kak {nama}"])
            if has_salutation:
                print(f"\n✅ PASS: Personal dengan sapaan")
            else:
                print(f"\n⚠️  CHECK: Sapaan tidak terdeteksi (cek manual)")

if __name__ == "__main__":
    try:
        r = requests.get("http://localhost:8080/health", timeout=2)
        test_final()
    except Exception as e:
        print(f"❌ Error: {e}")
