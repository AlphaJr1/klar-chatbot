#!/usr/bin/env python3
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from convo.engine import ConversationEngine

def test_company_name_detection():
    engine = ConversationEngine()
    test_user = "test_company_detection"
    
    print("=" * 60)
    print("Test: Deteksi Nama Perusahaan vs Nama Personal")
    print("=" * 60)
    
    test_cases = [
        {
            "description": "Test 1: Nama Perusahaan dengan PT",
            "messages": [
                ("eac saya rusak", "Keluhan awal"),
                ("tidak nyala", "Konfirmasi masalah"),
                ("sudah", "Jawaban troubleshooting"),
                ("tidak", "Jawaban troubleshooting"),
                ("PT Maju Jaya", "Nama perusahaan")
            ]
        },
        {
            "description": "Test 2: Nama Personal Biasa",
            "messages": [
                ("eac saya rusak", "Keluhan awal"),
                ("tidak nyala", "Konfirmasi masalah"),
                ("sudah", "Jawaban troubleshooting"),
                ("tidak", "Jawaban troubleshooting"),
                ("Budi Santoso", "Nama personal")
            ]
        }
    ]
    
    for test_case in test_cases:
        print(f"\n{'='*60}")
        print(f"{test_case['description']}")
        print(f"{'='*60}\n")
        
        engine.memstore.clear(test_user)
        
        for i, (msg, label) in enumerate(test_case['messages'], 1):
            print(f"\n[Step {i}] User ({label}): {msg}")
            result = engine.handle(test_user, msg)
            
            for bubble in result.get("bubbles", []):
                print(f"Bot: {bubble['text']}")
            
            if i == len(test_case['messages']):
                identity = engine.memstore.get_identity(test_user)
                print(f"\n📊 Identity Info:")
                print(f"   - Name: {identity.get('name')}")
                print(f"   - Gender: {identity.get('gender')}")
                print(f"   - Is Company: {identity.get('is_company', False)}")
                
                is_company = identity.get('is_company', False)
                if is_company:
                    print("\n✅ Bot SEHARUSNYA memanggil dengan nama langsung tanpa 'Kak'")
                else:
                    print("\n✅ Bot SEHARUSNYA memanggil dengan 'Pak/Bu/Kak + Nama'")
        
        print("\n" + "="*60)

if __name__ == "__main__":
    test_company_name_detection()
