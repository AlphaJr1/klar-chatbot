from __future__ import annotations
import json
import os
from typing import Dict, Any, Optional, Literal
from datetime import datetime, timezone

BASE = os.path.dirname(os.path.dirname(__file__))
LLM_LOG_PATH = os.path.join(BASE, "convo", "llm_log", "llm_log.json")

class DataCollector:
    
    VALID_PRODUCTS = ["F57A", "F90A"]
    
    JABODETABEK_KEYWORDS = [
        "jakarta", "bogor", "depok", "tangerang", "bekasi",
        "jkt", "jaktim", "jakbar", "jaksel", "jakut", "jakpus",
        "tangsel", "tangerang selatan", "bintaro", "serpong",
        "bsd", "gading serpong", "alam sutera", "karawaci",
        "cibubur", "cimanggis", "margonda", "ui", "sawangan",
        "cibinong", "sentul", "gunung putri", "cileungsi",
        "pondok gede", "jatiasih", "jatisampurna", "mustika jaya",
        "rawamangun", "kelapa gading", "pluit", "pantai indah kapuk",
        "pik", "sunter", "kemayoran", "menteng", "kuningan",
        "sudirman", "senayan", "kebayoran", "cilandak", "lebak bulus",
        "fatmawati", "pondok indah", "bintaro", "pesanggrahan"
    ]
    
    def __init__(self, ollama_client, memory_store):
        self.ollama = ollama_client
        self.memstore = memory_store
    
    def _log_llm_call(
        self,
        *,
        func: str,
        user_id: str,
        call_type: str,
        system: str,
        prompt: str,
        response: Any,
        meta: Optional[Dict[str, Any]] = None,
    ) -> None:
        try:
            os.makedirs(os.path.dirname(LLM_LOG_PATH), exist_ok=True)

            record = {
                "ts": datetime.now(timezone.utc).isoformat(),
                "func": func,
                "user_id": user_id,
                "call_type": call_type,
                "system": system,
                "prompt": prompt,
                "response": response,
                "meta": meta or {},
            }

            existing: list[Any] = []
            if os.path.exists(LLM_LOG_PATH):
                try:
                    with open(LLM_LOG_PATH, "r", encoding="utf-8") as f:
                        existing = json.load(f)
                        if not isinstance(existing, list):
                            existing = []
                except Exception:
                    existing = []

            existing.append(record)

            with open(LLM_LOG_PATH, "w", encoding="utf-8") as f:
                json.dump(existing, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
        
    def get_collection_state(self, user_id: str) -> Dict[str, Any]:
        identity = self.memstore.get_identity(user_id)
        
        name = identity.get("name")
        product = identity.get("product")
        address = identity.get("address")
        gender = identity.get("gender")
        
        is_jabodetabek = self._check_jabodetabek(address) if address else None
        
        return {
            "name": name,
            "gender": gender,
            "product": product,
            "address": address,
            "is_jabodetabek": is_jabodetabek,
            "is_complete": all([name, product, address]),
            "next_field": self._get_next_missing_field(name, product, address)
        }
    
    def _get_next_missing_field(self, name, product, address) -> Optional[str]:
        if not name:
            return "name"
        if not product:
            return "product"
        if not address:
            return "address"
        return None
    
    def _check_jabodetabek(self, address: str) -> bool:
        if not address:
            return False
        
        address_lower = address.lower()
        return any(keyword in address_lower for keyword in self.JABODETABEK_KEYWORDS)
    
    def validate_product(self, product_input: str) -> Dict[str, Any]:
        product_clean = product_input.strip().upper().replace(" ", "").replace("-", "")
        
        if product_clean in self.VALID_PRODUCTS:
            return {
                "valid": True,
                "product": product_clean,
                "message": None
            }
        
        product_patterns = {
            "F57A": ["F57", "57A", "F-57", "F57A", "EAC57", "EAC-57"],
            "F90A": ["F90", "90A", "F-90", "F90A", "EAC90", "EAC-90"]
        }
        
        if "EAC" in product_clean:
            if "90" in product_clean:
                return {
                    "valid": True,
                    "product": "F90A",
                    "message": None,
                    "inferred": True
                }
            elif "57" in product_clean:
                return {
                    "valid": True,
                    "product": "F57A",
                    "message": None,
                    "inferred": True
                }
        
        for valid_product, patterns in product_patterns.items():
            if any(pattern in product_clean for pattern in patterns):
                return {
                    "valid": True,
                    "product": valid_product,
                    "message": None,
                    "inferred": True
                }
        
        return {
            "valid": False,
            "product": None,
            "message": f"Mohon maaf, produk yang tersedia saat ini hanya {' atau '.join(self.VALID_PRODUCTS)}. Bisa dipastikan lagi produknya yang mana?"
        }

    def validate_address_via_llm(self, user_id: str, address: str) -> Dict[str, Any]:
        
        address_lower = address.lower()
        
        has_street = any(x in address_lower for x in [
            'jl.', 'jl ', 'jalan', 'gang', 'gg.', 'gg ', 'raya', 'street', 
            'boulevard', 'blvd', 'avenue', 'ave', 'jln', 'jln.'
        ])
        
        has_complex = any(x in address_lower for x in [
            'komplek', 'kompleks', 'perumahan', 'perum', 'cluster', 
            'residence', 'village', 'town', 'estate', 'griya', 'taman'
        ])
        
        has_number_or_marker = any(x in address_lower for x in [
            'km ', 'km.', 'no.', 'no ', 'nomor', 'blok', 'rt ', 'rt.', 
            'rw ', 'rw.', 'rt/', 'rw/', '#'
        ]) or any(c.isdigit() for c in address)
        
        city_keywords = [
            'jakarta', 'bogor', 'depok', 'tangerang', 'bekasi', 
            'bandung', 'surabaya', 'medan', 'semarang', 'yogyakarta', 'yogya', 'jogja',
            'malang', 'solo', 'surakarta', 'bali', 'denpasar', 'makassar', 'palembang',
            'jaktim', 'jakbar', 'jaksel', 'jakut', 'jakpus', 
            'tangsel', 'tangerang selatan', 'bsd', 'serpong', 'karawaci',
            'cibubur', 'cimanggis', 'margonda', 'sawangan', 'cibinong'
        ]
        has_city_name = any(city in address_lower for city in city_keywords)
        
        keyword_check = self._check_jabodetabek(address)
        
        address_score = 0
        if has_street or has_complex:
            address_score += 1
        if has_number_or_marker:
            address_score += 1
        if has_city_name:
            address_score += 1
        
        if address_score >= 3:
            return {
                "is_complete": True,
                "is_jabodetabek": keyword_check,
                "missing_info": [],
                "confidence": "high",
                "reason": "Alamat memiliki komponen lengkap (street/complex + number + city) - validasi Python"
            }
        
        if address_score == 2 and has_city_name:
            if (has_street or has_complex):
                return {
                    "is_complete": True,
                    "is_jabodetabek": keyword_check,
                    "missing_info": [],
                    "confidence": "medium",
                    "reason": "Alamat memiliki kota dan jalan/komplek - validasi Python"
                }
        
        if len(address.split()) >= 5 and has_city_name and (has_street or has_complex):
            return {
                "is_complete": True,
                "is_jabodetabek": keyword_check,
                "missing_info": [],
                "confidence": "medium",
                "reason": "Alamat cukup detail dengan kota dan lokasi - validasi Python"
            }
        
        system_msg = "Kamu adalah validator alamat. Jawab HANYA JSON valid."
        
        prompt = f"""
        Analisis alamat berikut dan tentukan:
        1. Apakah alamat ini LENGKAP untuk pengiriman/kunjungan teknisi?
        2. Apakah alamat ini berada di JABODETABEK?
        
        Alamat: "{address}"
        
        Kriteria alamat lengkap (MINIMAL):
        - Ada nama jalan/gang/komplek
        - Ada nomor rumah/blok ATAU patokan jelas (KM, dekat landmark, dll)
        - Ada nama kota/wilayah Jabodetabek (Jakarta Selatan, Depok, Tangerang, Bekasi, dll)
        
        PENTING: 
        - Alamat dianggap LENGKAP jika memiliki 3 komponen di atas
        - "KM" (kilometer) adalah patokan yang VALID
        - Kelurahan/kecamatan adalah OPSIONAL, tidak wajib
        - Jika ada nama kota (Jakarta, Depok, Tangerang, Bekasi, Bogor), itu SUDAH CUKUP
        
        Area Jabodetabek meliputi:
        - Jakarta (semua wilayah: Selatan, Utara, Barat, Timur, Pusat)
        - Bogor (kota dan kabupaten)
        - Depok
        - Tangerang (kota dan selatan)
        - Bekasi (kota dan kabupaten)
        
        Contoh alamat LENGKAP:
        - "Jl. Sudirman 123, Jakarta Selatan" ✓
        - "Jl. Raya Bogor KM 25, Depok" ✓
        - "Komplek Griya Asri, Bekasi" ✓
        
        Contoh alamat TIDAK LENGKAP:
        - "Jl. Sudirman" ✗ (tidak ada kota)
        - "Jakarta Selatan" ✗ (tidak ada jalan)
        
        Jawab HANYA JSON:
        {{
          "is_complete": true/false,
          "is_jabodetabek": true/false,
          "missing_info": ["list info yang kurang jika tidak lengkap"],
          "confidence": "high/medium/low",
          "reason": "penjelasan singkat"
        }}
        Ekstrak informasi dari jawaban pelanggan berikut:
        "{message}"
        
        Tugas:
        1. Identifikasi NAMA lengkap
        2. Tentukan GENDER berdasarkan nama (male/female/unknown)
        
        Tips gender:
        - Nama seperti: Budi, Ahmad, Andi, Rudi, Agus, Bambang → male
        - Nama seperti: Siti, Ani, Dewi, Rina, Sri, Fitri → female
        - Jika tidak yakin → unknown
        
        Jawab HANYA JSON:
        {{
          "name": "nama lengkap yang diekstrak",
          "gender": "male/female/unknown",
          "confidence": "high/medium/low"
        }}
        Ekstrak informasi produk dari jawaban pelanggan:
        "{message}"
        
        Produk yang valid: {', '.join(self.VALID_PRODUCTS)}
        
        Cari pola seperti:
        - "F57A" atau "f57a" atau "F 57 A"
        - "F90A" atau "f90a" atau "F 90 A"
        - "tipe F57A" atau "model F90A"
        
        Jawab HANYA JSON:
        {{
          "product": "F57A/F90A/none",
          "confidence": "high/medium/low"
        }}
        Generate pesan untuk memberitahu pelanggan bahwa alamat kurang lengkap.
        
        Info yang kurang: {missing_str}
        Sapaan: {salutation}
        
        Aturan:
        - Sopan dan tidak menyalahkan
        - Jelaskan apa yang kurang
        - Minta pelanggan melengkapi
        - Maksimal 2-3 kalimat
        
        Contoh: "Maaf {salutation}, alamatnya masih kurang lengkap. Bisa ditambahkan {missing_str}nya? Supaya teknisi kami bisa sampai dengan tepat."
        Generate pesan untuk memberitahu pelanggan bahwa produk tidak valid.
        
        Input pelanggan: "{invalid_input}"
        Produk valid: F57A atau F90A
        Sapaan: {salutation}
        
        Aturan:
        - Sopan dan tidak menyalahkan
        - Jelaskan produk yang tersedia
        - Minta konfirmasi ulang
        - Maksimal 2 kalimat
        
        Contoh: "Maaf {salutation}, untuk saat ini produk yang tersedia hanya F57A atau F90A. Bisa dipastikan lagi produknya yang mana?"
        Generate pesan penutup setelah data lengkap dikumpulkan.
        
        Data pelanggan:
        - Nama: {name}
        - Produk: {product}
        - Alamat: {address}
        - Lokasi: {"Jabodetabek" if is_jabodetabek else "Luar Jabodetabek"}
        
        Sapaan: {salutation}
        
        Aturan:
        - Ucapkan terima kasih
        - Konfirmasi data sudah diterima
        - Informasikan teknisi akan menghubungi
        - Maksimal 2-3 kalimat
        - Jangan gunakan tanda tanya
        
        Contoh: "Terima kasih {salutation} {name}. Data sudah kami terima. Teknisi kami akan segera menghubungi untuk jadwal kunjungan."
        Analisis apakah pesan pelanggan ini adalah jawaban untuk data collection atau pertanyaan lain.
        
        Pesan: "{message}"
        
        Konteks: Sedang dalam proses pengumpulan data (nama, produk, alamat).
        Field yang masih kurang: {state["next_field"]}
        
        Klasifikasi:
        - "data_answer": Jika pesan berisi jawaban untuk data (nama/produk/alamat)
        - "question": Jika pesan berisi pertanyaan tentang produk/layanan
        - "complaint": Jika pesan berisi keluhan baru
        - "chitchat": Jika pesan berisi obrolan biasa
        
        Jawab HANYA JSON:
        {{
          "type": "data_answer/question/complaint/chitchat",
          "confidence": "high/medium/low",
          "should_answer_first": true/false
        }}
        Generate pesan untuk mengajak pelanggan kembali ke pengisian data.
        
        Sapaan: {salutation}
        Data yang masih kurang: {field_name}
        
        Aturan:
        - Sangat halus dan tidak memaksa
        - Tunjukkan empati
        - Ajak kembali ke pengisian data
        - Maksimal 2 kalimat
        
        Contoh: "Baik {salutation}, saya mengerti. Sebelumnya, boleh kita lanjutkan pengisian {field_name}nya dulu?"