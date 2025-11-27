#!/usr/bin/env python3
import requests
import json

API_URL = "http://localhost:8080/chat"
SECRET = "dev_reset_2024"

def test_company_detection():
    print("=" * 60)
    print("Test: Deteksi Nama Perusahaan Tanpa PT/CV/UD")
    print("=" * 60)
    
    test_cases = [
        {
            "name": "Perusahaan tanpa inisiator",
            "user_id": "test_company_1",
            "nama": "Sejahtera Abadi",
            "expected_company": True
        },
        {
            "name": "Perusahaan dengan Toko",
            "user_id": "test_company_2",
            "nama": "Toko Berkah Jaya",
            "expected_company": True
        },
        {
            "name": "Perusahaan dengan PT",
            "user_id": "test_company_3",
            "nama": "PT Maju Mandiri",
            "expected_company": True
        },
        {
            "name": "Nama personal",
            "user_id": "test_personal_1",
            "nama": "Budi Santoso",
            "expected_company": False
        },
        {
            "name": "Nama personal female",
            "user_id": "test_personal_2",
            "nama": "Siti Nurhaliza",
            "expected_company": False
        }
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n{'='*60}")
        print(f"Test {i}: {test['name']}")
        print(f"{'='*60}")
        
        user_id = test['user_id']
        nama = test['nama']
        
        print(f"\n1. Trigger pending mode...")
        r = requests.post(API_URL, json={
            "user_id": user_id,
            "text": f"/dev pending {SECRET}"
        })
        
        if r.status_code == 200:
            data = r.json()
            bot_msg = data['bubbles'][0]['text']
            print(f"   Bot: {bot_msg}")
        
        print(f"\n2. Input nama: {nama}")
        r = requests.post(API_URL, json={
            "user_id": user_id,
            "text": nama
        })
        
        if r.status_code == 200:
            data = r.json()
            bot_msg = data['bubbles'][0]['text']
            print(f"   Bot: {bot_msg}")
        
        print(f"\n3. Input produk: F57A")
        r = requests.post(API_URL, json={
            "user_id": user_id,
            "text": "F57A"
        })
        
        if r.status_code == 200:
            data = r.json()
            bot_msg = data['bubbles'][0]['text']
            print(f"   Bot: {bot_msg}")
        
        print(f"\n4. Input alamat...")
        r = requests.post(API_URL, json={
            "user_id": user_id,
            "text": "Jl. Sudirman No. 123, Jakarta Selatan"
        })
        
        if r.status_code == 200:
            data = r.json()
            bot_msg = data['bubbles'][0]['text']
            print(f"   Bot: {bot_msg}")
            
            print(f"\n📝 Pesan Akhir:")
            print(f"   {bot_msg}")
            
            if test['expected_company']:
                if f"Kak {nama}" in bot_msg or f"Pak {nama}" in bot_msg or f"Bu {nama}" in bot_msg:
                    print(f"\n❌ GAGAL: Bot pakai sapaan untuk perusahaan!")
                    print(f"   Expected: '{nama}' (tanpa sapaan)")
                    print(f"   Got: sapaan terdeteksi")
                else:
                    print(f"\n✅ BERHASIL: Nama perusahaan tanpa sapaan")
            else:
                has_salutation = (f"Pak {nama}" in bot_msg or 
                                f"Bu {nama}" in bot_msg or 
                                f"Kak {nama}" in bot_msg)
                
                if has_salutation:
                    print(f"\n✅ BERHASIL: Nama personal dengan sapaan")
                else:
                    print(f"\n⚠️  Cek manual - sapaan mungkin berbeda")
        
        print(f"\n{'='*60}\n")

if __name__ == "__main__":
    try:
        r = requests.get("http://localhost:8080/health", timeout=2)
        if r.status_code == 200:
            print("\n✅ Server ready\n")
            test_company_detection()
        else:
            print("❌ Server error")
    except:
        print("❌ Server tidak tersedia di localhost:8080")
