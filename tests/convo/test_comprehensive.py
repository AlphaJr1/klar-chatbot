
import sys
import os
import time
import traceback
import tempfile
from typing import Dict, List, Any

BASE = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if os.path.join(BASE, "src") not in sys.path:
    sys.path.insert(0, os.path.join(BASE, "src"))

from src.convo.data_collector import DataCollector
from src.convo.memory_store import MemoryStore
from src.convo.ollama_client import OllamaClient

class TestMetrics:
    
    def __init__(self):
        self.tests = []
        self.start_time = None
        self.end_time = None
    
    def start(self):
        self.start_time = time.time()
    
    def end(self):
        self.end_time = time.time()
    
    def add_test(self, name: str, passed: bool, turns: int, duration: float, details: Dict[str, Any]):
        self.tests.append({
            "name": name,
            "passed": passed,
            "turns": turns,
            "duration": duration,
            "details": details
        })
    
    def get_summary(self) -> Dict[str, Any]:
        total = len(self.tests)
        passed = sum(1 for t in self.tests if t["passed"])
        
        avg_turns = sum(t["turns"] for t in self.tests) / total if total > 0 else 0
        avg_duration = sum(t["duration"] for t in self.tests) / total if total > 0 else 0
        
        return {
            "total_tests": total,
            "passed": passed,
            "failed": total - passed,
            "success_rate": (passed / total * 100) if total > 0 else 0,
            "avg_turns": avg_turns,
            "avg_duration": avg_duration,
            "total_duration": self.end_time - self.start_time if self.end_time and self.start_time else 0
        }

def create_test_collector():
    temp_file = tempfile.mktemp(suffix=".json")
    memstore = MemoryStore(path=temp_file, autosave=False, debug=False)
    collector = DataCollector(OllamaClient(), memstore)
    return collector, memstore, temp_file

def cleanup_test(temp_file):
    try:
        if os.path.exists(temp_file):
            os.unlink(temp_file)
    except:
        pass

def run_test(name: str, test_func, metrics: TestMetrics):
    print(f"\n{'='*60}")
    print(f"TEST: {name}")
    print(f"{'='*60}\n")
    
    start = time.time()
    
    try:
        result = test_func()
        duration = time.time() - start
        
        metrics.add_test(
            name=name,
            passed=result["passed"],
            turns=result.get("turns", 0),
            duration=duration,
            details=result.get("details", {})
        )
        
        status = "✅ PASSED" if result["passed"] else "❌ FAILED"
        print(f"\n{status} - {name}")
        print(f"Turns: {result.get('turns', 0)}, Duration: {duration:.2f}s")
        
        return result["passed"]
        
    except Exception as e:
        duration = time.time() - start
        print(f"\n❌ EXCEPTION: {e}")
        traceback.print_exc()
        
        metrics.add_test(
            name=name,
            passed=False,
            turns=0,
            duration=duration,
            details={"error": str(e)}
        )
        
        return False

def test_happy_path_male():
    collector, memstore, temp_file = create_test_collector()
    
    user_id = "test_happy_male"
    memstore.set_flag(user_id, "sop_pending", True)
    
    turns = 0
    
    try:
        result = collector.process_message(user_id, "Budi Santoso")
        turns += 1
        assert result["action"] == "name_saved_ask_next", f"Expected 'name_saved_ask_next' but got '{result['action']}'"
        
        result = collector.process_message(user_id, "F57A")
        turns += 1
        assert result["action"] == "product_saved_ask_next", f"Expected 'product_saved_ask_next' but got '{result['action']}'"
        
        result = collector.process_message(user_id, "Jl. Sudirman 123, Jakarta Selatan")
        turns += 1
        assert result["action"] == "complete", f"Expected 'complete' but got '{result['action']}'"
        
        state = collector.get_collection_state(user_id)
        
        return {
            "passed": state["is_complete"] and state["gender"] == "male",
            "turns": turns,
            "details": state
        }
    finally:
        cleanup_test(temp_file)

