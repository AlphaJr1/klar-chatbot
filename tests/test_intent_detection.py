import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.convo.engine import ConversationEngine

def test_intent_detection_improvement():
    print("=" * 70)
    print("TEST: Intent Detection Improvement")
    print("=" * 70)
    
    engine = ConversationEngine()
    
    test_cases = [
        # Intent: mati
        ("EAC saya mati nih", "mati"),
        ("alat tidak menyala", "mati"),
        ("unit padam total", "mati"),
        ("tidak hidup sama sekali", "mati"),
        ("mati total kak", "mati"),
        ("tidak berfungsi", "mati"),
        ("gak nyala", "mati"),
        ("water heater tidak panas", "mati"),
        
        # Intent: bunyi
        ("alat saya berbunyi aneh", "bunyi"),
        ("EAC bunyi kretek kretek", "bunyi"),
        ("suara berisik", "bunyi"),
        ("bunyi brebet", "bunyi"),
        ("mengeluarkan bunyi", "bunyi"),
        ("ada bunyi aneh", "bunyi"),
        ("berisik banget", "bunyi"),
        ("EAC di kantor kami berbunyi yang cukup mengganggu", "bunyi"),
        ("Kak EAC saya kok muncul bunyi terus yaa?", "bunyi"),
        
        # Intent: bau
        ("bau tidak sedap", "bau"),
        ("ada bau aneh", "bau"),
        ("bau menyengat", "bau"),
        ("aroma tidak enak", "bau"),
        
        # Intent: none (chitchat)
        ("halo", "none"),
        ("terima kasih", "none"),
        ("baik", "none"),
        ("oke siap", "none"),
    ]
    
    passed = 0
    failed = 0
    
    for message, expected_intent in test_cases:
        user_id = f"test_intent_{passed + failed}"
        engine.memstore.clear(user_id)
        
        result = engine.detect_intent_via_llm(user_id, message, ["mati", "bau", "bunyi"])
        detected_intent = result.get("intent", "none")
        
        status = "✅" if detected_intent == expected_intent else "❌"
        
        if detected_intent == expected_intent:
            passed += 1
        else:
            failed += 1
            
        print(f"{status} '{message[:50]}...' → Expected: {expected_intent}, Got: {detected_intent}")
        
        engine.memstore.clear(user_id)
    
    print("\n" + "=" * 70)
    print(f"HASIL: {passed}/{len(test_cases)} passed, {failed}/{len(test_cases)} failed")
    print(f"Accuracy: {passed/len(test_cases)*100:.1f}%")
    print("=" * 70)
    
    return failed == 0

if __name__ == "__main__":
    success = test_intent_detection_improvement()
    sys.exit(0 if success else 1)
