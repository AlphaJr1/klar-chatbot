#!/usr/bin/env python3
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from convo.data_collector import DataCollector
from convo.ollama_client import OllamaClient
from convo.memory_store import MemoryStore

def test_company_name_extraction():
    print("=" * 60)
    print("Test: Ekstraksi Nama Perusahaan vs Nama Personal")
    print("=" * 60)
    
    ollama = OllamaClient()
    memstore = MemoryStore()
    collector = DataCollector(ollama, memstore)
    
    test_cases = [
        {
            "message": "PT Maju Jaya",
            "expected_company": True,
            "description": "PT dengan spasi"
        },
        {
            "message": "PT. Maju Jaya",
            "expected_company": True,
            "description": "PT dengan titik"
        },
        {
            "message": "CV Berkah Sejahtera",
            "expected_company": True,
            "description": "CV"
        },
        {
            "message": "UD Sumber Rezeki",
            "expected_company": True,
            "description": "UD"
        },
        {
            "message": "Budi Santoso",
            "expected_company": False,
            "description": "Nama personal"
        },
        {
            "message": "Siti Aminah",
            "expected_company": False,
            "description": "Nama personal female"
        },
        {
            "message": "Ahmad",
            "expected_company": False,
            "description": "Nama pendek"
        }
    ]
    
    print("\n")
    for i, test in enumerate(test_cases, 1):
        print(f"Test {i}: {test['description']}")
        print(f"  Input: '{test['message']}'")
        
        result = collector.extract_name_and_gender_via_llm(f"test_user_{i}", test['message'])
        
        is_company = result.get("is_company", False)
        name = result.get("name", "")
        gender = result.get("gender", "unknown")
        
        print(f"  Output:")
        print(f"    - Name: {name}")
        print(f"    - Gender: {gender}")
        print(f"    - Is Company: {is_company}")
        
        if is_company == test["expected_company"]:
            print(f"  ✅ PASSED")
        else:
            print(f"  ❌ FAILED - Expected is_company={test['expected_company']}, got {is_company}")
        
        print()

if __name__ == "__main__":
    test_company_name_extraction()