def test_happy_path_female():
    collector, memstore, temp_file = create_test_collector()
    
    user_id = "test_happy_female"
    memstore.set_flag(user_id, "sop_pending", True)
    
    turns = 0
    
    try:
        result = collector.process_message(user_id, "Siti Nurhaliza")
        turns += 1
        assert result["action"] == "name_saved_ask_next"
        
        result = collector.process_message(user_id, "F90A")
        turns += 1
        assert result["action"] == "product_saved_ask_next"
        
        result = collector.process_message(user_id, "Jl. Raya Bogor KM 25, Depok")
        turns += 1
        assert result["action"] == "complete"
        
        state = collector.get_collection_state(user_id)
        
        return {
            "passed": state["is_complete"] and state["gender"] == "female",
            "turns": turns,
            "details": state
        }
    finally:
        cleanup_test(temp_file)

def test_invalid_product_retry():
    collector, memstore, temp_file = create_test_collector()
    
    user_id = "test_invalid_product"
    memstore.set_flag(user_id, "sop_pending", True)
    
    turns = 0
    
    try:
        result = collector.process_message(user_id, "Ahmad Hidayat")
        turns += 1
        
        result = collector.process_message(user_id, "F60A")
        turns += 1
        assert result["action"] == "ask_product", f"Expected 'ask_product' but got '{result['action']}'"
        
        result = collector.process_message(user_id, "F57A")
        turns += 1
        assert result["action"] == "product_saved_ask_next"
        
        result = collector.process_message(user_id, "Jl. Gatot Subroto 100, Jakarta Pusat")
        turns += 1
        
        state = collector.get_collection_state(user_id)
        
        return {
            "passed": state["is_complete"] and state["product"] == "F57A",
            "turns": turns,
            "details": state
        }
    finally:
        cleanup_test(temp_file)

def test_incomplete_address_retry():
    collector, memstore, temp_file = create_test_collector()
    
    user_id = "test_incomplete_addr"
    memstore.set_flag(user_id, "sop_pending", True)
    
    turns = 0
    
    try:
        result = collector.process_message(user_id, "Dewi Lestari")
        turns += 1
        
        result = collector.process_message(user_id, "F90A")
        turns += 1
        
        result = collector.process_message(user_id, "Jl. Sudirman")
        turns += 1
        assert result["action"] == "incomplete_address", f"Expected 'incomplete_address' but got '{result['action']}'"
        
        result = collector.process_message(user_id, "Jl. Sudirman 123, Tangerang Selatan")
        turns += 1
        assert result["action"] == "complete"
        
        state = collector.get_collection_state(user_id)
        
        return {
            "passed": state["is_complete"],
            "turns": turns,
            "details": state
        }
    finally:
        cleanup_test(temp_file)

def test_outside_jabodetabek():
    collector, memstore, temp_file = create_test_collector()
    
    user_id = "test_outside_jabodetabek"
    memstore.set_flag(user_id, "sop_pending", True)
    
    turns = 0
    
    try:
        result = collector.process_message(user_id, "Andi Wijaya")
        turns += 1
        
        result = collector.process_message(user_id, "F57A")
        turns += 1
        
        result = collector.process_message(user_id, "Jl. Raya Bandung 100, Bandung, Jawa Barat")
        turns += 1
        
        state = collector.get_collection_state(user_id)
        
        return {
            "passed": state["is_complete"] and state["is_jabodetabek"] == False,
            "turns": turns,
            "details": state
        }
    finally:
        cleanup_test(temp_file)

def test_unknown_gender():
    collector, memstore, temp_file = create_test_collector()
    
    user_id = "test_unknown_gender"
    memstore.set_flag(user_id, "sop_pending", True)
    
    turns = 0
    
    try:
        result = collector.process_message(user_id, "Alex Jordan")
        turns += 1
        
        result = collector.process_message(user_id, "F90A")
        turns += 1
        
        result = collector.process_message(user_id, "Jl. Kebon Jeruk 50, Jakarta Barat")
        turns += 1
        
        state = collector.get_collection_state(user_id)
        
        return {
            "passed": state["is_complete"] and state["gender"] == "unknown",
            "turns": turns,
            "details": state
        }
    finally:
        cleanup_test(temp_file)

