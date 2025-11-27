import requests
import json
import time

API_URL = "http://localhost:8080/chat"

def test_resolved_then_ack():
    print("\n🧪 Test: Resolved tiket, lalu customer bilang 'baik'")
    print("=" * 60)
    
    user_id = "test_resolved_ack_user"
    
    test_flow = [
        {"msg": "EAC saya mati kak", "expect_contains": None},
        {"msg": "sudah coba", "expect_contains": None},
        {"msg": "sudah dicoba semua", "expect_contains": None},
        {"msg": "alat sudah menyala kembali kak", "expect_contains": None},
        {"msg": "baik", "expect_not_contains": ["keluhan", "Maaf kak"]},
    ]
    
    for i, step in enumerate(test_flow, 1):
        print(f"\n📤 Step {i}: User → '{step['msg']}'")
        
        resp = requests.post(API_URL, json={
            "user_id": user_id,
            "text": step["msg"]
        })
        
        if resp.status_code != 200:
            print(f"❌ HTTP Error: {resp.status_code}")
            print(f"Response: {resp.text}")
            continue
        
        data = resp.json()
        bubbles = data.get("bubbles", [])
        
        for bubble in bubbles:
            text = bubble.get("text", "")
            print(f"📥 Bot → {text}")
            
            if i == len(test_flow):
                if step.get("expect_not_contains"):
                    for bad_word in step["expect_not_contains"]:
                        if bad_word.lower() in text.lower():
                            print(f"❌ FAIL: Bot masih nanya keluhan! Kata '{bad_word}' ditemukan")
                            return False
                
                print("✅ PASS: Bot tidak nanya keluhan lagi setelah resolved")
                return True
        
        time.sleep(0.5)
    
    return True

if __name__ == "__main__":
    result = test_resolved_then_ack()
    if result:
        print("\n✅ Test passed!")
    else:
        print("\n❌ Test failed!")
