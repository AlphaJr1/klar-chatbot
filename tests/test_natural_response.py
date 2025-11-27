import requests
import json

BASE_URL = "http://localhost:8080"

def get_bot_response(resp_json):
    bubbles = resp_json.get('bubbles', [])
    if bubbles:
        return bubbles[0].get('text', '')
    return ''

def test_natural_response():
    print("🧪 Test Natural Response Bot")
    print("=" * 50)
    
    user_id = "test_natural_001"
    
    # Test 1: Komplain tentang bunyi
    print("\n1️⃣ Customer komplain bunyi")
    resp = requests.post(f"{BASE_URL}/chat", json={
        "user_id": user_id,
        "text": "alat saya berbunyi aneh"
    })
    print(f"Bot: {get_bot_response(resp.json())}")
    
    # Test 2: Jawaban customer tentang frekuensi
    print("\n2️⃣ Customer jawab frekuensi bunyi (natural)")
    resp = requests.post(f"{BASE_URL}/chat", json={
        "user_id": user_id,
        "text": "hmm bisa dibilang sering sih kak"
    })
    print(f"Bot: {get_bot_response(resp.json())}")
    print("\n✅ Perhatikan: respons bot seharusnya lebih natural, tidak kaku seperti template SOP!")
    
    # Test 3: Customer bilang mau bantuan teknisi
    print("\n3️⃣ Customer setuju bantuan teknisi")
    resp = requests.post(f"{BASE_URL}/chat", json={
        "user_id": user_id,
        "text": "iya boleh, bantu dibersihkan"
    })
    for bubble in resp.json().get('bubbles', []):
        print(f"Bot: {bubble.get('text', '')}")
    print("\n✅ Respons pending seharusnya lebih natural!")
    
    # Reset untuk test baru
    print("\n" + "=" * 50)
    print("🔄 Reset memory...")
    reset_resp = requests.post(f"{BASE_URL}/chat", json={
        "user_id": user_id,
        "text": "/dev reset dev_reset_2024"
    })
    print(f"{get_bot_response(reset_resp.json())}")
    
    # Test 4: Komplain alat mati
    print("\n4️⃣ Customer komplain alat mati")
    resp = requests.post(f"{BASE_URL}/chat", json={
        "user_id": user_id,
        "text": "alat saya mati total"
    })
    print(f"Bot: {get_bot_response(resp.json())}")
    
    # Test 5: Customer jawab cover sudah rapat
    print("\n5️⃣ Customer jawab cover sudah rapat")
    resp = requests.post(f"{BASE_URL}/chat", json={
        "user_id": user_id,
        "text": "sudah rapat kok kak"
    })
    print(f"Bot: {get_bot_response(resp.json())}")
    print("\n✅ Pertanyaan berikutnya seharusnya natural!")
    
    # Test 6: Customer jawab sudah LOW tapi masih mati
    print("\n6️⃣ Customer jawab sudah LOW mode tapi masih mati")
    resp = requests.post(f"{BASE_URL}/chat", json={
        "user_id": user_id,
        "text": "sudah saya coba tekan LOW, tapi masih mati"
    })
    print(f"Bot: {get_bot_response(resp.json())}")
    
    # Test 7: Customer jawab MCB sudah ON
    print("\n7️⃣ Customer jawab MCB sudah ON")
    resp = requests.post(f"{BASE_URL}/chat", json={
        "user_id": user_id,
        "text": "sudah ON kak MCBnya"
    })
    print(f"Bot: {get_bot_response(resp.json())}")
    print("\n✅ Instruksi seharusnya natural!")
    
    # Test 8: Customer bilang masih mati juga
    print("\n8️⃣ Customer bilang masih mati setelah instruksi")
    resp = requests.post(f"{BASE_URL}/chat", json={
        "user_id": user_id,
        "text": "sudah saya coba tapi masih mati juga"
    })
    for bubble in resp.json().get('bubbles', []):
        print(f"Bot: {bubble.get('text', '')}")
    print("\n✅ Pending message seharusnya natural!")
    
    print("\n" + "=" * 50)
    print("✅ Test selesai! Cek apakah semua respons sudah natural dan tidak kaku")

if __name__ == "__main__":
    test_natural_response()
