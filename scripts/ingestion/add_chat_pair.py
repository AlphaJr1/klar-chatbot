
import os
import sys
import json
import re
from pathlib import Path

# === Path setup ===
BASE_DIR = Path(__file__).resolve().parent.parent
if BASE_DIR not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from convo.ollama_client import OllamaClient

# Ganti path ke new_chat.txt
CHAT_TXT = BASE_DIR / "kb" / "source" / "new_chat.txt"
CHAT_JSONL = BASE_DIR / "kb" / "compiled" / "chat_pairs.jsonl"

ollama = OllamaClient(model="qwen2.5:7b-instruct")

# =====================================================
# Helpers
# =====================================================
def clean_text(text: str) -> str:
    text = text.lower().strip()
    noise = [
        "selamat pagi", "selamat siang", "selamat sore", "terimakasih", "terima kasih",
        "baik kak", "baik pak", "baik mba", "iya kak", "sama sama", "🙏", "😊",
        "baik", "noted kak", "siap kak"
    ]
    for n in noise:
        text = text.replace(n, "")
    return text.strip()

def trim_non_technical_block(text: str) -> str:
    cut_keywords = ["rekening", "transfer", "biaya", "invoice", "lokasi", "booking", "atas nama"]
    for k in cut_keywords:
        if k in text.lower():
            idx = text.lower().index(k)
            return text[:idx]
    return text

def extract_topic_from_text(text: str) -> str:
    patterns = [
        r"bunyi[^\.\n]*",
        r"suara[^\.\n]*",
        r"lampu[^\.\n]*",
        r"unit[^\.\n]*",
        r"kipas[^\.\n]*",
        r"alat[^\.\n]*",
    ]
    for p in patterns:
        match = re.search(p, text.lower())
        if match:
            return match.group(0).strip()
    return "masalah teknis umum"

# =====================================================
# Summarizer Bahasa Indonesia
# =====================================================
def summarize_chunk(customer_texts, admin_texts):
    customer_block = trim_non_technical_block(" ".join(customer_texts).strip())
    admin_block = trim_non_technical_block(" ".join(admin_texts).strip())

    if not customer_block or not admin_block:
        print("[⚠️] Empty content after filtering → skipped.")
        return None

    prompt = f"""
Kamu adalah asisten yang merangkum percakapan teknis antara pelanggan dan admin servis Honeywell Air Cleaner.
Fokus HANYA pada masalah teknis dan cara penyelesaiannya.
Abaikan bagian yang berisi pembayaran, alamat, invoice, atau jadwal teknisi.

Kembalikan hasil dalam format JSON:
- topic: frasa singkat (maks. 10 kata) yang menjelaskan masalah utama
- customer: gabungan pertanyaan pelanggan
- admin: gabungan jawaban admin yang berisi solusi
- summary: 1 kalimat yang menjelaskan inti masalah & solusinya

Semua hasil HARUS dalam Bahasa Indonesia profesional.

Pesan pelanggan:
{customer_block}

Pesan admin:
{admin_block}