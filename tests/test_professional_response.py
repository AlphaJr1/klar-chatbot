import requests
import json

BASE_URL = "http://localhost:8080"

def get_bot_response(resp_json):
    bubbles = resp_json.get('bubbles', [])
    if bubbles:
        return bubbles[0].get('text', '')
    return ''

def test_professional_response():
    print("🧪 Test Professional Natural Response")
    print("=" * 60)
    
    user_id = "test_professional_001"
    
    # Reset
    print("\n🔄 Reset memory...")
    reset_resp = requests.post(f"{BASE_URL}/chat", json={
        "user_id": user_id,
        "text": "/dev reset dev_reset_2024"
    })
    print(f"{get_bot_response(reset_resp.json())}")
    
    # Test 1: Komplain bunyi
    print("\n" + "=" * 60)
    print("1️⃣ Customer komplain bunyi")
    resp = requests.post(f"{BASE_URL}/chat", json={
        "user_id": user_id,
        "text": "alat saya berbunyi aneh"
    })
    bot_msg = get_bot_response(resp.json())
    print(f"Bot: {bot_msg}")
    print(f"✅ Cek: Tidak ada 'dong', 'aja', 'gitu', 'sih'")
    
    # Test 2: Customer jawab sering
    print("\n" + "=" * 60)
    print("2️⃣ Customer jawab bunyi sering")
    resp = requests.post(f"{BASE_URL}/chat", json={
        "user_id": user_id,
        "text": "sering kak"
    })
    bot_msg = get_bot_response(resp.json())
    print(f"Bot: {bot_msg}")
    print(f"✅ Cek: Profesional, tidak ada bahasa gaul")
    
    # Test 3: Customer setuju teknisi
    print("\n" + "=" * 60)
    print("3️⃣ Customer setuju teknisi")
    resp = requests.post(f"{BASE_URL}/chat", json={
        "user_id": user_id,
        "text": "iya boleh"
    })
    for bubble in resp.json().get('bubbles', []):
        print(f"Bot: {bubble.get('text', '')}")
    print(f"✅ Cek: Profesional dan jelas")
    
    # Reset untuk test baru
    print("\n" + "=" * 60)
    print("🔄 Reset untuk test selanjutnya...")
    reset_resp = requests.post(f"{BASE_URL}/chat", json={
        "user_id": user_id,
        "text": "/dev reset dev_reset_2024"
    })
    
    # Test 4: Komplain mati
    print("\n" + "=" * 60)
    print("4️⃣ Customer komplain mati")
    resp = requests.post(f"{BASE_URL}/chat", json={
        "user_id": user_id,
        "text": "alat mati total"
    })
    bot_msg = get_bot_response(resp.json())
    print(f"Bot: {bot_msg}")
    print(f"✅ Cek: Instruksi jelas dan profesional")
    
    # Test 5: Cover sudah rapat
    print("\n" + "=" * 60)
    print("5️⃣ Customer jawab cover sudah rapat")
    resp = requests.post(f"{BASE_URL}/chat", json={
        "user_id": user_id,
        "text": "sudah rapat"
    })
    bot_msg = get_bot_response(resp.json())
    print(f"Bot: {bot_msg}")
    print(f"✅ Cek: Pertanyaan berikutnya natural tapi profesional")
    
    # Test 6: Sudah LOW tapi masih mati
    print("\n" + "=" * 60)
    print("6️⃣ Customer jawab sudah LOW tapi masih mati")
    resp = requests.post(f"{BASE_URL}/chat", json={
        "user_id": user_id,
        "text": "sudah saya tekan LOW tapi masih mati"
    })
    bot_msg = get_bot_response(resp.json())
    print(f"Bot: {bot_msg}")
    print(f"✅ Cek: Pertanyaan MCB profesional")
    
    # Test 7: MCB sudah ON
    print("\n" + "=" * 60)
    print("7️⃣ Customer jawab MCB sudah ON")
    resp = requests.post(f"{BASE_URL}/chat", json={
        "user_id": user_id,
        "text": "sudah ON"
    })
    bot_msg = get_bot_response(resp.json())
    print(f"Bot: {bot_msg}")
    print(f"✅ Cek: Instruksi profesional, tidak ada 'dong', 'aja'")
    
    # Test 8: Masih mati
    print("\n" + "=" * 60)
    print("8️⃣ Customer bilang masih mati")
    resp = requests.post(f"{BASE_URL}/chat", json={
        "user_id": user_id,
        "text": "masih mati juga"
    })
    for bubble in resp.json().get('bubbles', []):
        msg = bubble.get('text', '')
        print(f"Bot: {msg}")
        # Check for bad words
        bad_words = ['dong', 'aja', 'gitu', 'sih', 'teknisian']
        for word in bad_words:
            if word in msg.lower():
                print(f"  ❌ FOUND BAD WORD: '{word}'")
    print(f"✅ Cek: Pending message profesional, tidak ada kata gaul")
    
    print("\n" + "=" * 60)
    print("✅ Test selesai!")
    print("Pastikan tidak ada:")
    print("  - Bahasa gaul: dong, aja, gitu, sih")
    print("  - Kata serapan salah: teknisian")
    print("  - Bahasa yang terlalu informal atau aneh")

if __name__ == "__main__":
    test_professional_response()
