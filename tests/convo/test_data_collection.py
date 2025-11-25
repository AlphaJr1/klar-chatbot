
import sys
import os
from typing import Dict, Any, List

BASE = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if os.path.join(BASE, "src") not in sys.path:
    sys.path.insert(0, os.path.join(BASE, "src"))

from src.convo.data_collector import DataCollector
from src.convo.memory_store import MemoryStore
from src.convo.ollama_client import OllamaClient

class CustomerSimulator:
    
    def __init__(self, ollama_client):
        self.ollama = ollama_client
        self.persona = None
        self.scenario = None
    
    def set_scenario(self, scenario: Dict[str, Any]):
        self.scenario = scenario
        self.persona = scenario.get("personality", "cooperative")
    
    def respond(self, bot_question: str, context: str = "") -> str:
        
        if not self.scenario:
            return "Halo, EAC saya bermasalah"
        
        system_msg = f"""
        Kamu adalah customer bernama {self.scenario['name']} yang sedang chat dengan CS.
        
        Data dirimu:
        - Nama: {self.scenario['name']}
        - Gender: {self.scenario['gender']}
        - Produk: {self.scenario['product']}
        - Alamat: {self.scenario['address']}
        
        Personality: {self.persona}
        
        Aturan:
        - Jawab dengan natural seperti customer Indonesia
        - Jangan terlalu formal
        - Bisa pakai bahasa santai
        - Maksimal 1-2 kalimat per respons
        Pertanyaan CS: "{bot_question}"
        
        Konteks: {context}
        
        Behavior khusus:
    
    def __init__(self):
        self.memstore = MemoryStore(autosave=False, debug=True)
        self.ollama = OllamaClient()
        self.collector = DataCollector(self.ollama, self.memstore)
        self.customer = CustomerSimulator(self.ollama)
    
    def run_scenario(self, scenario: Dict[str, Any], max_turns: int = 20) -> Dict[str, Any]:
        
        user_id = f"test_{scenario['name'].replace(' ', '_').lower()}"
        
        # Create user if not exists
        try:
            self.memstore._get_or_create(user_id)
        except Exception as e:
            print(f"Error creating user: {e}")
            return {
                "success": False,
                "turns": 0,
                "conversation": [],
                "final_data": {},
                "issues": [{"issue": "user_creation_failed", "error": str(e)}]
            }
        
        self.customer.set_scenario(scenario)
        
        conversation = []
        issues = []
        
        initial_message = "Halo, EAC saya bermasalah"
        conversation.append({"role": "customer", "text": initial_message})
        
        self.memstore.set_flag(user_id, "sop_pending", True)
        
        first_question = self.collector.generate_question(user_id, "name")
        conversation.append({"role": "bot", "text": first_question})
        
        print(f"\n{'='*60}")
        print(f"SKENARIO: {scenario['name']} ({scenario.get('personality', 'cooperative')})")
        print(f"{'='*60}\n")
        
        print(f"Customer: {initial_message}")
        print(f"Bot: {first_question}\n")
        
        for turn in range(max_turns):
            bot_last_message = conversation[-1]["text"] if conversation else ""
            
            customer_response = self.customer.respond(
                bot_last_message,
                context=f"Turn {turn+1}"
            )
            
            conversation.append({"role": "customer", "text": customer_response})
            print(f"Customer: {customer_response}")
            
            result = self.collector.process_message(user_id, customer_response)
            
            if result["action"] == "off_topic":
                off_topic_info = result["off_topic_info"]
                
                if off_topic_info["should_answer_first"]:
                    generic_answer = "Baik, nanti teknisi kami akan jelaskan lebih detail."
                    print(f"Bot: {generic_answer}")
                    conversation.append({"role": "bot", "text": generic_answer})
                
                return_message = self.collector.generate_return_to_data_message(
                    user_id,
                    off_topic_info["missing_field"]
                )
                
                print(f"Bot: {return_message}")
                conversation.append({"role": "bot", "text": return_message})
                
                continue
            
            if result["response"]:
                print(f"Bot: {result['response']}\n")
                conversation.append({"role": "bot", "text": result["response"]})
            
            if result["is_complete"]:
                print(f"✅ Data collection SELESAI dalam {turn+1} turns")
                break
            
            if result["action"] == "incomplete_address":
                issues.append({
                    "turn": turn+1,
                    "issue": "incomplete_address",
                    "validation": result.get("validation_result")
                })
            
            if result["action"] == "invalid_product":
                issues.append({
                    "turn": turn+1,
                    "issue": "invalid_product"
                })
        
        else:
            print(f"⚠️  Max turns reached ({max_turns})")
            issues.append({"issue": "max_turns_reached"})
        
        final_state = self.collector.get_collection_state(user_id)
        
        print(f"\n{'='*60}")
        print("HASIL AKHIR:")
        print(f"{'='*60}")
        print(f"Nama: {final_state['name']}")
        print(f"Gender: {final_state['gender']}")
        print(f"Produk: {final_state['product']}")
        print(f"Alamat: {final_state['address']}")
        print(f"Jabodetabek: {final_state['is_jabodetabek']}")
        print(f"Complete: {final_state['is_complete']}")
        print(f"Total turns: {len([c for c in conversation if c['role'] == 'customer'])}")
        print(f"Issues: {len(issues)}")
        
        return {
            "success": final_state["is_complete"],
            "turns": len([c for c in conversation if c["role"] == "customer"]),
            "conversation": conversation,
            "final_data": final_state,
            "issues": issues
        }

def main():
    
    scenarios = [
        {
            "name": "Budi Santoso",
            "gender": "male",
            "product": "F57A",
            "address": "Jl. Sudirman No. 123, RT 05/RW 02, Kebayoran Baru, Jakarta Selatan 12190",
            "personality": "cooperative",
            "behavior": {
                "gives_incomplete_address_first": False,
                "asks_questions_during_collection": False,
                "gives_wrong_product_first": False
            }
        },
        {
            "name": "Siti Nurhaliza",
            "gender": "female",
            "product": "F90A",
            "address": "Komplek Griya Asri Blok C No. 15, Cimanggis, Depok, Jawa Barat",
            "personality": "cooperative",
            "behavior": {
                "gives_incomplete_address_first": True,
                "asks_questions_during_collection": False,
                "gives_wrong_product_first": False
            }
        },
        {
            "name": "Ahmad Hidayat",
            "gender": "male",
            "product": "F57A",
            "address": "Ruko Sentra Niaga Blok A-12, BSD City, Tangerang Selatan",
            "personality": "confused",
            "behavior": {
                "gives_incomplete_address_first": False,
                "asks_questions_during_collection": True,
                "gives_wrong_product_first": True
            }
        },
        {
            "name": "Dewi Lestari",
            "gender": "female",
            "product": "F90A",
            "address": "Jl. Raya Bogor KM 25, Cibubur, Jakarta Timur",
            "personality": "difficult",
            "behavior": {
                "gives_incomplete_address_first": True,
                "asks_questions_during_collection": True,
                "gives_wrong_product_first": False
            }
        }
    ]
    
    tester = DataCollectionTester()
    
    results = []
    
    for scenario in scenarios:
        result = tester.run_scenario(scenario, max_turns=15)
        results.append(result)
        
        input("\nTekan ENTER untuk lanjut ke skenario berikutnya...")
    
    print(f"\n\n{'='*60}")
    print("RINGKASAN SEMUA SKENARIO")
    print(f"{'='*60}\n")
    
    for i, (scenario, result) in enumerate(zip(scenarios, results), 1):
        status = "✅ SUCCESS" if result["success"] else "❌ FAILED"
        print(f"{i}. {scenario['name']} ({scenario['personality']}): {status}")
        print(f"   Turns: {result['turns']}, Issues: {len(result['issues'])}")
    
    success_rate = sum(1 for r in results if r["success"]) / len(results) * 100
    print(f"\nSuccess Rate: {success_rate:.1f}%")

if __name__ == "__main__":
    main()
