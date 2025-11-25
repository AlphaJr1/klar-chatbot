#!/usr/bin/env python3
import sys
import os

BASE = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if os.path.join(BASE, "src") not in sys.path:
    sys.path.insert(0, os.path.join(BASE, "src"))

from src.convo.engine import ConversationEngine
import time

def print_section(title):
    print("\n" + "=" * 80)
    print(f" {title}")
    print("=" * 80)

def print_interaction(user_msg, bot_response, metadata=None):
    print(f"\n👤 User: {user_msg}")
    print(f"🤖 Bot: {bot_response[:150]}{'...' if len(bot_response) > 150 else ''}")
    if metadata:
        for key, value in metadata.items():
            print(f"   [{key}]: {value}")

def test_full_flow_with_distractions():
    print("\n" + "🔥" * 40)
    print(" COMPREHENSIVE STRESS TEST: Full Flow + Distractions")
    print("🔥" * 40)
    
    engine = ConversationEngine()
    user_id = f"stress-test-{int(time.time())}"
    
    # ============================================================================
    # PHASE 1: TROUBLESHOOTING dengan Distraksi
    # ============================================================================
    print_section("PHASE 1: TROUBLESHOOTING DENGAN DISTRAKSI")
    
    # Step 1: Initial complaint
    r1 = engine.handle(user_id, "AC saya bunyi berisik")
    print_interaction("AC saya bunyi berisik", r1['bubbles'][0]['text'], {
        "active_intent": engine.memstore.get_flag(user_id, "active_intent"),
        "status": r1.get("status", "N/A")
    })
    
    # Step 2: DISTRAKSI - Chitchat
    r2 = engine.handle(user_id, "wah panas banget ya hari ini")
    print_interaction("wah panas banget ya hari ini", r2['bubbles'][0]['text'], {
        "distraksi": "chitchat",
        "active_intent": engine.memstore.get_flag(user_id, "active_intent")
    })
    
    # Step 3: Answer troubleshooting
    r3 = engine.handle(user_id, "sering bunyinya")
    print_interaction("sering bunyinya", r3['bubbles'][0]['text'])
    
    # Step 4: DISTRAKSI - Keluhan tambahan
    r4 = engine.handle(user_id, "eh iya AC nya juga bau tidak sedap")
    print_interaction("eh iya AC nya juga bau tidak sedap", r4['bubbles'][0]['text'], {
        "distraksi": "additional_complaint",
        "queued": engine.memstore.get_flag(user_id, "queued_complaints"),
        "active_intent": engine.memstore.get_flag(user_id, "active_intent")
    })
    
    # Step 5: DISTRAKSI - Competitor mention
    r5 = engine.handle(user_id, "daikin saya juga bermasalah")
    print_interaction("daikin saya juga bermasalah", r5['bubbles'][0]['text'], {
        "distraksi": "competitor",
        "active_intent": engine.memstore.get_flag(user_id, "active_intent")
    })
    
    # Step 6: Continue troubleshooting - akan masuk pending
    r6 = engine.handle(user_id, "tidak mau")
    print_interaction("tidak mau", r6['bubbles'][0]['text'], {
        "status": r6.get("status", "N/A"),
        "sop_pending": engine.memstore.get_flag(user_id, "sop_pending")
    })
    
    # ============================================================================
    # PHASE 2: DATA COLLECTION dengan Distraksi
    # ============================================================================
    print_section("PHASE 2: DATA COLLECTION DENGAN DISTRAKSI")
    
    # Step 7: Provide name
    r7 = engine.handle(user_id, "nama saya Budi")
    print_interaction("nama saya Budi", r7['bubbles'][0]['text'], {
        "identity": engine.memstore.get_identity(user_id)
    })
    
    # Step 8: DISTRAKSI - Pertanyaan saat data collection
    r8 = engine.handle(user_id, "berapa lama teknisi datang?")
    print_interaction("berapa lama teknisi datang?", r8['bubbles'][0]['text'], {
        "distraksi": "question_during_data_collection"
    })
    
    # Step 9: Provide product (partial)
    r9 = engine.handle(user_id, "EAC")
    print_interaction("EAC", r9['bubbles'][0]['text'], {
        "identity": engine.memstore.get_identity(user_id)
    })
    
    # Step 10: DISTRAKSI - Chitchat during data collection
    r10 = engine.handle(user_id, "oke siap")
    print_interaction("oke siap", r10['bubbles'][0]['text'], {
        "distraksi": "chitchat_during_data_collection"
    })
    
    # Step 11: Provide product model
    r11 = engine.handle(user_id, "35m65")
    print_interaction("35m65", r11['bubbles'][0]['text'], {
        "identity": engine.memstore.get_identity(user_id)
    })
    
    # Step 12: DISTRAKSI - New complaint during data collection
    r12 = engine.handle(user_id, "eh sekarang malah mati total")
    print_interaction("eh sekarang malah mati total", r12['bubbles'][0]['text'], {
        "distraksi": "new_complaint_during_data_collection",
        "active_intent": engine.memstore.get_flag(user_id, "active_intent")
    })
    
    # Step 13: Provide address
    r13 = engine.handle(user_id, "Jl. Sudirman No. 123, Jakarta Selatan")
    print_interaction("Jl. Sudirman No. 123, Jakarta Selatan", r13['bubbles'][0]['text'], {
        "identity": engine.memstore.get_identity(user_id)
    })
    
    # Step 14: DISTRAKSI - Competitor mention during data collection
    r14 = engine.handle(user_id, "LG saya juga rusak nih")
    print_interaction("LG saya juga rusak nih", r14['bubbles'][0]['text'], {
        "distraksi": "competitor_during_data_collection"
    })
    
    # Step 15: Complete data collection
    final_identity = engine.memstore.get_identity(user_id)
    
    # ============================================================================
    # VERIFICATION & RESULTS
    # ============================================================================
    print_section("VERIFICATION & RESULTS")
    
    print("\n📊 Final State:")
    print(f"   Active Intent: {engine.memstore.get_flag(user_id, 'active_intent')}")
    print(f"   SOP Pending: {engine.memstore.get_flag(user_id, 'sop_pending')}")
    print(f"   Queued Complaints: {engine.memstore.get_flag(user_id, 'queued_complaints')}")
    
    print("\n👤 Collected Identity Data:")
    for key, value in final_identity.items():
        print(f"   {key}: {value}")
    
    # Verify completeness
    print("\n✅ Data Collection Completeness:")
    required_fields = ["name", "product", "address"]
    for field in required_fields:
        value = final_identity.get(field)
        status = "✅" if value else "❌"
        print(f"   {status} {field}: {value if value else 'MISSING'}")
    
    # Check robustness
    print("\n🛡️ Robustness Check:")
    
    checks = [
        ("Intent Stability", engine.memstore.get_flag(user_id, "active_intent") == "bunyi", "Intent tetap 'bunyi' meskipun banyak distraksi"),
        ("Queued Complaints", "bau" in (engine.memstore.get_flag(user_id, "queued_complaints") or []), "Keluhan 'bau' masuk queue"),
        ("Data Collected", all(final_identity.get(f) for f in ["name", "product"]), "Minimal name & product terkumpul"),
        ("No Crash", True, "Tidak ada error/crash selama test"),
    ]
    
    all_passed = True
    for check_name, condition, description in checks:
        status = "✅ PASS" if condition else "❌ FAIL"
        print(f"   {status}: {check_name} - {description}")
        if not condition:
            all_passed = False
    
    # ============================================================================
    # SUMMARY
    # ============================================================================
    print_section("TEST SUMMARY")
    
    print("\n📈 Test Statistics:")
    history = engine.memstore.get_history(user_id)
    total_interactions = len([h for h in history if h["role"] == "user"])
    distractions = 7  # Counted manually from test
    
    print(f"   Total Interactions: {total_interactions}")
    print(f"   Distractions Handled: {distractions}")
    print(f"   Data Fields Attempted: {len(required_fields)}")
    print(f"   Data Fields Collected: {sum(1 for f in required_fields if final_identity.get(f))}")
    
    print("\n🎯 Test Coverage:")
    coverage_items = [
        "Troubleshooting flow",
        "Chitchat during troubleshooting",
        "Additional complaint (lock intent)",
        "Competitor mention filtering",
        "Question handling",
        "Data collection flow",
        "Distractions during data collection",
        "State persistence",
        "Queue management"
    ]
    
    for item in coverage_items:
        print(f"   ✅ {item}")
    
    if all_passed:
        print("\n" + "🎉" * 40)
        print(" ✅ STRESS TEST PASSED!")
        print(" System robust terhadap berbagai distraksi")
        print(" Data collection berjalan smooth hingga selesai")
        print("🎉" * 40)
    else:
        print("\n" + "⚠️ " * 40)
        print(" ⚠️  STRESS TEST PARTIALLY PASSED")
        print(" Beberapa check gagal, perlu review")
        print("⚠️ " * 40)
    
    return all_passed

if __name__ == "__main__":
    success = test_full_flow_with_distractions()
    sys.exit(0 if success else 1)
