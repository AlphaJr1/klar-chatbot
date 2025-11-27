#!/usr/bin/env python3
"""
Stress Test untuk Troubleshooting Flow via API Endpoint
Server: http://localhost:8081
"""

import requests
import json
import time
from typing import Dict, Any, List
from datetime import datetime

BASE_URL = "http://localhost:8081"
CHAT_ENDPOINT = f"{BASE_URL}/chat"

class Color:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_header(text: str):
    print(f"\n{Color.HEADER}{Color.BOLD}{'='*70}{Color.END}")
    print(f"{Color.HEADER}{Color.BOLD}{text.center(70)}{Color.END}")
    print(f"{Color.HEADER}{Color.BOLD}{'='*70}{Color.END}\n")

def print_step(step_num: int, description: str):
    print(f"{Color.CYAN}{Color.BOLD}[Step {step_num}] {description}{Color.END}")

def print_user_message(message: str):
    print(f"{Color.BLUE}User: {message}{Color.END}")

def print_bot_response(response: str):
    print(f"{Color.GREEN}Bot:  {response}{Color.END}")

def print_status(status: str, next_action: str):
    print(f"{Color.YELLOW}Status: {status} | Next: {next_action}{Color.END}")

def print_success(message: str):
    print(f"{Color.GREEN}✓ {message}{Color.END}")

def print_error(message: str):
    print(f"{Color.RED}✗ {message}{Color.END}")

