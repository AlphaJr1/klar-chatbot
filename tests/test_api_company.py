#!/usr/bin/env python3
import sys
import os
import requests
import json

API_URL = "http://localhost:8080/chat"
ADMIN_SECRET = "dev_reset_2024"

def test_api_company_name():
    print("=" * 60)
    print("Test API: Sapaan untuk Nama Perusahaan vs Personal")
    print("=" * 60)
    
    test_scenarios = [
        {
            "name": "Test Nama Perusahaan (PT)",
            "user_id": "test_pt_company",
            "messages": [
                "eac tidak nyala",
                "tidak",
                "PT Sejahtera Abadi",
                "F57A",
                "Jl. Sudirman No. 123, Jakarta Selatan"
            ]
        },
        {
            "name": "Test Nama Personal",
            "user_id": "test_personal_name",
            "messages": [
                "eac tidak nyala",
                "tidak",
                "Budi Santoso",
                "F57A",
                "Jl. Gatot Subroto No. 45, Jakarta Pusat"
            ]
        }
    ]
    
    for scenario in test_scenarios:
        print(f"\n{'='*60}")
        print(f"{scenario['name']}")
        print(f"{'='*60}\n")
        
        try:
            requests.post(
                f"http://localhost:8080/admin/reset-memory",
                params={"user_id": scenario['user_id'], "secret": ADMIN_SECRET},
                timeout=5
            )
        except:
            pass
        
        for i, msg in enumerate(scenario['messages'], 1):
            print(f"[{i}] User: {msg}")
            
            try:
                response = requests.post(
                    API_URL,
                    json={"user_id": scenario['user_id'], "text": msg},
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    bubbles = data.get("bubbles", [])
                    
                    bot_reply = ""
                    for bubble in bubbles:
                        text = bubble.get("text", "")
                        if text:
                            bot_reply += text + " "
                    
                    bot_reply = bot_reply.strip()
                    print(f"Bot: {bot_reply}")
                    
                    if i == len(scenario['messages']):
                        print(f"\n📝 Pesan terakhir (setelah data lengkap):")
                        print(f"   {bot_reply}")
                        
                        name_msg = scenario['messages'][2]
                        if "PT" in name_msg or "CV" in name_msg or "UD" in name_msg:
                            print(f"\n✅ Cek: Bot SEHARUSNYA memanggil '{name_msg}' TANPA 'Kak/Pak/Bu'")
                            if "Kak PT" in bot_reply or "Pak PT" in bot_reply or "Bu PT" in bot_reply:
                                print(f"❌ GAGAL: Bot masih pakai sapaan 'Kak/Pak/Bu' untuk nama perusahaan!")
                            else:
                                print(f"✅ BERHASIL: Bot tidak pakai sapaan untuk perusahaan")
                        else:
                            print(f"\n✅ Cek: Bot SEHARUSNYA memanggil 'Pak/Bu/Kak + {name_msg}'")
                            if f"Pak {name_msg}" in bot_reply or f"Bu {name_msg}" in bot_reply or f"Kak {name_msg}" in bot_reply:
                                print(f"✅ BERHASIL: Bot pakai sapaan yang tepat")
                            else:
                                print(f"⚠️  Perlu dicek manual apakah sapaan sudah benar")
                else:
                    print(f"❌ Error: {response.status_code} - {response.text}")
                    
            except Exception as e:
                print(f"❌ Error: {e}")
            
            print()
        
        print(f"{'='*60}\n")

if __name__ == "__main__":
    print("\n⚠️  Pastikan server sudah running di localhost:8080\n")
    
    try:
        requests.get("http://localhost:8080/health", timeout=2)
        test_api_company_name()
    except:
        print("❌ Server tidak tersedia di localhost:8080")
        print("Jalankan: bash bin/start_with_ngrok.sh")
