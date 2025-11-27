import requests
import json

API_URL = "http://localhost:8080/chat"
SECRET = "dev_reset_2024"

def test_ack_after_resolved_direct():
    print("\n🧪 Test: Direct test - set sop_resolved manually lalu kirim 'baik'")
    print("=" * 60)
    
    user_id = "test_direct_resolved"
    
    print("1. Reset memory dulu")
    resp = requests.post(API_URL, json={
        "user_id": user_id,
        "text": f"/dev reset {SECRET}"
    })
    print(f"   Reset: {resp.json()['bubbles'][0]['text']}")
    
    print("\n2. Set sop_resolved via API / internal")
    print("   (Kita akan simulasi dengan flow normal dulu, atau langsung test dengan memastikan flag ter-set)")
    
    print("\n3. Kirim komplain dulu")
    resp = requests.post(API_URL, json={
        "user_id": user_id,
        "text": "kalau ada bunyi gimana?"
    })
    data = resp.json()
    print(f"   Bot: {data['bubbles'][0]['text'][:80]}...")
    
    print("\n4. Jawab untuk trigger resolve")
    resp = requests.post(API_URL, json={
        "user_id": user_id,
        "text": "jarang"
    })
    data = resp.json()
    for bubble in data.get("bubbles", []):
        print(f"   Bot: {bubble.get('text', '')[:80]}...")
    
    print("\n5. Konfirmasi ya (should resolve)")
    resp = requests.post(API_URL, json={
        "user_id": user_id,
        "text": "iya"
    })
    data = resp.json()
    for bubble in data.get("bubbles", []):
        text = bubble.get("text", "")
        print(f"   Bot: {text}")
        if "tutup" in text.lower() or data.get("status") == "resolved":
            print("   ✅ Tiket resolved!")
    
    print("\n6. Customer bilang 'baik' setelah resolved")
    resp = requests.post(API_URL, json={
        "user_id": user_id,
        "text": "baik"
    })
    data = resp.json()
    
    for bubble in data.get("bubbles", []):
        text = bubble.get("text", "")
        print(f"   Bot: {text}")
        
        if "keluhan" in text.lower() or "maaf kak" in text.lower():
            print("   ❌ FAIL: Bot masih nanya keluhan!")
            return False
        else:
            print("   ✅ PASS: Bot tidak nanya keluhan lagi!")
            return True
    
    return False

if __name__ == "__main__":
    result = test_ack_after_resolved_direct()
    if result:
        print("\n✅ Test PASSED!")
    else:
        print("\n❌ Test FAILED!")