def send_message(user_id: str, text: str) -> Dict[str, Any]:
    """Kirim pesan ke endpoint /chat"""
    payload = {
        "user_id": user_id,
        "text": text
    }
    
    try:
        response = requests.post(CHAT_ENDPOINT, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print_error(f"Request failed: {e}")
        return {}

def reset_memory(user_id: str, secret: str = "dev_reset_2024"):
    """Reset memory user"""
    try:
        response = requests.post(
            f"{BASE_URL}/admin/reset-memory",
            params={"user_id": user_id, "secret": secret},
            timeout=10
        )
        response.raise_for_status()
        print_success(f"Memory reset untuk {user_id}")
    except Exception as e:
        print_error(f"Reset memory failed: {e}")

def extract_response_text(result: Dict[str, Any]) -> str:
    """Ekstrak text dari bubbles"""
    bubbles = result.get("bubbles", [])
    if bubbles:
        return " | ".join([b.get("text", "") for b in bubbles if b.get("text")])
    return ""

def test_mati_flow_success(user_id: str):
    """Test alur troubleshooting MATI - berhasil diselesaikan"""
    print_header("TEST 1: MATI FLOW - SUCCESS (Resolved)")
    
    reset_memory(user_id)
    time.sleep(0.5)
    
    # Step 1: Keluhan awal
    print_step(1, "User melaporkan alat mati")
    result = send_message(user_id, "Halo, EAC saya mati")
    response = extract_response_text(result)
    print_user_message("Halo, EAC saya mati")
    print_bot_response(response)
    print_status(result.get("status", ""), result.get("next", ""))
    time.sleep(1)
    
    # Step 2: Jawab ya untuk cover rapat
    print_step(2, "User jawab: sudah rapat covernya")
    result = send_message(user_id, "sudah rapat")
    response = extract_response_text(result)
    print_user_message("sudah rapat")
    print_bot_response(response)
    print_status(result.get("status", ""), result.get("next", ""))
    time.sleep(1)
    
    # Step 3: Coba tombol LOW - berhasil menyala
    print_step(3, "User lapor: sudah menyala setelah tekan LOW")
    result = send_message(user_id, "sudah menyala kak")
    response = extract_response_text(result)
    print_user_message("sudah menyala kak")
    print_bot_response(response)
    print_status(result.get("status", ""), result.get("next", ""))
    
    if result.get("status") == "resolved":
        print_success("✓ Case RESOLVED successfully!")
    else:
        print_error(f"✗ Expected 'resolved' but got '{result.get('status')}'")

def test_mati_flow_pending(user_id: str):
    """Test alur troubleshooting MATI - perlu teknisi"""
    print_header("TEST 2: MATI FLOW - PENDING (Need Technician)")
    
    reset_memory(user_id)
    time.sleep(0.5)
    
    # Step 1: Keluhan awal
    print_step(1, "User melaporkan alat mati")
    result = send_message(user_id, "EAC saya tidak menyala")
    response = extract_response_text(result)
    print_user_message("EAC saya tidak menyala")
    print_bot_response(response)
    time.sleep(1)
    
    # Step 2: Cover sudah rapat
    print_step(2, "Cover sudah rapat")
    result = send_message(user_id, "sudah rapat")
    response = extract_response_text(result)
    print_user_message("sudah rapat")
    print_bot_response(response)
    time.sleep(1)
    
    # Step 3: Tombol LOW tidak berhasil
    print_step(3, "Tombol LOW tidak berhasil")
    result = send_message(user_id, "masih tidak menyala")
    response = extract_response_text(result)
    print_user_message("masih tidak menyala")
    print_bot_response(response)
    time.sleep(1)
    
    # Step 4: MCB sudah ON tapi tetap mati
    print_step(4, "MCB sudah ON tapi masih mati")
    result = send_message(user_id, "MCB sudah ON tapi tetap tidak nyala")
    response = extract_response_text(result)
    print_user_message("MCB sudah ON tapi tetap tidak nyala")
    print_bot_response(response)
    print_status(result.get("status", ""), result.get("next", ""))
    
    if result.get("status") == "open" and "pending" in result.get("next", "").lower():
        print_success("✓ Case escalated to PENDING (data collection)")
    
    # Step 5: Data collection - Nama
    print_step(5, "Mengisi data - Nama")
    result = send_message(user_id, "Budi Santoso")
    response = extract_response_text(result)
    print_user_message("Budi Santoso")
    print_bot_response(response)
    time.sleep(0.5)
    
    # Step 6: Data collection - Produk
    print_step(6, "Mengisi data - Produk")
    result = send_message(user_id, "F57A")
    response = extract_response_text(result)
    print_user_message("F57A")
    print_bot_response(response)
    time.sleep(0.5)
    
    # Step 7: Data collection - Alamat
    print_step(7, "Mengisi data - Alamat")
    result = send_message(user_id, "Jl. Sudirman No. 123, Jakarta Selatan")
    response = extract_response_text(result)
    print_user_message("Jl. Sudirman No. 123, Jakarta Selatan")
    print_bot_response(response)
    print_status(result.get("status", ""), result.get("next", ""))
    
    if result.get("status") == "pending":
        print_success("✓ Data collection COMPLETE - Case PENDING")

def test_bau_flow(user_id: str):
    """Test alur troubleshooting BAU"""
    print_header("TEST 3: BAU FLOW - Pending for Filter Replacement")
    
    reset_memory(user_id)
    time.sleep(0.5)
    
    # Step 1: Keluhan bau
    print_step(1, "User melaporkan bau tidak sedap")
    result = send_message(user_id, "EAC saya mengeluarkan bau tidak sedap")
    response = extract_response_text(result)
    print_user_message("EAC saya mengeluarkan bau tidak sedap")
    print_bot_response(response)
    time.sleep(1)
    
    # Step 2: Setuju untuk jadwal teknisi
    print_step(2, "User setuju jadwal teknisi")
    result = send_message(user_id, "Ya, tolong jadwalkan")
    response = extract_response_text(result)
    print_user_message("Ya, tolong jadwalkan")
    print_bot_response(response)
    print_status(result.get("status", ""), result.get("next", ""))
    
    # Step 3: Isi nama
    print_step(3, "Mengisi nama")
    result = send_message(user_id, "Siti Nurhaliza")
    response = extract_response_text(result)
    print_user_message("Siti Nurhaliza")
    print_bot_response(response)
    time.sleep(0.5)
    
    # Step 4: Isi produk
    print_step(4, "Mengisi produk")
    result = send_message(user_id, "F90A")
    response = extract_response_text(result)
    print_user_message("F90A")
    print_bot_response(response)
    time.sleep(0.5)
    
    # Step 5: Isi alamat
    print_step(5, "Mengisi alamat")
    result = send_message(user_id, "Jl. Gatot Subroto KM 25, Depok")
    response = extract_response_text(result)
    print_user_message("Jl. Gatot Subroto KM 25, Depok")
    print_bot_response(response)
    print_status(result.get("status", ""), result.get("next", ""))

def test_bunyi_jarang_resolved(user_id: str):
    """Test alur BUNYI - jarang (resolved)"""
    print_header("TEST 4: BUNYI FLOW - JARANG (Resolved)")
    
    reset_memory(user_id)
    time.sleep(0.5)
    
    # Step 1: Keluhan bunyi
    print_step(1, "User melaporkan bunyi aneh")
    result = send_message(user_id, "EAC saya berbunyi aneh")
    response = extract_response_text(result)
    print_user_message("EAC saya berbunyi aneh")
    print_bot_response(response)
    time.sleep(1)
    
    # Step 2: Bunyi jarang
    print_step(2, "User jawab: bunyi jarang")
    result = send_message(user_id, "jarang, sesekali saja")
    response = extract_response_text(result)
    print_user_message("jarang, sesekali saja")
    print_bot_response(response)
    print_status(result.get("status", ""), result.get("next", ""))
    
    if result.get("status") == "resolved":
        print_success("✓ Case RESOLVED - Bunyi jarang masih normal")

def test_bunyi_sering_pending(user_id: str):
    """Test alur BUNYI - sering (pending)"""
    print_header("TEST 5: BUNYI FLOW - SERING (Pending)")
    
    reset_memory(user_id)
    time.sleep(0.5)
    
    # Step 1: Keluhan bunyi
    print_step(1, "User melaporkan bunyi berisik")
    result = send_message(user_id, "EAC berisik sekali")
    response = extract_response_text(result)
    print_user_message("EAC berisik sekali")
    print_bot_response(response)
    time.sleep(1)
    
    # Step 2: Bunyi sering
    print_step(2, "User jawab: bunyi sering")
    result = send_message(user_id, "sering banget, terus-terusan")
    response = extract_response_text(result)
    print_user_message("sering banget, terus-terusan")
    print_bot_response(response)
    print_status(result.get("status", ""), result.get("next", ""))
    
    # Data collection
    print_step(3, "Mengisi data - Ahmad")
    result = send_message(user_id, "Ahmad")
    print_user_message("Ahmad")
    print_bot_response(extract_response_text(result))
    time.sleep(0.5)
    
    result = send_message(user_id, "F57A")
    print_user_message("F57A")
    print_bot_response(extract_response_text(result))
    time.sleep(0.5)
    
    result = send_message(user_id, "Komplek Griya Asri Blok A5, Bekasi")
    print_user_message("Komplek Griya Asri Blok A5, Bekasi")
    print_bot_response(extract_response_text(result))
    print_status(result.get("status", ""), result.get("next", ""))

def test_distraction_handling(user_id: str):
    """Test handling distraction during troubleshooting"""
    print_header("TEST 6: DISTRACTION HANDLING")
    
    reset_memory(user_id)
    time.sleep(0.5)
    
    # Step 1: Mulai troubleshooting mati
    print_step(1, "Mulai troubleshooting")
    result = send_message(user_id, "EAC tidak nyala")
    print_user_message("EAC tidak nyala")
    print_bot_response(extract_response_text(result))
    time.sleep(1)
    
    # Step 2: Distraction - chitchat
    print_step(2, "User chitchat (distraction)")
    result = send_message(user_id, "wah panas banget ya hari ini")
    print_user_message("wah panas banget ya hari ini")
    print_bot_response(extract_response_text(result))
    time.sleep(1)
    
    # Step 3: Additional complaint
    print_step(3, "User menyebut keluhan tambahan (bunyi)")
    result = send_message(user_id, "eh iya, EAC nya juga bunyi aneh lho")
    print_user_message("eh iya, EAC nya juga bunyi aneh lho")
    print_bot_response(extract_response_text(result))
    time.sleep(1)
    
    # Step 4: Kembali ke troubleshooting utama
    print_step(4, "Lanjut jawab pertanyaan troubleshooting")
    result = send_message(user_id, "sudah rapat covernya")
    print_user_message("sudah rapat covernya")
    print_bot_response(extract_response_text(result))
    print_status(result.get("status", ""), result.get("next", ""))

def test_explicit_resolution(user_id: str):
    """Test explicit resolution detection"""
    print_header("TEST 7: EXPLICIT RESOLUTION DETECTION")
    
    reset_memory(user_id)
    time.sleep(0.5)
    
    # Step 1: Keluhan
    print_step(1, "User melaporkan mati")
    result = send_message(user_id, "EAC mati total")
    print_user_message("EAC mati total")
    print_bot_response(extract_response_text(result))
    time.sleep(1)
    
    # Step 2: Explicit resolution
    print_step(2, "User bilang sudah menyala kembali (explicit)")
    result = send_message(user_id, "oh wait, sudah menyala kembali kak")
    print_user_message("oh wait, sudah menyala kembali kak")
    print_bot_response(extract_response_text(result))
    print_status(result.get("status", ""), result.get("next", ""))
    
    if result.get("status") == "resolved":
        print_success("✓ Explicit resolution DETECTED correctly")

def run_all_tests():
    """Jalankan semua test"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    print(f"\n{Color.BOLD}{Color.HEADER}")
    print("╔" + "="*68 + "╗")
    print("║" + " STRESS TEST - TROUBLESHOOTING FLOW VIA API ".center(68) + "║")
    print("║" + f" Server: {BASE_URL} ".center(68) + "║")
    print("║" + f" Timestamp: {timestamp} ".center(68) + "║")
    print("╚" + "="*68 + "╝")
    print(f"{Color.END}\n")
    
    # Check server health
    try:
        health = requests.get(f"{BASE_URL}/health", timeout=5).json()
        print_success(f"Server OK - Version: {health.get('version', 'unknown')}")
    except Exception as e:
        print_error(f"Server NOT responding: {e}")
        return
    
    tests = [
        ("test_mati_success_001", test_mati_flow_success),
        ("test_mati_pending_002", test_mati_flow_pending),
        ("test_bau_003", test_bau_flow),
        ("test_bunyi_jarang_004", test_bunyi_jarang_resolved),
        ("test_bunyi_sering_005", test_bunyi_sering_pending),
        ("test_distraction_006", test_distraction_handling),
        ("test_explicit_007", test_explicit_resolution),
    ]
    
    for user_id, test_func in tests:
        try:
            test_func(user_id)
            time.sleep(2)
        except KeyboardInterrupt:
            print(f"\n{Color.RED}Test interrupted by user{Color.END}")
            break
        except Exception as e:
            print_error(f"Test failed: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n{Color.BOLD}{Color.GREEN}")
    print("╔" + "="*68 + "╗")
    print("║" + " ALL TESTS COMPLETED ".center(68) + "║")
    print("╚" + "="*68 + "╝")
    print(f"{Color.END}\n")

if __name__ == "__main__":
    run_all_tests()