def test_case_insensitive_product():
    collector, memstore, temp_file = create_test_collector()
    
    user_id = "test_case_product"
    memstore.set_flag(user_id, "sop_pending", True)
    
    turns = 0
    
    try:
        result = collector.process_message(user_id, "Rizki Fauzi")
        turns += 1
        
        result = collector.process_message(user_id, "f57a")
        turns += 1
        assert result["action"] == "product_saved_ask_next"
        
        result = collector.process_message(user_id, "Komplek Griya Asri, Bekasi")
        turns += 1
        
        state = collector.get_collection_state(user_id)
        
        return {
            "passed": state["is_complete"] and state["product"] == "F57A",
            "turns": turns,
            "details": state
        }
    finally:
        cleanup_test(temp_file)

def test_long_address():
    collector, memstore, temp_file = create_test_collector()
    
    user_id = "test_long_addr"
    memstore.set_flag(user_id, "sop_pending", True)
    
    turns = 0
    
    try:
        result = collector.process_message(user_id, "Fajar Kurniawan")
        turns += 1
        
        result = collector.process_message(user_id, "F90A")
        turns += 1
        
        result = collector.process_message(user_id, "Jl. Raya Margonda No. 123, RT 05/RW 02, Kelurahan Kemiri Muka, Kecamatan Beji, Kota Depok, Jawa Barat 16423")
        turns += 1
        
        state = collector.get_collection_state(user_id)
        
        return {
            "passed": state["is_complete"] and state["is_jabodetabek"] == True,
            "turns": turns,
            "details": state
        }
    finally:
        cleanup_test(temp_file)

def main():
    
    print("\n")
    print("╔" + "="*58 + "╗")
    print("║" + " "*8 + "COMPREHENSIVE DATA COLLECTION TEST" + " "*16 + "║")
    print("╚" + "="*58 + "╝")
    
    metrics = TestMetrics()
    metrics.start()
    
    tests = [
        ("Happy Path - Male Name", test_happy_path_male),
        ("Happy Path - Female Name", test_happy_path_female),
        ("Invalid Product Retry", test_invalid_product_retry),
        ("Incomplete Address Retry", test_incomplete_address_retry),
        ("Outside Jabodetabek", test_outside_jabodetabek),
        ("Unknown Gender", test_unknown_gender),
        ("Case Insensitive Product", test_case_insensitive_product),
        ("Long Detailed Address", test_long_address),
    ]
    
    results = []
    
    for name, test_func in tests:
        passed = run_test(name, test_func, metrics)
        results.append((name, passed))
    
    metrics.end()
    
    print("\n\n")
    print("="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    for name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{name:35s} {status}")
    
    summary = metrics.get_summary()
    
    print("\n" + "="*60)
    print("METRICS")
    print("="*60)
    print(f"Total Tests: {summary['total_tests']}")
    print(f"Passed: {summary['passed']}")
    print(f"Failed: {summary['failed']}")
    print(f"Success Rate: {summary['success_rate']:.1f}%")
    print(f"Average Turns: {summary['avg_turns']:.1f}")
    print(f"Average Duration: {summary['avg_duration']:.2f}s")
    print(f"Total Duration: {summary['total_duration']:.2f}s")
    
    if summary['success_rate'] == 100:
        print("\n🎉 ALL TESTS PASSED!")
    elif summary['success_rate'] >= 75:
        print(f"\n✅ GOOD - {summary['success_rate']:.0f}% tests passed")
    else:
        print(f"\n⚠️  NEEDS IMPROVEMENT - Only {summary['success_rate']:.0f}% passed")
    
    print()

if __name__ == "__main__":
    main()
