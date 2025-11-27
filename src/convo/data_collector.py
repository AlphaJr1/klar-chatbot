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
        """
        
        result = self.ollama.generate_json(system=system_msg, prompt=prompt) or {}
        
        self._log_llm_call(
            func="validate_address_via_llm",
            user_id=user_id,
            call_type="generate_json",
            system=system_msg,
            prompt=prompt,
            response=result,
            meta={"address": address, "python_validation_score": address_score, "skipped_due_to_python": False}
        )
        
        result.setdefault("is_complete", False)
        result.setdefault("is_jabodetabek", keyword_check)
        result.setdefault("missing_info", [])
        result.setdefault("confidence", "low")
        result.setdefault("reason", "")
        
        return result
    
    def extract_name_and_gender_via_llm(self, user_id: str, message: str) -> Dict[str, Any]:
        
        message_clean = message.strip()
        words = message_clean.split()
        
        non_name_keywords = [
            'saya', 'atas', 'nama', 'pembelian', 'kemarin', 'adalah', 'itu', 'ini',
            'dari', 'untuk', 'dengan', 'yang', 'di', 'ke', 'pada', 'oleh',
            'produk', 'alamat', 'serial', 'nomor', 'telepon', 'hp', 'wa'
        ]
        
        if 1 <= len(words) <= 2:
            has_non_name = any(word.lower() in non_name_keywords for word in words)
            if not has_non_name:
                name = message_clean.title()
                gender = self._detect_gender_simple(name)
                
                return {
                    "name": name,
                    "gender": gender,
                    "confidence": "high",
                    "is_company": False
                }
        
        system_msg = "Kamu adalah ekstrator nama dan tipe entitas. Jawab HANYA JSON valid."
        
        prompt = f"""
        Analisis nama dari jawaban pelanggan berikut:
        "{message}"
        
        Tugas:
        1. Ekstrak NAMA lengkap
        2. Tentukan apakah ini nama PERUSAHAAN atau nama PERSONAL
        3. Tentukan GENDER (hanya untuk personal)
        
        Kriteria PERUSAHAAN (is_company: true):
        - Ada inisiator: PT, CV, UD, Yayasan, Toko, Koperasi
        - Nama berbentuk institusi: "Sejahtera Jaya", "Maju Bersama", "Karya Mandiri"
        - Pola nama bisnis: mengandung kata seperti Jaya, Sejahtera, Mandiri, Abadi, Sentosa, Makmur, Karya
        - Nama yang terlalu formal/tidak lazim untuk personal
        
        Kriteria PERSONAL (is_company: false):
        - Nama orang Indonesia: Budi, Ahmad, Siti, Dewi, dll
        - Pola nama personal: [Nama Depan] [Nama Belakang]
        - Mengandung nama yang umum digunakan orang
        
        Tips gender (untuk personal):
        - Male: Budi, Ahmad, Andi, Rudi, Agus, Bambang, Dedi, Eko, dll
        - Female: Siti, Ani, Dewi, Rina, Sri, Fitri, Wati, Yanti, dll
        - Unknown: jika perusahaan atau tidak yakin
        
        Contoh:
        - "PT Maju Jaya" → is_company: true
        - "Sejahtera Abadi" → is_company: true (pola nama bisnis)
        - "Toko Berkah" → is_company: true
        - "Budi Santoso" → is_company: false, gender: male
        - "Siti Aminah" → is_company: false, gender: female
        
        Jawab HANYA JSON:
        {{
          "name": "nama lengkap yang diekstrak",
          "gender": "male/female/unknown",
          "is_company": true/false,
          "confidence": "high/medium/low"
        }}
        """
        
        result = self.ollama.generate_json(system=system_msg, prompt=prompt) or {}
        
        self._log_llm_call(
            func="extract_name_and_gender_via_llm",
            user_id=user_id,
            call_type="generate_json",
            system=system_msg,
            prompt=prompt,
            response=result,
            meta={"message": message}
        )
        
        result.setdefault("name", "")
        result.setdefault("gender", "unknown")
        result.setdefault("confidence", "low")
        result.setdefault("is_company", False)
        
        return result
    
    def _detect_gender_simple(self, name: str) -> str:
        name_lower = name.lower()
        
        female_keywords = [
            'siti', 'ani', 'dewi', 'rina', 'sri', 'fitri', 'wati', 'yanti', 'lestari', 'nurhaliza',
            'ayu', 'bella', 'citra', 'diah', 'endah', 'farah', 'gita', 'hana', 'indah', 'julia',
            'kartika', 'linda', 'maya', 'putri', 'ratna', 'sari', 'tari', 'utami',
            'vina', 'wulan', 'yuni', 'zahra', 'anggun', 'cantika', 'dina', 'elsa', 'nurul'
        ]
        
        male_keywords = [
            'budi', 'ahmad', 'andi', 'rudi', 'agus', 'bambang', 'dedi', 'eko', 'hadi', 'joko',
            'ade', 'aditya', 'arif', 'bayu', 'dani', 'fajar', 'hendra', 'irwan', 'jaya',
            'kurniawan', 'lukman', 'muhammad', 'putra', 'rahman', 'santoso', 'taufik',
            'usman', 'wahyu', 'yudi', 'hidayat', 'rizki', 'fauzi', 'hakim', 'malik'
        ]
        
        for keyword in female_keywords:
            if keyword in name_lower:
                return "female"
        
        for keyword in male_keywords:
            if keyword in name_lower:
                return "male"
        
        return "unknown"
    
    def extract_product_via_llm(self, user_id: str, message: str) -> Dict[str, Any]:
        
        message_upper = message.upper().replace(" ", "").replace(".", "").replace(",", "")
        
        for product in self.VALID_PRODUCTS:
            product_clean = product.replace(" ", "")
            
            if product_clean in message_upper:
                return {
                    "product": product,
                    "confidence": "high"
                }
            
            product_parts = [c for c in product if c.isalnum()]
            pattern = "".join(product_parts)
            if pattern in message_upper:
                return {
                    "product": product,
                    "confidence": "high"
                }
        
        import re
        pattern_f57a = r'[fF]\s*5\s*7\s*[aA]'
        pattern_f90a = r'[fF]\s*9\s*0\s*[aA]'
        
        if re.search(pattern_f57a, message):
            return {
                "product": "F57A",
                "confidence": "high"
            }
        
        if re.search(pattern_f90a, message):
            return {
                "product": "F90A",
                "confidence": "high"
            }
        
        msg_normalized = message.lower().replace(" ", "").replace("type", "").replace("tipe", "").replace("model", "")
        if "f57a" in msg_normalized or "57a" in msg_normalized:
            return {
                "product": "F57A",
                "confidence": "medium"
            }
        if "f90a" in msg_normalized or "90a" in msg_normalized:
            return {
                "product": "F90A",
                "confidence": "medium"
            }
        
        system_msg = "Kamu adalah ekstrator produk. Jawab HANYA JSON valid."
        
        prompt = f"""
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
        """
        
        result = self.ollama.generate_json(system=system_msg, prompt=prompt) or {}
        
        self._log_llm_call(
            func="extract_product_via_llm",
            user_id=user_id,
            call_type="generate_json",
            system=system_msg,
            prompt=prompt,
            response=result,
            meta={"message": message, "skipped_due_to_regex": False}
        )
        
        result.setdefault("product", "none")
        result.setdefault("confidence", "low")
        
        return result
    
    def generate_question(self, user_id: str, field: str, context: Optional[str] = None) -> str:
        
        identity = self.memstore.get_identity(user_id)
        gender = identity.get("gender")
        
        if gender == "male":
            salutation = "Pak"
        elif gender == "female":
            salutation = "Bu"
        else:
            salutation = "Kak"
        
        if field == "name":
            return f"Baik {salutation}, boleh tahu kemarin pembeliannya atas nama siapa?"
        
        elif field == "product":
            return f"Baik {salutation}, untuk produknya F57A atau F90A?"
        
        elif field == "address":
            return f"Baik {salutation}, boleh info alamat lengkapnya? Supaya kami bisa pastikan lokasinya."
        
        else:
            return f"Maaf {salutation}, ada yang bisa saya bantu?"

    
    def generate_incomplete_address_message(self, user_id: str, missing_info: list) -> str:
        
        identity = self.memstore.get_identity(user_id)
        gender = identity.get("gender")
        
        if gender == "male":
            salutation = "Pak"
        elif gender == "female":
            salutation = "Bu"
        else:
            salutation = "Kak"
        
        system_msg = "Kamu adalah CS Honeywell yang ramah dan profesional."
        
        missing_str = ", ".join(missing_info) if missing_info else "beberapa detail"
        
        prompt = f"""
        Generate pesan untuk memberitahu pelanggan bahwa alamat kurang lengkap.
        
        Info yang kurang: {missing_str}
        Sapaan: {salutation}
        
        Aturan:
        - Sopan dan tidak menyalahkan
        - Jelaskan apa yang kurang
        - Minta pelanggan melengkapi
        - Maksimal 2-3 kalimat
        
        Contoh: "Maaf {salutation}, alamatnya masih kurang lengkap. Bisa ditambahkan {missing_str}nya? Supaya teknisi kami bisa sampai dengan tepat."
        """
        
        message = self.ollama.generate(system=system_msg, prompt=prompt).strip()
        
        self._log_llm_call(
            func="generate_incomplete_address_message",
            user_id=user_id,
            call_type="generate",
            system=system_msg,
            prompt=prompt,
            response=message,
            meta={"missing_info": missing_info}
        )
        
        return message
    
    def generate_invalid_product_message(self, user_id: str, invalid_input: str) -> str:
        
        identity = self.memstore.get_identity(user_id)
        gender = identity.get("gender")
        
        if gender == "male":
            salutation = "Pak"
        elif gender == "female":
            salutation = "Bu"
        else:
            salutation = "Kak"
        
        system_msg = "Kamu adalah CS Honeywell yang ramah dan profesional."
        
        prompt = f"""
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
        """
        
        message = self.ollama.generate(system=system_msg, prompt=prompt).strip()
        
        self._log_llm_call(
            func="generate_invalid_product_message",
            user_id=user_id,
            call_type="generate",
            system=system_msg,
            prompt=prompt,
            response=message,
            meta={"invalid_input": invalid_input}
        )
        
        return message
    
    def generate_completion_message(self, user_id: str) -> str:
        
        identity = self.memstore.get_identity(user_id)
        name = identity.get("name")
        product = identity.get("product")
        address = identity.get("address")
        gender = identity.get("gender")
        is_company = identity.get("is_company", False)
        
        if gender == "male":
            salutation = "Pak"
        elif gender == "female":
            salutation = "Bu"
        else:
            salutation = "Kak"
        
        if is_company:
            name_with_salutation = name
        else:
            name_with_salutation = f"{salutation} {name}"
        
        is_jabodetabek = self._check_jabodetabek(address)
        
        system_msg = "Kamu adalah CS Honeywell yang ramah dan profesional."
        
        prompt = f"""
        Generate pesan penutup setelah data lengkap dikumpulkan.
        
        Data pelanggan:
        - Nama: {name_with_salutation}
        - Produk: {product}
        - Alamat: {address}
        - Lokasi: {"Jabodetabek" if is_jabodetabek else "Luar Jabodetabek"}
        
        Aturan:
        - Ucapkan terima kasih
        - Konfirmasi data sudah diterima
        - Informasikan teknisi akan menghubungi
        - Maksimal 2-3 kalimat
        - Jangan gunakan tanda tanya
        - Gunakan nama lengkap sesuai yang diberikan (sudah termasuk sapaan jika perlu)
        
        Contoh: "Terima kasih {name_with_salutation}. Data sudah kami terima. Teknisi kami akan segera menghubungi untuk jadwal kunjungan."
        """
        
        message = self.ollama.generate(system=system_msg, prompt=prompt).strip()
        
        self._log_llm_call(
            func="generate_completion_message",
            user_id=user_id,
            call_type="generate",
            system=system_msg,
            prompt=prompt,
            response=message,
            meta={"name": name, "product": product, "address": address, "is_jabodetabek": is_jabodetabek, "is_company": is_company}
        )
        
        if "?" in message:
            message = message.split("?")[0].strip() + "."
        
        return message
    
    def should_return_to_data_collection(self, user_id: str, message: str) -> Dict[str, Any]:
        
        state = self.get_collection_state(user_id)
        
        if state["is_complete"]:
            return {
                "should_return": False,
                "reason": "data_complete"
            }
        
        message_clean = message.strip()
        
        words = message_clean.split()
        if len(words) <= 5 and '?' not in message_clean:
            return {
                "should_return": False,
                "reason": "short_answer"
            }
        
        if any(prod in message_clean.upper().replace(" ", "") for prod in self.VALID_PRODUCTS):
            return {
                "should_return": False,
                "reason": "contains_product"
            }
        
        address_keywords = ['jalan', 'jl.', 'jl ', 'komplek', 'gang', 'gg.', 'rt', 'rw', 'kelurahan', 'kecamatan']
        if any(keyword in message_clean.lower() for keyword in address_keywords):
            return {
                "should_return": False,
                "reason": "looks_like_address"
            }
        
        system_msg = "Kamu adalah classifier pesan. Jawab HANYA JSON valid."
        
        prompt = f"""
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
        """
        
        result = self.ollama.generate_json(system=system_msg, prompt=prompt) or {}
        
        self._log_llm_call(
            func="should_return_to_data_collection",
            user_id=user_id,
            call_type="generate_json",
            system=system_msg,
            prompt=prompt,
            response=result,
            meta={"state": state, "message": message}
        )
        
        result.setdefault("type", "data_answer")
        result.setdefault("confidence", "low")
        result.setdefault("should_answer_first", False)
        
        if result["type"] != "data_answer":
            return {
                "should_return": True,
                "message_type": result["type"],
                "should_answer_first": result["should_answer_first"],
                "missing_field": state["next_field"]
            }
        
        return {
            "should_return": False,
            "reason": "is_data_answer"
        }
    
    def generate_return_to_data_message(self, user_id: str, missing_field: str) -> str:
        
        identity = self.memstore.get_identity(user_id)
        gender = identity.get("gender")
        
        if gender == "male":
            salutation = "Pak"
        elif gender == "female":
            salutation = "Bu"
        else:
            salutation = "Kak"
        
        field_name_map = {
            "name": "nama",
            "product": "produk",
            "address": "alamat"
        }
        
        field_name = field_name_map.get(missing_field, "data")
        
        system_msg = "Kamu adalah CS Honeywell yang ramah dan profesional."
        
        prompt = f"""
        Generate pesan untuk mengajak pelanggan kembali ke pengisian data.
        
        Sapaan: {salutation}
        Data yang masih kurang: {field_name}
        
        Aturan:
        - Sangat halus dan tidak memaksa
        - Tunjukkan empati
        - Ajak kembali ke pengisian data
        - Maksimal 2 kalimat
        
        Contoh: "Baik {salutation}, saya mengerti. Sebelumnya, boleh kita lanjutkan pengisian {field_name}nya dulu?"
        """
        
        message = self.ollama.generate(system=system_msg, prompt=prompt).strip()
        
        self._log_llm_call(
            func="generate_return_to_data_message",
            user_id=user_id,
            call_type="generate",
            system=system_msg,
            prompt=prompt,
            response=message,
            meta={"missing_field": missing_field}
        )
        
        return message
    
    def process_message(self, user_id: str, message: str) -> Dict[str, Any]:
        
        state = self.get_collection_state(user_id)
        
        if state["is_complete"]:
            return {
                "action": "complete",
                "response": self.generate_completion_message(user_id),
                "data_updated": {},
                "is_complete": True
            }
        
        off_topic_check = self.should_return_to_data_collection(user_id, message)
        
        if off_topic_check["should_return"]:
            return {
                "action": "off_topic",
                "response": None,
                "off_topic_info": off_topic_check,
                "is_complete": False
            }
        
        next_field = state["next_field"]
        
        if next_field == "name":
            existing_name = state.get("name")
            extracted = self.extract_name_and_gender_via_llm(user_id, message)
            
            if extracted["name"] and extracted["confidence"] in ["high", "medium"]:
                self.memstore.set_name(user_id, extracted["name"])
                self.memstore.set_gender(user_id, extracted["gender"])
                self.memstore.update(user_id, {"is_company": extracted.get("is_company", False)})
                
                new_state = self.get_collection_state(user_id)
                
                if new_state["next_field"]:
                    next_question = self.generate_question(user_id, new_state["next_field"])
                    return {
                        "action": "name_saved_ask_next",
                        "response": next_question,
                        "data_updated": {
                            "name": extracted["name"], 
                            "gender": extracted["gender"],
                            "is_company": extracted.get("is_company", False)
                        },
                        "is_complete": False
                    }
                else:
                    return {
                        "action": "complete",
                        "response": self.generate_completion_message(user_id),
                        "data_updated": {
                            "name": extracted["name"], 
                            "gender": extracted["gender"],
                            "is_company": extracted.get("is_company", False)
                        },
                        "is_complete": True
                    }
            else:
                identity = self.memstore.get_identity(user_id)
                gender = identity.get("gender")
                salutation = "Pak" if gender == "male" else "Bu" if gender == "female" else "Kak"
                
                fallback = f"Maaf {salutation}, boleh diulang namanya?"
                return {
                    "action": "ask_name",
                    "response": fallback,
                    "data_updated": {},
                    "is_complete": False
                }
        
        elif next_field == "product":
            extracted = self.extract_product_via_llm(user_id, message)
            
            if extracted["product"] != "none":
                validation = self.validate_product(extracted["product"])
                
                if validation["valid"]:
                    self.memstore.set_product(user_id, validation["product"])
                    
                    new_state = self.get_collection_state(user_id)
                    
                    if new_state["next_field"]:
                        next_question = self.generate_question(user_id, new_state["next_field"])
                        return {
                            "action": "product_saved_ask_next",
                            "response": next_question,
                            "data_updated": {"product": validation["product"]},
                            "is_complete": False
                        }
                    else:
                        return {
                            "action": "complete",
                            "response": self.generate_completion_message(user_id),
                            "data_updated": {"product": validation["product"]},
                            "is_complete": True
                        }
                else:
                    identity = self.memstore.get_identity(user_id)
                    gender = identity.get("gender")
                    salutation = "Pak" if gender == "male" else "Bu" if gender == "female" else "Kak"
                    
                    fallback = f"Maaf {salutation}, produk yang tersedia hanya F57A atau F90A. Bisa dipastikan lagi?"
                    return {
                        "action": "invalid_product",
                        "response": fallback,
                        "data_updated": {},
                        "is_complete": False
                    }
            else:
                identity = self.memstore.get_identity(user_id)
                gender = identity.get("gender")
                salutation = "Pak" if gender == "male" else "Bu" if gender == "female" else "Kak"
                
                fallback = f"Baik {salutation}, untuk produknya F57A atau F90A?"
                return {
                    "action": "ask_product",
                    "response": fallback,
                    "data_updated": {},
                    "is_complete": False
                }
        
        elif next_field == "address":
            validation = self.validate_address_via_llm(user_id, message)
            
            if validation["is_complete"]:
                self.memstore.update(user_id, {"address": message})
                
                return {
                    "action": "complete",
                    "response": self.generate_completion_message(user_id),
                    "data_updated": {
                        "address": message,
                        "is_jabodetabek": validation["is_jabodetabek"]
                    },
                    "is_complete": True
                }
            else:
                incomplete_msg = self.generate_incomplete_address_message(user_id, validation.get("missing_info", []))
                
                return {
                    "action": "incomplete_address",
                    "response": incomplete_msg,
                    "data_updated": {},
                    "is_complete": False,
                    "validation_result": validation
                }
        
        identity = self.memstore.get_identity(user_id)
        gender = identity.get("gender")
        salutation = "Pak" if gender == "male" else "Bu" if gender == "female" else "Kak"
        
        return {
            "action": "unknown",
            "response": f"Baik {salutation}, ada yang bisa saya bantu?",
            "data_updated": {},
            "is_complete": False
        }
