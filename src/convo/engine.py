from __future__ import annotations
import json, os, sys, random
from typing import Dict, Any, Optional
from datetime import datetime, timedelta, timezone

BASE = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if os.path.join(BASE, "src") not in sys.path:
    sys.path.insert(0, os.path.join(BASE, "src"))

RAG_LOG_PATH = os.path.join(BASE, "src", "retriever", "rag_query_log.json")
LLM_LOG_PATH = os.path.join(BASE, "data", "storage", "logs", "llm_log.json")

from .memory_store import MemoryStore as MemoryStoreBackend
from .session_logger import get_wa_logger
from .chat_logger import get_chat_logger
from .ollama_client import OllamaClient
from .data_collector import DataCollector

def short_log(logger, jid: str, stage: str, info_or_msg: Any):
    try:
        if isinstance(info_or_msg, dict):
            logger.log_stage(jid=jid, stage=stage, info=info_or_msg, response="")
        else:
            logger.log_stage(jid=jid, stage=stage, info={}, response=str(info_or_msg))
    except Exception:
        pass

class ConversationEngine:
    def __init__(self) -> None:
        self.memstore = MemoryStoreBackend(autosave=True, debug=False)
        self.gateway_only = False
        if hasattr(self.memstore, "set_debug"):
            self.memstore.set_debug(False)

        try:
            self.logger = get_wa_logger()
        except Exception:
            from types import SimpleNamespace
            self.logger = SimpleNamespace(
                log_in=lambda **_: None,
                log_stage=lambda **_: None,
            )
        
        try:
            self.chat_logger = get_chat_logger()
        except Exception:
            from types import SimpleNamespace
            self.chat_logger = SimpleNamespace(
                log_incoming=lambda **_: None,
                log_outgoing=lambda **_: None,
            )

        self.ollama = OllamaClient()
        self.data_collector = DataCollector(self.ollama, self.memstore)

    def load_sop_from_file(self) -> dict:
        sop_path = os.path.join(BASE, "data", "kb", "sop.json")

        try:
            with open(sop_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            short_log(self.logger, "system", "load_sop", {"status": "ok", "items": len(data)})

            return data

        except Exception as e:
            short_log(self.logger, "system", "load_sop_error", str(e))
            return {}

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

    def _user_context_header(self, user_id: str) -> str:
        try:
            rec = self.memstore.get(user_id)
            token = rec.get("session_token", "unknown")
        except Exception:
            token = "unknown"
        return (
            f"[SESSION CONTEXT – USER ID: {user_id} | TOKEN: {token}] "
            "Jangan gunakan konteks atau percakapan dari pengguna lain.\n"
        )

    def detect_intent_via_llm(self, user_id: str, message: str, sop_intents: list[str]) -> Dict[str, Any]:
        sop = self.load_sop_from_file()
        active_intent = self.memstore.get_flag(user_id, "active_intent")

        history = self.memstore.get(user_id).get("history", [])
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        todays_messages = []
        for h in history:
            if h["ts"].startswith(today):
                role = "Bot" if h["role"] == "bot" else "User"
                todays_messages.append(f"{role}: {h['text']}")
        history_block = "\n".join(todays_messages) if todays_messages else "(Tidak ada percakapan hari ini)"

        active_step_json = None
        if active_intent and active_intent in sop:
            active_step_info = self.get_active_step(user_id, sop)
            step_id = active_step_info.get("step_id")
            if step_id:
                for s in sop[active_intent]["steps"]:
                    if s["id"] == step_id:
                        active_step_json = s
                        break

        system_msg = (
            "Kamu adalah intent classifier Honeywell. "
            "Jawab HANYA JSON VALID. DILARANG menambah field."
        )

        prompt = f"""
        {self._user_context_header(user_id)}

        Riwayat percakapan hari ini:
        {history_block}

        Pesan pelanggan:
        \"{message}\"

        Active intent saat ini: {active_intent or "none"}

        Daftar intent valid:
        {", ".join(sop_intents)}
        
        PRODUK HONEYWELL:
        - EAC (Electronic Air Cleaner) / Air Purifier / Pembersih Udara
        - Water Heater / Pemanas Air
        - Produk lainnya
        
        MAPPING KELUHAN KE INTENT:
        
        Intent "mati":
        - Tidak menyala, tidak hidup, mati total, padam, off, tidak berfungsi
        - Tidak panas (untuk water heater)
        - Tidak ada respon sama sekali
        
        Intent "bau":
        - Bau tidak sedap, bau aneh, bau menyengat
        - Aroma tidak enak
        
        Intent "bunyi":
        - Bunyi aneh, berisik, suara berisik
        - Bunyi kretek-kretek, bunyi berdengung
        - Noise, berisik

        LOGIC PRIORITAS:
        
        1. Jika active_intent SUDAH ADA (bukan "none"):
           a) Intent TETAP = active_intent (JANGAN ubah!)
           b) DETEKSI keluhan TAMBAHAN (additional_complaint):
              ⚠️ PENTING: Hanya deteksi jika pesan JELAS dan EKSPLISIT menyebut keluhan baru.
              JANGAN deteksi jika substring kebetulan ada dalam kata lain.
              
              - Jika JELAS menyebut masalah bau → additional_complaint="bau"
                Contoh: "juga bau", "bau menyengat", "ada bau aneh"
              
              - Jika JELAS menyebut masalah bunyi → additional_complaint="bunyi"
                Contoh: "juga berisik", "mengeluarkan bunyi aneh", "suara berisik"
              
              - Jika JELAS menyebut masalah mati/tidak nyala/tidak panas → additional_complaint="mati"
                Contoh: "EAC juga mati", "tidak menyala", "padam total"
              
              - Jika hanya chitchat/terima kasih/sapaan tanpa keluhan → additional_complaint="none"
                Contoh: "terimakasih", "ok siap", "baik", "halo"
           
           c) is_new_complaint = false (SELALU, kecuali keluhan SAMA yang berulang dengan kata "lagi"/"kembali")
        
        2. Jika active_intent BELUM ADA (masih "none"):
           a) Deteksi intent dari keluhan (mati / bau / bunyi / none)
           b) additional_complaint = "none" (tidak relevan jika belum ada active)
           c) is_new_complaint = true (jika ada keluhan perangkat), false (jika hanya greeting/chitchat)

        Jika active_step tersedia:
        {json.dumps(active_step_json, ensure_ascii=False, indent=2) if active_step_json else "(Tidak ada step aktif)"}

        CONTOH KASUS - SAAT ACTIVE_INTENT ADA:
        
        Contoh 1:
        active_intent = "mati"
        message = "eh iya EAC nya juga bunyi aneh lho"
        →  intent = "mati" (TETAP)
        →  additional_complaint = "bunyi" (DETECTED - karena jelas mention bunyi EAC)
        →  is_new_complaint = false
        
        Contoh 2:
        active_intent = "bunyi"
        message = "iya dan juga bau nya menyengat"
        →  intent = "bunyi" (TETAP)
        →  additional_complaint = "bau" (DETECTED - karena jelas mention bau)
        →  is_new_complaint = false
        
        Contoh 3:
        active_intent = "mati"
        message = "tidak nyala"
        →  intent = "mati" (TETAP)
        →  additional_complaint = "none" (tidak mention keluhan lain)
        →  is_new_complaint = false
        
        Contoh 4 (PENTING):
        active_intent = "bau"
        message = "terimakasih"
        →  intent = "bau" (TETAP)
        →  additional_complaint = "none" (hanya ucapan terima kasih, BUKAN keluhan)
        →  is_new_complaint = false

        Kembalikan hanya JSON:
        {{
        "has_greeting": true/false,
        "greeting_part": "<string>",
        "issue_part": "<string>",
        "intent": "<mati/bau/bunyi/none>",
        "category": "domain/chitchat/nonsense",
        "is_new_complaint": true/false,
        "additional_complaint": "<mati/bau/bunyi/none>"
        }}
        """

        out = self.ollama.generate_json(system=system_msg, prompt=prompt) or {}

        self._log_llm_call(
            func="detect_intent_via_llm",
            user_id=user_id,
            call_type="generate_json",
            system=system_msg,
            prompt=prompt,
            response=out,
            meta={
                "active_intent": active_intent,
                "active_step": active_step_json,
                "history_today": len(todays_messages),
            },
        )

        out.setdefault("has_greeting", False)
        out.setdefault("greeting_part", "")
        out.setdefault("issue_part", message)
        out.setdefault("intent", active_intent or "none")
        out.setdefault("category", "domain")
        out.setdefault("is_new_complaint", False)
        out.setdefault("additional_complaint", "none")

        if active_intent and out.get("intent") in ("none", None):
            out["intent"] = active_intent

        return out

    def handle_greeting(self, user_id: str, message: str, extracted: Dict[str, Any]) -> Optional[str]:
        if not extracted.get("should_reply_greeting"):
            return None

        greet_text = extracted.get("greeting_part") or "Halo"

        prompt = f"""
        Balas greeting berikut dengan sopan dan profesional.
        Maksimal 1 kalimat.
        Hindari kata 'Anda'.
        Greeting pelanggan: "{greet_text}"
        """

        system_msg = "Asisten CS Honeywell yang profesional."
        full_prompt = self._user_context_header(user_id) + prompt

        reply = self.ollama.generate(
            system=system_msg,
            prompt=full_prompt,
        ).strip()

        self._log_llm_call(
            func="handle_greeting",
            user_id=user_id,
            call_type="generate",
            system=system_msg,
            prompt=full_prompt,
            response=reply,
            meta={"greeting_part": greet_text},
        )

        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        self.memstore.set_flag(user_id, "last_greeted_date", str(today))

        return reply

    def handle_data_collection(self, user_id: str, message: str) -> Optional[str]:
        if message.lower() in ["skip to data", "mulai data"]:
            prompt = """
            Kamu asisten CS Honeywell.
            Mulai proses pengumpulan data dengan satu pertanyaan:
            minta nama pelanggan dengan sopan, maksimal 2 kalimat.
            """
            system_msg = "Asisten CS teknis Honeywell profesional, sopan dan on-point. "

            reply = self.ollama.generate(
                system=system_msg,
                prompt=prompt,
            ).strip()

            self._log_llm_call(
                func="handle_data_collection_skip",
                user_id=user_id,
                call_type="generate",
                system=system_msg,
                prompt=prompt,
                response=reply,
                meta={},
            )
        
        has_identity = False
        identity_type = "none"
        
        msg_lower = message.lower()
        words = message.split()
        
        name_indicators = ['nama', 'saya', 'atas nama', 'an.', 'a.n.']
        address_keywords = ['jl.', 'jl ', 'jalan', 'gang', 'komplek', 'perumahan', 'jakarta', 'depok', 'tangerang', 'bekasi', 'bogor']
        product_keywords = ['f57a', 'f90a', 'produk', 'tipe', 'model']
        serial_keywords = ['serial', 'nomor seri', 'no seri', 'sn']
        company_keywords = ['perusahaan', 'company', 'pt', 'cv', 'kantor']
        
        if any(ind in msg_lower for ind in name_indicators) and len(words) <= 6:
            has_identity = True
            identity_type = "nama"
        elif any(kw in msg_lower for kw in address_keywords):
            has_identity = True
            identity_type = "alamat"
        elif any(kw in msg_lower for kw in product_keywords):
            has_identity = True
            identity_type = "produk"
        elif any(kw in msg_lower for kw in serial_keywords):
            has_identity = True
            identity_type = "serial"
        elif any(kw in msg_lower for kw in company_keywords):
            has_identity = True
            identity_type = "company"
        
        if not has_identity:
            if len(words) <= 3 and not any(c in msg_lower for c in ['?', 'apa', 'gimana', 'kenapa', 'kapan']):
                has_identity = True
                identity_type = "nama"
        
        if not has_identity:
            sop_pending = self.memstore.get_flag(user_id, "sop_pending")
            if not sop_pending:
                return None

        identity = self.memstore.get_identity(user_id)
        slots = self.memstore.get_slots(user_id)
        name = identity.get("name")
        product = identity.get("product")
        address = identity.get("address")
        company = slots.get("company")
        serial = identity.get("serial")
        gender = identity.get("gender")

        # Hanya deteksi dan simpan jika early check mendeteksi ada identitas
        if has_identity: # Fixed: Removed undefined 'early.get("has_identity")' and used 'has_identity'
            detect_prompt = f"""
            Analisis pesan pelanggan berikut:
            "{message}"

            Tentukan apakah pesan ini mengandung informasi identitas (nama, alamat, produk, company, serial).
            Jawab hanya JSON:
            {{
              "type": "nama / alamat / produk / company / serial / none",
              "value": "<isi yang dideteksi>"
            }}
            """
            system_msg_detect = "Detektor data pelanggan. Jawab HANYA JSON valid."
            detected = self.ollama.generate_json(
                system=system_msg_detect,
                prompt=detect_prompt,
            ) or {}

            self._log_llm_call(
                func="handle_data_collection_detect",
                user_id=user_id,
                call_type="generate_json",
                system=system_msg_detect,
                prompt=detect_prompt,
                response=detected,
                meta={},
            )

            dtype = detected.get("type", "none")
            val = (detected.get("value") or "").strip()
            conf = detected.get("confidence", "low")

            if dtype == "nama" and val and conf in ["high", "medium"]:
                self.memstore.set_name(user_id, val)
            elif dtype == "alamat" and val:
                self.memstore.update(user_id, {"address": val})
            elif dtype == "produk" and val:
                self.memstore.set_product(user_id, val)
            elif dtype == "company" and val:
                self.memstore.set_slot(user_id, "company", val)
            elif dtype == "serial" and val:
                self.memstore.update(user_id, {"serial": val})

        name = self.memstore.get_identity(user_id).get("name")
        address = self.memstore.get_identity(user_id).get("address")
        product = self.memstore.get_identity(user_id).get("product")
        complete = all([name, address, product])
        
        if complete:
            prompt = f"""
            Data pelanggan telah lengkap:
            - Nama: {name or '-'}
            - Alamat: {address or '-'}
            - Produk: {product or '-'}

            Tulis pesan penutup sopan 2–3 kalimat tanpa tanda tanya.
            Fokus: data sudah diterima, teknisi akan menghubungi kembali.
            """
            
            system_msg_complete = "Asisten CS teknis Honeywell profesional, sopan dan on-point. "

            reply = self.ollama.generate(
                system=system_msg_complete,
                prompt=prompt,
            ).strip()

            self._log_llm_call(
                func="handle_data_collection_complete",
                user_id=user_id,
                call_type="generate",
                system=system_msg_complete,
                prompt=prompt,
                response=reply,
                meta={"name": name, "address": address, "product": product},
            )

            if "?" in reply:
                reply = reply.split("?")[0].strip() + "."
            return reply

        missing_field = None
        if not name:
            missing_field = "name"
        elif not address:
            missing_field = "address"
        elif not product:
            missing_field = "product"
        elif not company:
            missing_field = "company"
        elif not serial:
            missing_field = "serial"

        if gender == "male":
            persona = "Gunakan sapaan 'Bapak' atau 'Pak' dalam kalimat."
        elif gender == "female":
            persona = "Gunakan sapaan 'Ibu' atau 'Bu' dalam kalimat."
        else:
            persona = (
                "Jika gender belum diketahui, gunakan sapaan netral seperti 'Bapak/Ibu' atau 'Pak/Bu', "
                "atau tanpa sapaan langsung."
            )

        if missing_field == "name":
            ask_prompt = "Pelanggan belum menyebut nama. Tanyakan nama dengan sopan, maksimal 1 kalimat."
        elif missing_field == "address":
            ask_prompt = "Pelanggan belum menyebut alamat. Tanyakan alamat lengkap dengan sopan."
        elif missing_field == "product":
            ask_prompt = "Pelanggan belum menyebut produk. Tanyakan produk yang dilaporkan dengan sopan."
        elif missing_field == "company":
            ask_prompt = "Tanyakan nama perusahaan (opsional) dengan nada santai dan sopan."
        else:
            ask_prompt = "Tanyakan nomor/serial produk. Jelaskan singkat bahwa jika belum pegang tidak apa-apa."

        system_msg_ask = f"Asisten CS pengumpul data. {persona}"
        reply = self.ollama.generate(
            system=system_msg_ask,
            prompt=ask_prompt,
        ).strip()

        self._log_llm_call(
            func="handle_data_collection_ask",
            user_id=user_id,
            call_type="generate",
            system=system_msg_ask,
            prompt=ask_prompt,
            response=reply,
            meta={"missing_field": missing_field},
        )

        if "anda" in reply.lower():
            short_log(self.logger, user_id, "anti_anda_violation", reply[:120])

        return reply

    def parse_answer_via_llm(self, user_id: str, message: str, expected_results: list, question_context: str = "") -> str:
        msg_lower = message.lower().strip()
        words = msg_lower.split()
        
        positive_keywords = [
            "iya", "ya", "yup", "yoi", "yap", "yes", "ye", "yep",
            "sudah", "udah", "udh", "dah",
            "betul", "benar", "bener", "bnr",
            "nyala", "hidup", "jalan", "berfungsi", "normal", "lancar",
            "oke", "ok", "okay", "oki", "okeh",
            "baik", "bagus", "mantap", "sip", "siap", "iya dong",
            "setuju", "bisa", "tentu", "pastilah", "iyap"
        ]
        
        negative_keywords = [
            "tidak", "tdk", "ga", "gak", "gk", 
            "nggak", "ngga", "enggak", "engga", "nope", "ndak",
            "belum", "blm", "blum",
            "mati", "rusak", "gak nyala", "gak hidup", "gak jalan",
            "no", "nggk", "nda", "ndak",
            "bukan", "ngak", "teu", "ente"
        ]
        
        sering_keywords = ["sering", "sering banget", "kadang", "kadang-kadang", "sometimes", "occasionally", "lumayan sering", "kerap"]
        jarang_keywords = ["jarang", "jarang banget", "rarely", "sesekali", "hampir tidak", "jarang sekali", "sangat jarang"]
        
        if len(words) == 1:
            if msg_lower in positive_keywords:
                return "yes"
            if msg_lower in negative_keywords:
                return "no"
            if msg_lower in sering_keywords:
                return "sering"
            if msg_lower in jarang_keywords:
                return "jarang"
        
        if len(words) <= 3:
            has_positive = sum(1 for kw in positive_keywords if kw in msg_lower)
            has_negative = sum(1 for kw in negative_keywords if kw in msg_lower)
            has_sering = any(kw in msg_lower for kw in sering_keywords)
            has_jarang = any(kw in msg_lower for kw in jarang_keywords)
            
            if has_sering and "sering" in expected_results:
                return "sering"
            if has_jarang and "jarang" in expected_results:
                return "jarang"
            
            if has_positive > has_negative and has_positive > 0:
                return "yes"
            if has_negative > has_positive and has_negative > 0:
                return "no"
            
            if has_positive == has_negative and has_positive > 0:
                if any(w in ["ya", "iya", "sudah", "udah", "oke", "ok"] for w in words):
                    return "yes"
                return "no"
        
        if len(words) <= 5:
            strong_positive_phrases = [
                "iya", "sudah", "udah", "ya sudah", "ya udah", "oke deh", 
                "siap", "bisa", "ok siap", "iya bisa"
            ]
            strong_negative_phrases = [
                "tidak", "belum", "ga", "gak", "nggak", "ngga",
                "belum nih", "ga bisa", "gak bisa", "masih mati"
            ]
            
            for phrase in strong_positive_phrases:
                if phrase in msg_lower:
                    return "yes"
            
            for phrase in strong_negative_phrases:
                if phrase in msg_lower:
                    return "no"
        
        if not message or len(message.strip()) < 2:
            return "unclear"
        
        if len(words) > 10:
            return "unclear"
        
        system_msg = "Kamu adalah answer classifier. Jawab HANYA JSON VALID."
        
        prompt = f"""
        Konteks: User sedang menjawab pertanyaan troubleshooting.
        
        Pertanyaan bot sebelumnya: "{question_context}"
        Jawaban user: "{message}"
        
        Expected results: {expected_results}
        
        Klasifikasikan jawaban ke salah satu kategori:
        - "yes" jika jawaban POSITIF (iya, ya, sudah, udah, udh, betul, benar, nyala, oke, ok, baik, dll)
        - "no" jika jawaban NEGATIF (tidak, belum, blm, ga, gak, nggak, ngga, mati, enggak, dll)
        - "sering" jika menunjukkan frekuensi TINGGI
        - "jarang" jika menunjukkan frekuensi RENDAH
        - "unclear" jika benar-benar tidak jelas atau ambigu
        
        PENTING: Jangan terlalu strict. Jika ada indikasi yes/no, classify sebagai yes/no.
        
        Return HANYA JSON:
        {{
          "result": "yes/no/sering/jarang/unclear",
          "confidence": "high/medium/low"
        }}
        """
        
        full_prompt = self._user_context_header(user_id) + prompt
        
        out = self.ollama.generate_json(system=system_msg, prompt=full_prompt) or {}
        
        self._log_llm_call(
            func="parse_answer_via_llm",
            user_id=user_id,
            call_type="generate_json",
            system=system_msg,
            prompt=full_prompt,
            response=out,
            meta={"expected_results": expected_results, "question_context": question_context, "skipped_due_to_rule": False},
        )
        
        result = out.get("result", "unclear")
        confidence = out.get("confidence", "low")
        
        if result == "unclear":
            if any(kw in msg_lower for kw in positive_keywords):
                return "yes"
            elif any(kw in msg_lower for kw in negative_keywords):
                return "no"
            elif any(kw in msg_lower for kw in sering_keywords):
                return "sering"
            elif any(kw in msg_lower for kw in jarang_keywords):
                return "jarang"
        
        return result

    def get_active_step(self, user_id: str, sop: dict) -> dict:
        intent = self.memstore.get_flag(user_id, "active_intent")
        if not intent or intent not in sop:
            return {
                "intent": None,
                "step_id": None,
                "step_index": None,
                "step_text": None,
                "is_last": False
            }

        steps = sop[intent].get("steps", [])
        if not steps:
            return {
                "intent": intent,
                "step_id": None,
                "step_index": None,
                "step_text": None,
                "is_last": True
            }

        active_step_id = self.memstore.get_flag(user_id, f"{intent}_active_step")
        
        if not active_step_id:
            first_step = steps[0]
            ask_list = first_step.get("ask_templates") or first_step.get("ask") or []
            ask_preview = ask_list[0] if isinstance(ask_list, list) else ask_list
            
            return {
                "intent": intent,
                "step_id": first_step.get("id"),
                "step_index": 0,
                "step_text": ask_preview,
                "is_last": (len(steps) == 1)
            }
        
        for idx, step in enumerate(steps):
            if step.get("id") == active_step_id:
                ask_list = step.get("ask_templates") or step.get("ask") or []
                ask_preview = ask_list[0] if isinstance(ask_list, list) else ask_list
                
                return {
                    "intent": intent,
                    "step_id": step.get("id"),
                    "step_index": idx,
                    "step_text": ask_preview,
                    "is_last": (idx == len(steps) - 1)
                }

        return {
            "intent": intent,
            "step_id": None,
            "step_index": len(steps),
            "step_text": None,
            "is_last": True
        }

    def update_troubleshoot_flags(self, user_id: str, intent: str, step_id: str, result: str):
        self.memstore.set_flag(user_id, step_id, True)

        answer_key = f"{step_id}_answer"
        self.memstore.set_flag(user_id, answer_key, result)

        ts_key = f"{step_id}_ts"
        self.memstore.set_flag(user_id, ts_key, datetime.now(timezone.utc).isoformat())

        completed_steps = self.memstore.get_flag(user_id, f"{intent}_completed_steps") or []
        if step_id not in completed_steps:
            completed_steps.append(step_id)
            self.memstore.set_flag(user_id, f"{intent}_completed_steps", completed_steps)

        self.memstore.set_flag(user_id, "last_step_done", step_id)
        self.memstore.set_flag(user_id, "last_step_result", result)

        return {
            "step_id": step_id,
            "result": result,
            "completed_steps": completed_steps
        }

    def should_trigger_data_collection(self, user_id: str, intent: str) -> bool:
        return self.memstore.get_flag(user_id, "sop_pending") == True

    def summarize_troubleshoot_progress(self, user_id: str, intent: str, sop: dict) -> dict:
        steps = sop.get(intent, {}).get("steps", [])
        completed = self.memstore.get_flag(user_id, f"{intent}_completed_steps") or []
        active = self.get_active_step(user_id, sop)

        last = self.memstore.get_flag(user_id, "last_step_result")

        if self.memstore.get_flag(user_id, "sop_pending"):
            state = "pending"
        elif active["step_id"] is None and last == "yes":
            state = "resolved"
        elif active["step_id"] is None:
            state = "done_unresolved"
        else:
            state = "in_progress"

        return {
            "intent": intent,
            "completed_steps": completed,
            "active_step": active,
            "last_result": last,
            "state": state
        }

    def reset_troubleshoot_state(self, user_id: str, intent: str):
        steps = self.load_sop_from_file().get(intent, {}).get("steps", [])
        for s in steps:
            sid = s["id"]
            self.memstore.clear_flag(user_id, sid)
            self.memstore.clear_flag(user_id, f"{sid}_answer")
            self.memstore.clear_flag(user_id, f"{sid}_ts")
            self.memstore.clear_flag(user_id, f"asked_{sid}")
            self.memstore.clear_flag(user_id, f"{sid}_waiting_confirm")
            self.memstore.clear_flag(user_id, f"{sid}_confirm_data")

        self.memstore.clear_flag(user_id, f"{intent}_completed_steps")
        self.memstore.clear_flag(user_id, f"{intent}_active_step")
        self.memstore.clear_flag(user_id, f"{intent}_clarify_count")
        self.memstore.clear_flag(user_id, "last_step_done")
        self.memstore.clear_flag(user_id, "last_step_result")
        self.memstore.clear_flag(user_id, "sop_pending")
        self.memstore.clear_flag(user_id, "active_intent")

    def _track_intent_change(self, user_id: str, new_intent: str) -> bool:
        last_intent = self.memstore.get_flag(user_id, "last_processed_intent")
        
        if last_intent != new_intent:
            self.memstore.set_flag(user_id, "last_processed_intent", new_intent)
            return True
        
        return False
    
    def _detect_additional_complaint_python(self, message: str, active_intent: str) -> str:
        if not active_intent or active_intent == "none":
            return "none"
        
        msg_lower = message.lower().strip()
        
        chitchat_only = [
            "terimakasih", "terima kasih", "makasih", "thanks", "thank you",
            "ok", "oke", "okay", "baik", "sip", "siap", "ya", "iya", "yup",
            "halo", "hai", "hi", "pagi", "siang", "sore", "malam",
        ]
        
        if msg_lower in chitchat_only or len(msg_lower.split()) <= 2:
            if any(chat in msg_lower for chat in chitchat_only):
                return "none"
        
        mati_keywords = [
            "mati", "tidak menyala", "gak nyala", "ga nyala", "ngga nyala", "nggak nyala",
            "tidak hidup", "gak hidup", "ga hidup", "off", "padam", "tidak berfungsi"
        ]
        
        bau_keywords = [
            "bau", "aroma", "baud", "bauk", "aromanya", "baunya", "amis", "anyir",
            "menyengat", "tidak sedap", "gak sedap", "tidak enak", "gak enak"
        ]
        
        bunyi_keywords = [
            "bunyi", "suara", "berisik", "bising", "berisiknya", "noise", "ribut",
            "keras", "berisik sekali", "bunyi aneh", "suara aneh", "dengung", "berdengung"
        ]
        
        detected_mati = any(kw in msg_lower for kw in mati_keywords)
        detected_bau = any(kw in msg_lower for kw in bau_keywords)
        detected_bunyi = any(kw in msg_lower for kw in bunyi_keywords)
        
        if active_intent == "mati":
            if detected_bau and not detected_bunyi:
                return "bau"
            elif detected_bunyi and not detected_bau:
                return "bunyi"
            elif detected_bau and detected_bunyi:
                if "bau" in msg_lower and msg_lower.index("bau") < msg_lower.index("bunyi"):
                    return "bau"
                else:
                    return "bunyi"
        
        elif active_intent == "bau":
            if detected_mati and not detected_bunyi:
                return "mati"
            elif detected_bunyi and not detected_mati:
                return "bunyi"
            elif detected_mati and detected_bunyi:
                if "mati" in msg_lower and msg_lower.index("mati") < msg_lower.index("bunyi"):
                    return "mati"
                else:
                    return "bunyi"
        
        elif active_intent == "bunyi":
            if detected_mati and not detected_bau:
                return "mati"
            elif detected_bau and not detected_mati:
                return "bau"
            elif detected_mati and detected_bau:
                if "mati" in msg_lower and msg_lower.index("mati") < msg_lower.index("bau"):
                    return "mati"
                else:
                    return "bau"
        
        return "none"
    
    def _queue_additional_complaint(self, user_id: str, complaint_type: str) -> None:
        queued = self.memstore.get_flag(user_id, "queued_complaints") or []
        
        if complaint_type not in queued and complaint_type != "none":
            queued.append(complaint_type)
            self.memstore.set_flag(user_id, "queued_complaints", queued)
    
    def _get_queued_complaints(self, user_id: str) -> list:
        return self.memstore.get_flag(user_id, "queued_complaints") or []
    
    def _clear_queued_complaints(self, user_id: str) -> None:
        self.memstore.clear_flag(user_id, "queued_complaints")
    
    def _detect_competitor_mention(self, message: str) -> dict:
        msg_lower = message.lower()
        
        competitors = {
            "daikin": ["daikin", "daiken"],
            "panasonic": ["panasonic"],
            "lg": ["lg", "l g", "el ji"],
            "sharp": ["sharp", "syarp"],
            "samsung": ["samsung"],
            "gree": ["gree"],
            "polytron": ["polytron"],
            "midea": ["midea"],
            "aux": ["aux"],
            "haier": ["haier"]
        }
        
        for brand, keywords in competitors.items():
            for kw in keywords:
                if kw in msg_lower:
                    return {"has_competitor": True, "brand": brand}
        
        return {"has_competitor": False, "brand": None}
    
    def _classify_distraction_type(self, message: str) -> str:
        msg_lower = message.lower()
        
        competitor_check = self._detect_competitor_mention(message)
        if competitor_check["has_competitor"]:
            return "competitor"
        
        question_indicators = ["?", "apa", "kenapa", "gimana", "bagaimana", "kapan", "dimana", "berapa", "apakah", "bisakah", "boleh", "harga", "biaya", "teknisi", "garansi"]
        if any(kw in msg_lower for kw in question_indicators):
            return "question"
        
        chitchat_indicators = ["panas", "dingin", "hujan", "cuaca", "terima kasih", "makasih", "thanks", "oke", "ok", "baik", "siap"]
        if any(kw in msg_lower for kw in chitchat_indicators):
            return "chitchat"
        
        return "unclear"
    
    def _generate_distraction_response(self, user_id: str, message: str, dtype: str, follow_up: str) -> str:
        if dtype == "competitor":
            competitor_info = self._detect_competitor_mention(message)
            brand = competitor_info.get("brand", "produk lain")
            
            responses = [
                f"Maaf kak, kami khusus handle produk Honeywell. Untuk {brand} bisa hubungi service center mereka ya.",
                f"Kami dari tim Honeywell kak, jadi fokusnya di produk Honeywell. Ada yang bisa dibantu untuk produk Honeywell?"
            ]
            response = random.choice(responses)
            return f"{response} {follow_up}"
        
        elif dtype == "question":
            system_msg = "CS Honeywell yang helpful."
            prompt = f"""Customer: "{message}"\nJawab SINGKAT (maks 8 kata):\n- Harga/biaya → "Akan kami konfirmasi kak"\n- Teknisi/jadwal → "Nanti kami kabari kak"\n- Garansi → "1 tahun kak"\nJangan kata "Anda". Response:"""
            response = self.ollama.generate(system=system_msg, prompt=prompt).strip()
            return f"{response} Balik ke EAC nya ya, {follow_up.lower()}"
        
        elif dtype == "chitchat":
            system_msg = "CS ramah."
            prompt = f"""Customer: "{message}"\nJawab SANGAT SINGKAT (4-5 kata), natural:\n- "panas ya" → "Iya kak, memang terik."\n- "makasih" → "Sama-sama kak."\nResponse:"""
            response = self.ollama.generate(system=system_msg, prompt=prompt).strip()
            return f"{response} Oh iya kak, {follow_up.lower()}"
        
        return follow_up
    
    def _generate_acknowledge_and_redirect(
        self, 
        user_id: str, 
        additional_complaint: str, 
        active_intent: str,
        troubleshoot_question: str
    ) -> str:
        complaint_map = {
            "mati": "tidak menyala",
            "bau": "bau tidak sedap", 
            "bunyi": "bunyi tidak normal"
        }
        
        additional_text = complaint_map.get(additional_complaint, additional_complaint)
        active_text = complaint_map.get(active_intent, active_intent)
        
        system_msg = "Kamu adalah CS Honeywell yang ramah dan fokus."
        
        prompt = f"""
        Generate response natural untuk acknowledge keluhan tambahan tapi redirect ke troubleshooting aktif.
        
        Keluhan tambahan yang disebutkan: {additional_text}
        Keluhan yang sedang ditangani: {active_text}
        Pertanyaan troubleshoot berikutnya: "{troubleshoot_question}"
        
        Format response:
        1. Acknowledge keluhan tambahan dengan singkat (maksimal 5 kata)
        2. Redirect ke troubleshooting aktif dengan smooth transition
        3. Lanjutkan dengan pertanyaan troubleshoot
        
        Contoh bagus:
        - "Baik kak, saya catat juga ada bunyi. Tapi kita selesaikan yang tidak menyala dulu ya? {troubleshoot_question.lower()}"
        - "Oke kak, untuk bau nya saya catat. Kita fokus dulu ke yang mati ya? {troubleshoot_question.lower()}"
        
        PENTING:
        - Maksimal 2 kalimat
        - Natural dan tidak kaku
        - Jangan gunakan kata "Anda"
        - Gunakan "kita" atau "kami"
        
        Generate HANYA response (tanpa tanda kutip):
        """
        
        full_prompt = self._user_context_header(user_id) + prompt
        
        response = self.ollama.generate(system=system_msg, prompt=full_prompt).strip()
        
        self._log_llm_call(
            func="_generate_acknowledge_and_redirect",
            user_id=user_id,
            call_type="generate",
            system=system_msg,
            prompt=full_prompt,
            response=response,
            meta={
                "additional_complaint": additional_complaint,
                "active_intent": active_intent,
                "troubleshoot_question": troubleshoot_question
            }
        )
        
        return response

    def sop_reset_state(self, user_id: str):
        sop = self.load_sop_from_file()
        intents = [k for k in sop.keys() if k != "rules"]

        for intent in intents:
            self.reset_troubleshoot_state(user_id, intent)

        return {"status": "ok", "msg": "SOP state reset."}

    def sop_status(self, user_id: str) -> dict:
        sop = self.load_sop_from_file()
        intents = [k for k in sop.keys() if k != "rules"]

        report = {}

        for intent in intents:
            summary = self.summarize_troubleshoot_progress(user_id, intent, sop)
            report[intent] = summary

        return report

    def _build_sop_state(self, user_id: str, intent: str, sop: dict) -> dict:
        
        if intent not in sop or intent in ("rules", "metadata"):
            return {
                "intent": intent,
                "active_step": None,
                "completed_steps": [],
                "all_steps": [],
                "metadata": sop.get("metadata", {}),
                "flags": {}
            }

        active = self.get_active_step(user_id, sop)
        completed_steps = self.memstore.get_flag(user_id, f"{intent}_completed_steps") or []
        
        all_steps = sop[intent].get("steps", [])
        
        step_def = None
        if active["step_id"]:
            step_def = next((s for s in all_steps if s["id"] == active["step_id"]), None)
        
        step_answers = {}
        for step in all_steps:
            step_id = step["id"]
            answer = self.memstore.get_flag(user_id, f"{step_id}_answer")
            if answer:
                step_answers[step_id] = answer
        
        flags = {
            "active_intent": self.memstore.get_flag(user_id, "active_intent"),
            "sop_pending": self.memstore.get_flag(user_id, "sop_pending"),
            "last_step_done": self.memstore.get_flag(user_id, "last_step_done"),
            "last_step_result": self.memstore.get_flag(user_id, "last_step_result"),
        }
        
        confirm_flag = f"{active['step_id']}_waiting_confirm" if active["step_id"] else None
        confirm_data = None
        if confirm_flag:
            if self.memstore.get_flag(user_id, confirm_flag):
                confirm_data = self.memstore.get_flag(user_id, f"{active['step_id']}_confirm_data")
        
        return {
            "intent": intent,
            "active_step": active,
            "step_def": step_def,
            "completed_steps": completed_steps,
            "all_steps": all_steps,
            "step_answers": step_answers,
            "metadata": sop.get("metadata", {}),
            "flags": flags,
            "waiting_confirm": confirm_flag is not None and self.memstore.get_flag(user_id, confirm_flag),
            "confirm_data": confirm_data
        }

    def _is_explicit_resolution(self, message: str) -> bool:
        msg_lower = message.lower().strip()
        
        negative_indicators = [
            'tidak', 'belum', 'masih', 'ga', 'gak',
            'nggak', 'enggak', 'kagak', 'ndak', 'blm',
            'tdk', 'gk', 'ngga', 'nggak'
        ]
        
        if any(neg in msg_lower for neg in negative_indicators):
            return False
        
        resolution_patterns = [
            'sudah menyala',
            'sudah nyala',
            'sudah hidup',
            'sudah berfungsi',
            'sudah jalan',
            'sudah normal',
            'sudah ok',
            'sudah oke',
            'alat sudah',
            'unit sudah',
            'sudah baik',
            'sudah bisa',
            'berhasil',
            'bisa nyala',
            'bisa menyala',
            'kembali normal',
            'kembali hidup',
            'menyala kembali',
            'nyala kembali',
        ]
        
        return any(pattern in msg_lower for pattern in resolution_patterns)
    
    def _is_simple_acknowledge(self, message: str) -> bool:
        msg_lower = message.lower().strip()
        words = msg_lower.split()
        
        if len(words) > 3:
            return False
        
        simple_acks = ['iya', 'ya', 'ok', 'oke', 'baik', 'sip', 'siap']
        return msg_lower in simple_acks or (len(words) <= 2 and all(w in simple_acks for w in words))
    
    def _check_spam_or_profanity(self, user_id: str, message: str) -> Dict[str, bool]:
        msg_lower = message.lower().strip()
        msg_clean = msg_lower.replace(' ', '')
        
        profanity_keywords = [
            'anjg', 'anjing', 'asu', 'babi', 'bangsat', 'bajingan', 'kontol', 
            'memek', 'ngentot', 'jancok', 'tolol', 'goblok', 'bodoh', 'idiot',
            'fuck', 'shit', 'bitch', 'damn', 'cunt', 'dick', 'pussy', 'ass',
            'tai', 'taik', 'sial', 'sialan', 'kampret', 'monyet', 'kimak',
            'cok', 'njing', 'njir', 'asw'
        ]
        
        is_profanity = any(word in msg_lower.split() or word in msg_clean for word in profanity_keywords)
        
        is_spam = False
        
        if len(message) <= 3 and not any(char.isalpha() for char in message):
            is_spam = True
        
        nonsense_patterns = [
            'al', 'ohokkk', 'affh', 'tll', 'maksa', 'ga', 'gaa', 'gaaa'
        ]
        
        if msg_clean in nonsense_patterns:
            is_spam = True
        
        if len(msg_clean) <= 3 and msg_clean.isalpha() and msg_clean not in ['eac', 'iya', 'ya', 'ok', 'oke']:
            is_spam = True
        
        return {
            "is_spam": is_spam,
            "is_profanity": is_profanity
        }

    def _parse_user_answer(self, message: str, expected_result: list) -> str:
        """Parse user answer dengan Python rule-based (TIDAK pakai LLM)"""
        msg_lower = message.lower().strip()
        words = msg_lower.split()
        
        yes_keywords = ['ya', 'iya', 'sudah', 'benar', 'betul', 'oke', 'ok', 'yes', 
                       'menyala', 'berfungsi', 'normal', 'hidup', 'nyala', 'on',
                       'udah', 'udh', 'yup', 'yep', 'yoi', 'sip', 'siap', 'iyap']
        no_keywords = ['tidak', 'belum', 'no', 'nggak', 'enggak', 'gak', 'ga', 
                      'rusak', 'nope', 'off', 'mati', 'blm', 'blum', 'tdk', 'gk',
                      'ngga', 'ndak', 'bukan', 'masih']
        
        sering_keywords = ['sering', 'kadang', 'sometimes', 'occasionally', 
                          'kadang-kadang', 'kerap', 'terus-terusan', 'terus', 
                          'banget', 'sekali', 'sangat', 'frequently']
        jarang_keywords = ['jarang', 'rarely', 'sesekali', 'hampir tidak', 'sangat jarang']
        
        positive_phrases = [
            'sudah rapat', 'sudah tertutup', 'sudah on', 'sudah dikunci',
            'sudah menyala', 'sudah nyala', 'sudah hidup', 'sudah berfungsi',
            'sudah normal', 'sudah ok', 'sudah oke', 'udah rapat', 'udah nyala',
            'iya sudah', 'ya sudah', 'iya', 'ya', 'ok', 'oke', 'baik', 'siap'
        ]
        
        negative_phrases = [
            'belum rapat', 'belum tertutup', 'belum on', 'belum dikunci',
            'tidak menyala', 'tidak nyala', 'tidak hidup', 'tidak berfungsi',
            'gak menyala', 'gak nyala', 'masih mati', 'masih tidak', 'masih gak',
            'tetap mati', 'tetap tidak', 'belum menyala', 'belum nyala',
            'masih tidak nyala', 'masih belum', 'ngga nyala', 'ngga menyala'
        ]
        
        sering_phrases = [
            'sering banget', 'sering sekali', 'sangat sering', 'terus-terusan',
            'terus menerus', 'setiap saat', 'tiap saat', 'hampir selalu',
            'always', 'continuously', 'all the time'
        ]
        
        jarang_phrases = [
            'jarang banget', 'jarang sekali', 'sangat jarang', 'hampir tidak pernah',
            'kadang-kadang saja', 'sesekali saja', 'sesekali aja', 'rarely'
        ]
        
        if 'sering' in expected_result or 'jarang' in expected_result:
            for phrase in sering_phrases:
                if phrase in msg_lower:
                    return 'sering'
            
            for phrase in jarang_phrases:
                if phrase in msg_lower:
                    return 'jarang'
            
            has_sering = any(kw in msg_lower for kw in sering_keywords)
            has_jarang = any(kw in msg_lower for kw in jarang_keywords)
            
            if has_sering and not has_jarang:
                return 'sering'
            if has_jarang and not has_sering:
                return 'jarang'
            
            if any(word in msg_lower for word in ['terus', 'banget', 'sekali', 'sangat']):
                if not has_jarang:
                    return 'sering'
        
        if 'yes' in expected_result or 'no' in expected_result:
            ambiguous_phrases = [
                'sudah dicoba', 'sudah coba', 'sudah saya coba', 'sudah di coba',
                'sudah saya', 'sudah aku', 'sudah kucoba', 'sudah ku coba'
            ]
            if any(phrase in msg_lower for phrase in ambiguous_phrases):
                return 'unclear'
            
            for phrase in negative_phrases:
                if phrase in msg_lower:
                    return 'no'
            
            for phrase in positive_phrases:
                if phrase in msg_lower:
                    return 'yes'
            
            has_yes_words = sum(1 for word in words if word in yes_keywords)
            has_no_words = sum(1 for word in words if word in no_keywords)
            
            if has_yes_words > 0 and has_no_words == 0:
                return 'yes'
            
            if has_no_words > 0 and has_yes_words == 0:
                return 'no'
            
            if has_yes_words > 0 and has_no_words > 0:
                negative_context = ['masih', 'belum', 'tetap', 'tidak', 'gak', 'ga']
                if any(word in words for word in negative_context):
                    return 'no'
                
                strong_yes = ['sudah', 'ya', 'iya', 'ok', 'oke', 'benar', 'betul', 'udah']
                if any(word in strong_yes for word in words):
                    return 'yes'
                
                return 'no'
        
        return 'unclear'

    def _is_step_already_asked(self, user_id: str, step_id: str, step_text: str) -> bool:
        
        history = self.memstore.get(user_id).get("history", [])
        
        if len(history) < 2:
            return False
        
        last_msg = history[-1]
        if last_msg["role"] != "user":
            return False
        
        second_last = history[-2] if len(history) >= 2 else None
        if second_last and second_last["role"] == "bot":
            return True
        
        return False

    def _llm_decide_next_action(self, user_id: str, message: str, sop_state: dict, intent: str) -> dict:
        history = self.memstore.get_history(user_id)
        last_bot_msg = ""
        for h in reversed(history):
            if h["role"] == "bot":
                last_bot_msg = h["text"]
                break
        
        step_already_asked = False
        if sop_state["active_step"] and last_bot_msg:
            step_text = sop_state["active_step"].get("step_text", "")
            if step_text and step_text in last_bot_msg:
                step_already_asked = True
        
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        todays_messages = []
        for h in history:
            if h["ts"].startswith(today):
                role = "Bot" if h["role"] == "bot" else "User"
                todays_messages.append(f"{role}: {h['text']}")
        history_block = "\\n".join(todays_messages) if todays_messages else "(Tidak ada percakapan hari ini)"
        
        system_msg = (
            "Kamu adalah SOP Decision Engine untuk troubleshooting Honeywell. "
            "Tugasmu adalah membaca SOP JSON dan menentukan action selanjutnya berdasarkan state saat ini. "
            "Jawab HANYA JSON VALID. DILARANG menambah field atau mengubah format."
        )
        
        prompt = f"""
        {self._user_context_header(user_id)}

        RIWAYAT PERCAKAPAN HARI INI:
        {history_block}

        PESAN TERAKHIR BOT:
        "{last_bot_msg}"

        PESAN USER SAAT INI:
        "{message}"

        ===== SOP STATE =====
        Intent: {sop_state["intent"]}
        
        Active Step:
        {json.dumps(sop_state["active_step"], ensure_ascii=False, indent=2)}
        
        Step Already Asked: {"YA - step ini sudah ditanyakan ke user" if step_already_asked else "TIDAK - step ini belum ditanyakan"}
        
        Step Definition (lengkap dengan logic):
        {json.dumps(sop_state["step_def"], ensure_ascii=False, indent=2) if sop_state["step_def"] else "null"}
        
        Completed Steps: {sop_state["completed_steps"]}
        
        Step Answers (jawaban user di step sebelumnya):
        {json.dumps(sop_state["step_answers"], ensure_ascii=False, indent=2)}
        
        Flags:
        {json.dumps(sop_state["flags"], ensure_ascii=False, indent=2)}
        
        Waiting Confirm: {sop_state["waiting_confirm"]}
        Confirm Data: {json.dumps(sop_state["confirm_data"], ensure_ascii=False, indent=2) if sop_state["confirm_data"] else "null"}
        
        Metadata Templates:
        {json.dumps(sop_state["metadata"], ensure_ascii=False, indent=2)}
        
        ===== CONSTRAINT KETAT =====
        1. HARUS mengikuti "logic" dari step_def
        2. TIDAK BOLEH skip step atau membuat keputusan di luar SOP
        3. HARUS mempertimbangkan "expected_result" dan "on_answer_*" logic
        4. Jika waiting_confirm=true, ini adalah jawaban konfirmasi dari user
        5. Jika step_def null, berarti semua step selesai → pending atau resolve
        6. Parse jawaban user berdasarkan expected_result di step_def
        7. Jika "Step Already Asked" = YA, berarti user sedang menjawab pertanyaan step ini
        
        ===== DECISION LOGIC =====
        
        A. Jika waiting_confirm=true:
           - Parse jawaban user (yes/no)
           - Ikuti logic dari confirm_data["branch"]
           - Jika resolve_if_yes=true dan user jawab yes → action="resolve"
           - Jika next_if_no ada dan user jawab no → action="next", next_step_id=<id>
           - Jika pending_if_no=true dan user jawab no → action="pending"
        
        B. Jika step_def tidak null dan "Step Already Asked" = TIDAK:
           - action="ask"
           - template_key="ask_templates"
        
        C. Jika step_def tidak null dan "Step Already Asked" = YA:
           - Parse jawaban user berdasarkan expected_result
           - Jika jawaban unclear → action="clarify"
           - Ambil logic berdasarkan jawaban: on_answer_yes / on_answer_no / on_answer_sering / on_answer_jarang
           - Jika logic["instruct"]=true → action="instruct", template_key="instruct_templates"
           - Jika logic["confirm"]=true → action="confirm", template_key="confirm_templates"
           - Jika logic["offer"]=true → action="offer", template_key="offer_templates"
           - Jika logic["resolve"]=true → action="resolve", template_key="resolve_templates"
           - Jika logic["pending"]=true → action="pending", template_key="pending_templates"
           - Jika logic["next"] ada → action="next", next_step_id=<id>
        
        D. Jika step_def null (semua step selesai):
           - Cek last_step_result
           - Jika last_step_result="yes" → action="resolve"
           - Jika last_step_result="no" atau "sering" → action="pending"
        
        ===== OUTPUT FORMAT =====
        Kembalikan HANYA JSON:
        {{
          "action": "ask/confirm/instruct/resolve/pending/next/clarify/offer",
          "template_key": "ask_templates/confirm_templates/instruct_templates/resolve_templates/pending_templates/offer_templates/null",
          "next_step_id": "<step_id jika action=next, atau null>",
          "user_answer": "<parsed answer: yes/no/sering/jarang/unclear>",
          "reason": "<penjelasan singkat kenapa memilih action ini>"
        }}
        
        PENTING: 
        - Jangan buat keputusan sendiri, ikuti SOP logic dengan ketat
        - Jika "Step Already Asked" = YA, berarti user sedang menjawab, JANGAN ask lagi
        - Pastikan template_key sesuai dengan yang ada di step_def
        """
        
        out = self.ollama.generate_json(system=system_msg, prompt=prompt) or {}
        
        self._log_llm_call(
            func="_llm_decide_next_action",
            user_id=user_id,
            call_type="generate_json",
            system=system_msg,
            prompt=prompt,
            response=out,
            meta={
                "intent": intent,
                "active_step_id": sop_state["active_step"]["step_id"] if sop_state["active_step"] else None,
                "waiting_confirm": sop_state["waiting_confirm"],
                "step_already_asked": step_already_asked,
            },
        )
        
        out.setdefault("action", "clarify")
        out.setdefault("template_key", None)
        out.setdefault("next_step_id", None)
        out.setdefault("user_answer", "unclear")
        out.setdefault("reason", "")
        
        return out

    def _naturalize_template(self, user_id: str, template_text: str, action_type: str) -> str:
        history = self.memstore.get_history(user_id)
        last_user_msg = ""
        for h in reversed(history):
            if h["role"] == "user":
                last_user_msg = h["text"]
                break
        
        system_msg = "Kamu adalah CS Honeywell yang ramah, sopan, dan profesional. Gunakan bahasa Indonesia yang baik dan benar."
        
        prompt = f"""Tugas: Ubah template SOP menjadi lebih natural TANPA mengubah makna atau informasi yang ada.

        Pesan terakhir customer: "{last_user_msg}"

        Template SOP: "{template_text}"

        Aturan WAJIB:
        1. PERTAHANKAN semua informasi dari template - jangan tambah, kurang, atau ubah
        2. Tetap profesional dan sopan sebagai customer service
        3. Gunakan bahasa Indonesia yang baik dan benar - JANGAN gunakan bahasa asing
        4. DILARANG gunakan bahasa gaul: "dong", "aja", "gitu", "sih", "gimana", "ngga"
        5. DILARANG gunakan kata serapan salah: "teknisian" (gunakan "teknisi")
        6. Gunakan "kak" untuk sapaan
        7. Tidak gunakan kata "Anda"
        8. Maksimal 3 kalimat
        9. Hindari tanda kutip
        10. Jangan bertele-tele
        11. JANGAN mengarang atau mengubah konteks - ikuti template dengan ketat

        Contoh konversi yang BENAR:
        Template: "Baik kak, saya teruskan ke teknisi ya."
        Natural: "Baik kak, saya bantu teruskan ke teknisi ya."

        Template: "Kak, bisa dicek posisi MCB-nya apakah sedang di posisi ON?"
        Natural: "Kak, boleh dicek apakah MCB-nya sudah dalam posisi ON?"

        Contoh konversi yang SALAH (jangan seperti ini):
        Template: "Baik kak, saya teruskan ke teknisi ya."
        SALAH: "Teruskan dong ke teknisi ya..." ❌ (bahasa gaul)
        SALAH: "Buat nyambung aja kita cek..." ❌ (mengubah makna)

        Ubah template di atas menjadi lebih natural dalam BAHASA INDONESIA:"""
        
        reply = self.ollama.generate(system=system_msg, prompt=prompt).strip()
        
        # Cleanup kutip jika masih ada
        reply = reply.replace('"', '').replace("'", '')
        
        # Safety check: jika ada karakter non-latin (bahasa asing), gunakan template asli
        try:
            # Cek apakah ada karakter CJK (Chinese, Japanese, Korean)
            cjk_pattern = r'[\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff\uac00-\ud7af]'
            import re
            if re.search(cjk_pattern, reply):
                short_log(self.logger, user_id, "naturalize_fallback", f"Foreign chars detected, use template")
                reply = template_text
        except Exception:
            pass
        
        self._log_llm_call(
            func="_naturalize_template",
            user_id=user_id,
            call_type="generate",
            system=system_msg,
            prompt=prompt,
            response=reply,
            meta={"template_text": template_text, "action_type": action_type}
        )
        
        return reply

    def _generate_natural_fallback(self, user_id: str, message: str, context: str) -> str:
        history = self.memstore.get_history(user_id)
        last_bot_msg = ""
        for h in reversed(history):
            if h["role"] == "bot":
                last_bot_msg = h["text"]
                break
        
        identity = self.memstore.get_identity(user_id)
        gender = identity.get("gender")
        salutation = "Pak" if gender == "male" else "Bu" if gender == "female" else "Kak"
        
        system_msg = "Kamu adalah CS Honeywell yang ramah dan natural. Bukan chatbot kaku."
        
        context_map = {
            "no_step_def": "Customer mengirim pesan tapi sistem tidak menemukan step troubleshooting yang sesuai",
            "no_logic": "Customer menjawab pertanyaan troubleshooting tapi jawabannya tidak jelas atau tidak sesuai ekspektasi",
            "general": "Kondisi umum dimana bot perlu waktu untuk memproses atau mengecek sesuatu",
            "chitchat_no_intent": "Customer ngobrol chitchat tapi tidak ada keluhan yang jelas",
            "no_intent": "Customer mengirim pesan tapi tidak terdeteksi keluhan spesifik tentang EAC"
        }
        
        context_desc = context_map.get(context, "Kondisi umum")
        
        prompt = f"""Situasi: {context_desc}

        Pesan terakhir bot: "{last_bot_msg}"
        Pesan customer: "{message}"

        Tugas: Generate respon natural untuk meminta klarifikasi atau informasi lebih lanjut.

        Aturan PENTING:
        1. Jangan terdengar seperti chatbot - hindari frasa formal seperti:
        ❌ "Maaf kak, saya belum menangkap keluhan spesifiknya"
        ❌ "Bisa dijelaskan lebih detail?"
        ❌ "Izinkan saya cek lebih lanjut"
        
        2. Gunakan bahasa natural seperti manusia:
        ✅ "Hmm, boleh dijelaskan lagi kak? Saya kurang tangkap maksudnya"
        ✅ "Oh, jadi masalahnya gimana ya kak? Biar saya bisa bantu lebih baik"
        ✅ "Oke kak, coba ceritakan lagi keluhan EAC nya seperti apa?"
        
        3. Variasikan respon - jangan monoton
        4. Maksimal 2 kalimat pendek
        5. Gunakan sapaan "{salutation}"
        6. Fokus ke keluhan EAC jika context tentang intent
        7. Natural dan conversational

        Generate HANYA response (tanpa tanda kutip):"""
        
        reply = self.ollama.generate(system=system_msg, prompt=prompt).strip()
        reply = reply.replace('"', '').replace("'", '')
        
        self._log_llm_call(
            func="_generate_natural_fallback",
            user_id=user_id,
            call_type="generate",
            system=system_msg,
            prompt=prompt,
            response=reply,
            meta={"context": context, "message": message}
        )
        
        return reply


    def _execute_llm_decision(self, user_id: str, decision: dict, intent: str, sop: dict) -> dict:
        
        action = decision.get("action", "clarify")
        template_key = decision.get("template_key")
        next_step_id = decision.get("next_step_id")
        user_answer = decision.get("user_answer", "unclear")
        
        meta = sop.get("metadata", {})
        sop_state = self._build_sop_state(user_id, intent, sop)
        step_def = sop_state.get("step_def")
        active_step_id = sop_state["active_step"]["step_id"] if sop_state["active_step"] else None
        
        if action == "clarify":
            clarify_count = self.memstore.get_flag(user_id, f"{intent}_clarify_count") or 0
            clarify_count += 1
            self.memstore.set_flag(user_id, f"{intent}_clarify_count", clarify_count)
            
            short_log(self.logger, user_id, "clarify_count", f"Intent: {intent}, Count: {clarify_count}/3")
            
            if clarify_count >= 3:
                self.memstore.set_flag(user_id, f"{intent}_clarify_count", 0)
                
                escalate_msg = "Baik kak, sepertinya perlu pengecekan lebih detail oleh teknisi kami. Boleh saya bantu jadwalkan kunjungan teknisi?"
                self.memstore.append_history(user_id, "bot", escalate_msg)
                
                self.memstore.set_flag(user_id, "sop_pending", True)
                self.memstore.set_flag(user_id, "pending_just_triggered", True)
                
                short_log(self.logger, user_id, "clarify_escalated", f"Auto-escalate after {clarify_count} clarifications")
                
                return {"bubbles": [{"text": escalate_msg}], "next": "await_reply", "status": "open"}
            
            clarify_list = meta.get("general_templates", {}).get("clarify", [])
            clarify = random.choice(clarify_list) if clarify_list else "Boleh dijelaskan sedikit lagi kak?"
            self.memstore.append_history(user_id, "bot", clarify)
            return {"bubbles": [{"text": clarify}], "next": "await_reply"}

        
        if action == "ask":
            if not step_def or not active_step_id:
                fallback = "Baik kak, izinkan saya cek lebih lanjut ya."
                self.memstore.append_history(user_id, "bot", fallback)
                return {"bubbles": [{"text": fallback}], "next": "await_reply"}
            
            ask_flag = f"asked_{active_step_id}"
            if self.memstore.get_flag(user_id, ask_flag):
                fallback = "Baik kak, izinkan saya cek lebih lanjut ya."
                self.memstore.append_history(user_id, "bot", fallback)
                return {"bubbles": [{"text": fallback}], "next": "await_reply"}
            
            self.memstore.set_flag(user_id, ask_flag, True)
            
            ask_list = step_def.get("ask_templates") or step_def.get("ask") or []
            ask_text = random.choice(ask_list) if ask_list else "(template ask kosong)"
            
            reply = self._naturalize_template(user_id, ask_text, "ask")
            
            self.memstore.append_history(user_id, "bot", reply)
            return {"bubbles": [{"text": reply}], "next": "await_reply"}
        
        if action == "instruct":
            if not step_def:
                fallback = "Baik kak, izinkan saya cek lebih lanjut ya."
                self.memstore.append_history(user_id, "bot", fallback)
                return {"bubbles": [{"text": fallback}], "next": "await_reply"}
            
            instruct_list = step_def.get("instruct_templates") or []
            instruct_text = random.choice(instruct_list) if instruct_list else "(template instruct kosong)"
            
            reply = self._naturalize_template(user_id, instruct_text, "instruct")
            
            self.memstore.append_history(user_id, "bot", reply)
            return {"bubbles": [{"text": reply}], "next": "await_reply"}
        
        if action == "confirm":
            if not step_def or not active_step_id:
                fallback = "Baik kak, izinkan saya cek lebih lanjut ya."
                self.memstore.append_history(user_id, "bot", fallback)
                return {"bubbles": [{"text": fallback}], "next": "await_reply"}
            
            if user_answer != "unclear" and active_step_id:
                self.update_troubleshoot_flags(user_id, intent, active_step_id, user_answer)
            
            confirm_list = step_def.get("confirm_templates") or []
            confirm_text = random.choice(confirm_list) if confirm_list else "(template confirm kosong)"
            
            confirm_flag = f"{active_step_id}_waiting_confirm"
            confirm_data_flag = f"{active_step_id}_confirm_data"
            
            logic_key = f"on_answer_{user_answer}"
            branch = step_def.get("logic", {}).get(logic_key, {})
            
            self.memstore.set_flag(user_id, confirm_flag, True)
            self.memstore.set_flag(user_id, confirm_data_flag, {
                "original_result": user_answer,
                "branch": branch
            })
            
            reply = self._naturalize_template(user_id, confirm_text, "confirm")
            
            self.memstore.append_history(user_id, "bot", reply)
            return {"bubbles": [{"text": reply}], "next": "await_reply"}
        
        if action == "offer":
            if not step_def:
                fallback = "Baik kak, izinkan saya cek lebih lanjut ya."
                self.memstore.append_history(user_id, "bot", fallback)
                return {"bubbles": [{"text": fallback}], "next": "await_reply"}
            
            offer_list = step_def.get("offer_templates") or []
            offer_text = random.choice(offer_list) if offer_list else "(template offer kosong)"
            
            reply = self._naturalize_template(user_id, offer_text, "offer")
            
            self.memstore.append_history(user_id, "bot", reply)
            return {"bubbles": [{"text": reply}], "next": "await_reply"}
        
        if action == "resolve":
            if not self._is_explicit_resolution(message):
                short_log(self.logger, user_id, "prevent_premature_resolve", 
                         f"LLM want resolve but no explicit confirmation from user")
                
                confirm_msg = "Apakah alatnya sudah berfungsi normal kak?"
                self.memstore.append_history(user_id, "bot", confirm_msg)
                
                if active_step_id:
                    self.memstore.set_flag(user_id, f"{active_step_id}_waiting_confirm", True)
                    self.memstore.set_flag(user_id, f"{active_step_id}_confirm_data", {
                        "resolve_if_yes": True,
                        "next_if_no": None,
                        "pending_if_no": True
                    })
                
                return {"bubbles": [{"text": confirm_msg}], "next": "await_reply"}
            
            if step_def:
                resolve_list = step_def.get("resolve_templates") or meta.get("general_templates", {}).get("closing_resolved", [])
            else:
                resolve_list = meta.get("general_templates", {}).get("closing_resolved", [])
            
            resolve_template = random.choice(resolve_list) if resolve_list else "Baik kak, saya tutup laporannya ya."
            resolve_msg = self._naturalize_template(user_id, resolve_template, "resolve")
            
            self.memstore.append_history(user_id, "bot", resolve_msg)
            
            self.memstore.set_flag(user_id, "sop_resolved", True)
            self.memstore.clear_flag(user_id, "active_intent")
            self.reset_troubleshoot_state(user_id, intent)
            
            return {"bubbles": [{"text": resolve_msg}], "next": "end", "status": "resolved"}
        
        if action == "pending":
            if step_def:
                pending_list = step_def.get("pending_templates") or meta.get("general_templates", {}).get("closing_pending", [])
            else:
                pending_list = meta.get("general_templates", {}).get("closing_pending", [])
            
            pending_template = random.choice(pending_list) if pending_list else "Baik kak, saya bantu teruskan ke teknisi ya."
            pending_msg = self._naturalize_template(user_id, pending_template, "pending")
            
            self.memstore.set_flag(user_id, "sop_pending", True)
            self.memstore.append_history(user_id, "bot", pending_msg)
            
            name_question = self.data_collector.generate_question(user_id, "name")
            combined_response = f"{pending_msg} {name_question}"
            self.memstore.append_history(user_id, "bot", name_question)
            
            return {"bubbles": [{"text": pending_msg}, {"text": name_question}], "next": "await_reply", "status": "open"}
        
        if action == "next":
            if not next_step_id:
                fallback = "Baik kak, izinkan saya cek lebih lanjut ya."
                self.memstore.append_history(user_id, "bot", fallback)
                return {"bubbles": [{"text": fallback}], "next": "await_reply"}
            
            if active_step_id and user_answer != "unclear":
                self.update_troubleshoot_flags(user_id, intent, active_step_id, user_answer)
            
            self.memstore.set_flag(user_id, f"asked_{next_step_id}", False)
            
            next_step = next((s for s in sop[intent]["steps"] if s["id"] == next_step_id), None)
            if not next_step:
                fallback = "Baik kak, izinkan saya cek lebih lanjut ya."
                self.memstore.append_history(user_id, "bot", fallback)
                return {"bubbles": [{"text": fallback}], "next": "await_reply"}
            
            ask_list = next_step.get("ask_templates") or next_step.get("ask") or ["Boleh kami cek kondisi alatnya kak?"]
            next_ask = random.choice(ask_list)
            
            reply = self._naturalize_template(user_id, next_ask, "next")
            
            self.memstore.append_history(user_id, "bot", reply)
            
            return {"bubbles": [{"text": reply}], "next": "await_reply"}
        
        fallback = "Baik kak, izinkan saya cek lebih lanjut ya."
        self.memstore.append_history(user_id, "bot", fallback)
        return {"bubbles": [{"text": fallback}], "next": "await_reply"}

    def handle_exploration(self, user_id: str, message: str, sop: dict, intent: str, is_new_complaint: bool = False, additional_complaint: str = "none"):
        current_active_intent = self.memstore.get_flag(user_id, "active_intent")
        sop_pending = self.memstore.get_flag(user_id, "sop_pending")
        sop_resolved = self.memstore.get_flag(user_id, "sop_resolved")
        
        active_step_id = self.memstore.get_flag(user_id, f"{current_active_intent}_active_step") if current_active_intent else None
        waiting_confirm = self.memstore.get_flag(user_id, f"{active_step_id}_waiting_confirm") if active_step_id else False
        
        if waiting_confirm:
            is_new_complaint = False
        
        short_log(self.logger, user_id, "lock_intent_check", 
                 f"additional={additional_complaint}, curr_active={current_active_intent}, match={current_active_intent != additional_complaint}")
        
        if additional_complaint and additional_complaint != "none" and current_active_intent and current_active_intent != additional_complaint:
            short_log(self.logger, user_id, "lock_intent_triggered", 
                     f"Active: {current_active_intent}, Additional: {additional_complaint}, Queued")
            
            self._queue_additional_complaint(user_id, additional_complaint)
            
            sop_state = self._build_sop_state(user_id, current_active_intent, sop)
            step_def = sop_state.get("step_def")
            
            if step_def:
                ask_list = step_def.get("ask_templates", [])
                troubleshoot_question = random.choice(ask_list) if ask_list else "Boleh kita lanjutkan troubleshooting nya?"
            else:
                troubleshoot_question = "Boleh kita lanjutkan troubleshooting nya?"
            
            acknowledge_response = self._generate_acknowledge_and_redirect(
                user_id=user_id,
                additional_complaint=additional_complaint,
                active_intent=current_active_intent,
                troubleshoot_question=troubleshoot_question
            )
            
            self.memstore.append_history(user_id, "bot", acknowledge_response)
            return {"bubbles": [{"text": acknowledge_response}], "next": "await_reply", "status": "in_progress"}
        
        intent_changed = self._track_intent_change(user_id, intent)
        
        is_new_issue = (
            intent_changed or 
            sop_pending or 
            sop_resolved or 
            (current_active_intent is None and intent) or
            is_new_complaint
        )
        
        if is_new_issue:
            clarify_count_backup = self.memstore.get_flag(user_id, f"{intent}_clarify_count") or 0
            
            if current_active_intent and current_active_intent != intent:
                self.reset_troubleshoot_state(user_id, current_active_intent)
            
            self.reset_troubleshoot_state(user_id, intent)
            
            if current_active_intent == intent:
                self.memstore.set_flag(user_id, f"{intent}_clarify_count", clarify_count_backup)
            
            self.memstore.clear_flag(user_id, "sop_pending")
            self.memstore.clear_flag(user_id, "sop_resolved")
            self.memstore.clear_flag(user_id, "active_intent")
        
        self.memstore.set_flag(user_id, "active_intent", intent)
        
        active_step_id = self.memstore.get_flag(user_id, f"{intent}_active_step")
        if not active_step_id and intent in sop:
            steps = sop[intent].get("steps", [])
            if steps:
                first_step_id = steps[0].get("id")
                self.memstore.set_flag(user_id, f"{intent}_active_step", first_step_id)
        
        sop_state = self._build_sop_state(user_id, intent, sop)
        step_def = sop_state.get("step_def")
        active_step = sop_state.get("active_step")
        waiting_confirm = sop_state.get("waiting_confirm", False)
        confirm_data = sop_state.get("confirm_data")
        
        if current_active_intent and self._is_explicit_resolution(message) and not sop_pending:
            resolve_list = step_def.get("resolve_templates", []) if step_def else []
            if not resolve_list:
                resolve_list = sop.get("metadata", {}).get("general_templates", {}).get("closing_resolved", [])
            resolve_template = random.choice(resolve_list) if resolve_list else "Baik kak, saya tutup laporannya ya."
            resolve_msg = self._naturalize_template(user_id, resolve_template, "resolve")
            
            self.memstore.set_flag(user_id, "sop_resolved", True)
            self.memstore.clear_flag(user_id, "active_intent")
            self.memstore.append_history(user_id, "bot", resolve_msg)
            self.reset_troubleshoot_state(user_id, intent)
            
            return {"bubbles": [{"text": resolve_msg}], "next": "end", "status": "resolved"}
        
        
        step_already_asked = False
        if active_step and step_def:
            step_id = active_step.get("step_id", "")
            
            history = self.memstore.get_history(user_id)
            if len(history) >= 2:
                last_msg = history[-1]
                second_last = history[-2]
                
                if last_msg.get("role") == "user" and second_last.get("role") == "bot":
                    step_already_asked = True
        
        user_answer = 'unclear'
        if step_already_asked and step_def:
            expected_result = step_def.get("expected_result", [])
            user_answer = self._parse_user_answer(message, expected_result)
        
        if waiting_confirm and confirm_data:
            user_answer_confirm = self._parse_user_answer(message, ['yes', 'no'])
            
            if user_answer_confirm == 'yes':
                if confirm_data.get("resolve_if_yes"):
                    resolve_list = step_def.get("resolve_templates", [])
                    resolve_template = random.choice(resolve_list) if resolve_list else "Baik kak, saya tutup laporannya ya."
                    resolve_msg = self._naturalize_template(user_id, resolve_template, "resolve")
                    
                    self.memstore.set_flag(user_id, "sop_resolved", True)
                    self.memstore.clear_flag(user_id, "active_intent")
                    self.memstore.append_history(user_id, "bot", resolve_msg)
                    
                    return {"bubbles": [{"text": resolve_msg}], "next": "end", "status": "resolved"}
            
            elif user_answer_confirm == 'no':
                if confirm_data.get("next_if_no"):
                    next_step_id = confirm_data["next_if_no"]
                    self.memstore.set_flag(user_id, f"{active_step['step_id']}_waiting_confirm", False)
                    
                    completed = sop_state["completed_steps"]
                    if active_step["step_id"] not in completed:
                        completed.append(active_step["step_id"])
                        self.memstore.set_flag(user_id, f"{intent}_completed_steps", completed)
                    
                    self.memstore.set_flag(user_id, f"{intent}_active_step", next_step_id)
                    
                    next_step = next((s for s in sop[intent]["steps"] if s["id"] == next_step_id), None)
                    if next_step:
                        ask_list = next_step.get("ask_templates", [])
                        ask_template = random.choice(ask_list) if ask_list else "Boleh kami cek kondisi alatnya kak?"
                        ask_msg = self._naturalize_template(user_id, ask_template, "ask")
                        self.memstore.append_history(user_id, "bot", ask_msg)
                        return {"bubbles": [{"text": ask_msg}], "next": "await_reply"}
                
                elif confirm_data.get("pending_if_no"):
                    pending_list = step_def.get("pending_templates", [])
                    pending_template = random.choice(pending_list) if pending_list else "Baik kak, saya teruskan ke teknisi ya."
                    pending_msg = self._naturalize_template(user_id, pending_template, "pending")
                    
                    self.memstore.set_flag(user_id, "sop_pending", True)
                    self.memstore.set_flag(user_id, "pending_just_triggered", True)
                    self.memstore.append_history(user_id, "bot", pending_msg)
                    
                    return {"bubbles": [{"text": pending_msg}], "next": "await_reply", "status": "open"}
        
        if not step_def:
            fallback = self._generate_natural_fallback(user_id, message, "no_step_def")
            self.memstore.append_history(user_id, "bot", fallback)
            return {"bubbles": [{"text": fallback}], "next": "await_reply"}
        
        if not step_already_asked:
            ask_list = step_def.get("ask_templates", [])
            ask_template = random.choice(ask_list) if ask_list else "Boleh kami cek kondisi alatnya kak?"
            ask_msg = self._naturalize_template(user_id, ask_template, "ask")
            self.memstore.append_history(user_id, "bot", ask_msg)
            return {"bubbles": [{"text": ask_msg}], "next": "await_reply"}
        
        if self._is_simple_acknowledge(message) and user_answer == 'yes':
            acknowledge_responses = [
                f"Baik kak, silakan dicoba dulu ya. Kabari kami hasilnya.",
                f"Oke kak, ditunggu kabarnya setelah dicoba ya.",
                f"Siap kak, mohon kabari kalau sudah dicoba ya."
            ]
            ack_msg = random.choice(acknowledge_responses)
            self.memstore.append_history(user_id, "bot", ack_msg)
            return {"bubbles": [{"text": ack_msg}], "next": "await_reply"}
        
        if user_answer == 'unclear':
            clarify_count = self.memstore.get_flag(user_id, f"{intent}_clarify_count") or 0
            clarify_count += 1
            self.memstore.set_flag(user_id, f"{intent}_clarify_count", clarify_count)
            
            short_log(self.logger, user_id, "clarify_count_exploration", f"Intent: {intent}, Count: {clarify_count}/3")
            
            if clarify_count >= 3:
                self.memstore.set_flag(user_id, f"{intent}_clarify_count", 0)
                
                escalate_msg = "Baik kak, sepertinya perlu pengecekan lebih detail oleh teknisi kami. Boleh saya bantu jadwalkan kunjungan teknisi?"
                self.memstore.append_history(user_id, "bot", escalate_msg)
                
                self.memstore.set_flag(user_id, "sop_pending", True)
                self.memstore.set_flag(user_id, "pending_just_triggered", True)
                
                short_log(self.logger, user_id, "clarify_escalated_exploration", f"Auto-escalate after {clarify_count} unclear answers")
                
                return {"bubbles": [{"text": escalate_msg}], "next": "await_reply", "status": "open"}
            
            clarify_list = sop_state["metadata"].get("general_templates", {}).get("clarify", [])
            clarify_msg = random.choice(clarify_list) if clarify_list else "Boleh dijelaskan sedikit lagi kak?"
            self.memstore.append_history(user_id, "bot", clarify_msg)
            return {"bubbles": [{"text": clarify_msg}], "next": "await_reply"}
        
        self.memstore.set_flag(user_id, f"{intent}_clarify_count", 0)
        
        logic_key = f"on_answer_{user_answer}"
        logic = step_def.get("logic", {}).get(logic_key, {})
        
        if not logic:
            fallback = self._generate_natural_fallback(user_id, message, "no_logic")
            self.memstore.append_history(user_id, "bot", fallback)
            return {"bubbles": [{"text": fallback}], "next": "await_reply"}
        
        self.memstore.set_flag(user_id, f"{active_step['step_id']}_answer", user_answer)
        
        if logic.get("instruct"):
            instruct_list = step_def.get("instruct_templates", [])
            instruct_template = random.choice(instruct_list) if instruct_list else "Silakan ikuti instruksi berikut."
            instruct_msg = self._naturalize_template(user_id, instruct_template, "instruct")
            self.memstore.append_history(user_id, "bot", instruct_msg)
            
            if logic.get("confirm"):
                self.memstore.set_flag(user_id, f"{active_step['step_id']}_waiting_confirm", True)
                self.memstore.set_flag(user_id, f"{active_step['step_id']}_confirm_data", logic)
            
            return {"bubbles": [{"text": instruct_msg}], "next": "await_reply"}
        
        if logic.get("confirm"):
            confirm_list = step_def.get("confirm_templates", [])
            confirm_template = random.choice(confirm_list) if confirm_list else "Apakah sudah berfungsi kak?"
            confirm_msg = self._naturalize_template(user_id, confirm_template, "confirm")
            self.memstore.append_history(user_id, "bot", confirm_msg)
            
            self.memstore.set_flag(user_id, f"{active_step['step_id']}_waiting_confirm", True)
            self.memstore.set_flag(user_id, f"{active_step['step_id']}_confirm_data", logic)
            
            return {"bubbles": [{"text": confirm_msg}], "next": "await_reply"}
        
        if logic.get("resolve"):
            if not self._is_explicit_resolution(message):
                short_log(self.logger, user_id, "prevent_premature_resolve_logic", 
                         f"SOP logic want resolve but no explicit confirmation")
                
                confirm_msg = "Apakah alatnya sudah berfungsi normal kak?"
                self.memstore.append_history(user_id, "bot", confirm_msg)
                
                self.memstore.set_flag(user_id, f"{active_step['step_id']}_waiting_confirm", True)
                self.memstore.set_flag(user_id, f"{active_step['step_id']}_confirm_data", {
                    "resolve_if_yes": True,
                    "next_if_no": None,
                    "pending_if_no": True
                })
                
                return {"bubbles": [{"text": confirm_msg}], "next": "await_reply"}
            
            resolve_list = step_def.get("resolve_templates", [])
            resolve_template = random.choice(resolve_list) if resolve_list else "Baik kak, saya tutup laporannya ya."
            resolve_msg = self._naturalize_template(user_id, resolve_template, "resolve")
            
            self.memstore.set_flag(user_id, "sop_resolved", True)
            self.memstore.clear_flag(user_id, "active_intent")
            self.memstore.append_history(user_id, "bot", resolve_msg)
            
            return {"bubbles": [{"text": resolve_msg}], "next": "end", "status": "resolved"}
        
        if logic.get("pending"):
            pending_list = step_def.get("pending_templates", [])
            pending_template = random.choice(pending_list) if pending_list else "Baik kak, saya teruskan ke teknisi ya."
            pending_msg = self._naturalize_template(user_id, pending_template, "pending")
            
            self.memstore.set_flag(user_id, "sop_pending", True)
            self.memstore.set_flag(user_id, "pending_just_triggered", True)
            self.memstore.append_history(user_id, "bot", pending_msg)
            
            return {"bubbles": [{"text": pending_msg}], "next": "await_reply", "status": "open"}
        
        if logic.get("next"):
            next_step_id = logic["next"]
            
            completed = sop_state["completed_steps"]
            if active_step["step_id"] not in completed:
                completed.append(active_step["step_id"])
                self.memstore.set_flag(user_id, f"{intent}_completed_steps", completed)
            
            self.memstore.set_flag(user_id, f"{intent}_active_step", next_step_id)
            
            next_step = next((s for s in sop[intent]["steps"] if s["id"] == next_step_id), None)
            if next_step:
                ask_list = next_step.get("ask_templates", [])
                ask_template = random.choice(ask_list) if ask_list else "Boleh kami cek kondisi alatnya kak?"
                ask_msg = self._naturalize_template(user_id, ask_template, "ask")
                self.memstore.append_history(user_id, "bot", ask_msg)
                return {"bubbles": [{"text": ask_msg}], "next": "await_reply"}
        
        fallback = self._generate_natural_fallback(user_id, message, "general")
        self.memstore.append_history(user_id, "bot", fallback)
        return {"bubbles": [{"text": fallback}], "next": "await_reply"}
    
    def _log_and_return(self, user_id: str, response_dict: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        bubbles = response_dict.get("bubbles", [])
        response_text = " | ".join([b.get("text", "") for b in bubbles if b.get("text")])
        status = response_dict.get("status", "unknown")
        next_action = response_dict.get("next", "unknown")
        
        active_intent = self.memstore.get_flag(user_id, "active_intent")
        sop_pending = self.memstore.get_flag(user_id, "sop_pending")
        identity = self.memstore.get_identity(user_id)
        collection_state = self.data_collector.get_collection_state(user_id)
        
        log_metadata = {
            "status": status,
            "next_action": next_action,
            "active_intent": active_intent,
            "sop_pending": sop_pending,
            "bubble_count": len(bubbles),
            "user_name": identity.get("name"),
            "user_product": identity.get("product"),
            "user_address": identity.get("address"),
            "data_collection_complete": collection_state.get("is_complete", False),
            "next_field_needed": collection_state.get("next_field"),
        }
        
        if metadata:
            log_metadata.update(metadata)
        
        self.chat_logger.log_outgoing(
            user_id=user_id,
            response=response_text,
            status=status,
            metadata=log_metadata
        )
        
        return response_dict

    def handle(self, user_id: str, message: str, gateway_only: bool = False) -> Dict[str, Any]:
        self.gateway_only = gateway_only
        msg = (message or "").strip()
        
        sop_pending_flag = self.memstore.get_flag(user_id, "sop_pending")
        active_intent = self.memstore.get_flag(user_id, "active_intent")
        
        if not msg:
            if sop_pending_flag:
                state = self.data_collector.get_collection_state(user_id)
                next_field = state.get("next_field")
                
                if next_field:
                    identity = self.memstore.get_identity(user_id)
                    gender = identity.get("gender")
                    salutation = "Pak" if gender == "male" else "Bu" if gender == "female" else "Kak"
                    
                    field_map = {"name": "nama", "product": "produk", "address": "alamat"}
                    field_name = field_map.get(next_field, "data")
                    
                    fallback = f"Maaf {salutation}, boleh diisi {field_name}nya ya?"
                    return self._log_and_return(user_id, {
                        "bubbles": [{"text": fallback}], 
                        "next": "await_reply",
                        "status": "open"
                    }, {"context": "empty_message_with_pending"})
            
            return self._log_and_return(user_id, {
                "bubbles": [{"text": "Maaf kak, silakan jelaskan keluhannya ya."}], 
                "next": "await_reply"
            }, {"context": "empty_message"})

        self.memstore.append_history(user_id, "user", msg)
        
        identity = self.memstore.get_identity(user_id)
        self.chat_logger.log_incoming(
            user_id=user_id,
            message=msg,
            metadata={
                "gateway_only": gateway_only,
                "sop_pending": sop_pending_flag,
                "active_intent": active_intent,
                "user_name": identity.get("name"),
                "user_product": identity.get("product"),
                "has_address": bool(identity.get("address"))
            }
        )
        
        spam_check = self._check_spam_or_profanity(user_id, msg)
        if spam_check["is_spam"] or spam_check["is_profanity"]:
            spam_type = "profanity" if spam_check["is_profanity"] else "spam"
            short_log(self.logger, user_id, f"{spam_type}_detected", f"Msg: {msg[:30]}")
            
            if spam_check["is_profanity"]:
                return self._log_and_return(user_id, {
                    "bubbles": [{"text": "🙏"}], 
                    "next": "await_reply"
                }, {"context": "profanity_filtered"})
            
            spam_count = self.memstore.get_flag(user_id, "spam_count") or 0
            spam_count += 1
            self.memstore.set_flag(user_id, "spam_count", spam_count)
            
            if spam_count >= 3:
                self.memstore.set_flag(user_id, "spam_count", 0)
                return self._log_and_return(user_id, {
                    "bubbles": [{"text": "Kak, kalau ada keluhan EAC bisa langsung ceritakan ya 😊"}], 
                    "next": "await_reply"
                }, {"context": "spam_threshold_reached"})
            
            return self._log_and_return(user_id, {
                "bubbles": [{"text": "🙏"}], 
                "next": "await_reply"
            }, {"context": "spam_filtered"})
        
        self.memstore.set_flag(user_id, "spam_count", 0)
        
        sop_resolved_flag = self.memstore.get_flag(user_id, "sop_resolved")
        if sop_resolved_flag:
            short_log(self.logger, user_id, "after_resolved_msg", f"Msg: {msg[:50]}")
            
            simple_ack = self._is_simple_acknowledge(msg)
            
            if simple_ack:
                ack_responses = [
                    "Siap kak 👍",
                    "Baik kak, senang bisa membantu 😊",
                    "Sama-sama kak, jangan ragu hubungi kami lagi ya 🙏",
                ]
                ack_msg = random.choice(ack_responses)
                self.memstore.append_history(user_id, "bot", ack_msg)
                return self._log_and_return(user_id, {
                    "bubbles": [{"text": ack_msg}], 
                    "next": "end",
                    "status": "resolved"
                }, {"context": "after_resolved_simple_ack"})
            
            self.memstore.clear_flag(user_id, "sop_resolved")
            short_log(self.logger, user_id, "sop_resolved_cleared", "User mengirim pesan baru setelah resolved, clear flag")

        sop = self.load_sop_from_file()
        sop_intents = [k for k in sop.keys() if k != "rules" and k != "metadata"]

        active_intent = self.memstore.get_flag(user_id, "active_intent")
        sop_pending_for_check = self.memstore.get_flag(user_id, "sop_pending")
        
        if active_intent and not sop_pending_for_check:
            data_detected = self._detect_and_store_identity(user_id, msg)
            if data_detected:
                short_log(self.logger, user_id, "data_collected_mid_flow", 
                         f"Type: {data_detected['type']}, Value: {data_detected['value']}")

        unified = self.detect_intent_via_llm(user_id, msg, sop_intents)

        category      = unified["category"]
        has_greeting  = unified["has_greeting"]
        greeting_part = unified["greeting_part"]
        issue_part    = unified["issue_part"]
        sop_intent    = unified["intent"]
        is_new_complaint = unified.get("is_new_complaint", False)
        additional_complaint = unified.get("additional_complaint", "none")
        
        rapid_switch_detected = False
        if active_intent and active_intent != "none":
            python_additional = self._detect_additional_complaint_python(msg, active_intent)
            
            if sop_intent != active_intent and sop_intent != "none":
                switch_keywords = [
                    "eh bukan", "tunggu", "maksud saya", "maksudku", "maaf", "sebenernya",
                    "actually", "sebenarnya", "salah", "bukan itu"
                ]
                if any(kw in msg.lower() for kw in switch_keywords):
                    rapid_switch_detected = True
                    short_log(self.logger, user_id, "rapid_intent_switch", 
                             f"Switching from '{active_intent}' to '{sop_intent}'")
                    
                    self.reset_troubleshoot_state(user_id, active_intent)
                    
                    python_additional = "none"
                    additional_complaint = "none"
            
            if python_additional != "none" and not rapid_switch_detected:
                additional_complaint = python_additional
                if sop_intent != active_intent:
                    sop_intent = active_intent
                    is_new_complaint = False
            
            sop_state = self._build_sop_state(user_id, active_intent, sop)
            active_step = sop_state.get("active_step")
            step_def = sop_state.get("step_def")
            
            is_answering_troubleshoot = False
            if active_step and step_def:
                # Check if bot just asked a question
                history = self.memstore.get_history(user_id)
                if len(history) >= 2:
                    last_msg = history[-1]
                    second_last = history[-2]
                    if last_msg.get("role") == "user" and second_last.get("role") == "bot":
                        # Bot just asked, user just answered - this is troubleshooting answer
                        is_answering_troubleshoot = True
            
            # Only check distraction if NOT answering troubleshooting
            if not is_answering_troubleshoot:
                distraction_type = self._classify_distraction_type(msg)
                
                if distraction_type in ("competitor", "question", "chitchat") and sop_intent == active_intent and not rapid_switch_detected:
                    if active_step and step_def:
                        ask_list = step_def.get("ask_templates", [])
                        troubleshoot_question = random.choice(ask_list) if ask_list else "Boleh kita lanjutkan troubleshooting kak?"
                        
                        combined_response = self._generate_distraction_response(
                            user_id, msg, distraction_type, troubleshoot_question
                        )
                        
                        short_log(self.logger, user_id, f"{distraction_type}_handled_early", 
                                 f"Early distraction detection: {distraction_type}")
                        
                        self.memstore.append_history(user_id, "bot", combined_response)
                        return self._log_and_return(user_id, {"bubbles": [{"text": combined_response}], "next": "await_reply", "status": "in_progress"}, {"context": "early_distraction_handled", "distraction_type": distraction_type})
        
        
        if sop_pending_flag:
            collection_state = self.data_collector.get_collection_state(user_id)
            is_complete = collection_state.get("is_complete", False)
            
            if is_complete:
                pending_closing_sent = self.memstore.get_flag(user_id, "pending_closing_sent")
                
                if pending_closing_sent:
                    simple_ack = self._is_simple_acknowledge(msg)
                    
                    common_acks = [
                        'baik kak', 'baik ka', 'oke kak', 'ok kak', 'siap kak',
                        'terima kasih', 'makasih', 'thanks', 'thank you',
                        'sip kak', 'iya kak', 'ya kak'
                    ]
                    is_common_ack = any(ack in msg.lower() for ack in common_acks)
                    
                    if simple_ack or is_common_ack or len(msg) <= 3:
                        short_log(self.logger, user_id, "pending_complete_ack", 
                                 f"Simple ack after pending complete, minimal response")
                        
                        ack_responses = [
                            "🙏",
                            "Siap kak 👍",
                            "Terima kasih kak 😊"
                        ]
                        ack_msg = random.choice(ack_responses)
                        self.memstore.append_history(user_id, "bot", ack_msg)
                        return self._log_and_return(user_id, {
                            "bubbles": [{"text": ack_msg}],
                            "next": "end",
                            "status": "pending"
                        }, {"context": "pending_complete_simple_ack"})
                
                identity = self.memstore.get_identity(user_id)
                name = identity.get("name", "Kak")
                gender = identity.get("gender")
                is_company = identity.get("is_company", False)
                salutation = "Pak" if gender == "male" else "Bu" if gender == "female" else "Kak"
                
                if is_company:
                    greeting_name = name
                elif name and name != "Kak":
                    greeting_name = f"{salutation} {name}"
                else:
                    greeting_name = salutation
                
                closing_msg = f"Data {greeting_name} sudah kami terima. Teknisi kami akan segera menghubungi untuk konfirmasi jadwal kunjungan."
                
                self.memstore.append_history(user_id, "bot", closing_msg)
                self.memstore.set_flag(user_id, "pending_closing_sent", True)
                
                return self._log_and_return(user_id, {
                    "bubbles": [{"text": closing_msg}],
                    "next": "end",
                    "status": "pending"
                }, {"context": "pending_complete_reminder"})
            
            if sop_intent == active_intent or (sop_intent == "none" and not rapid_switch_detected) or (not is_new_complaint and not rapid_switch_detected):
                sop_intent = "none"

        if category in ("chitchat", "nonsense") and not has_greeting:
            if active_intent:
                sop_state = self._build_sop_state(user_id, active_intent, sop)
                active_step = sop_state.get("active_step")
                step_def = sop_state.get("step_def")
                
                if active_step and step_def:
                    distraction_type = self._classify_distraction_type(msg)
                    
                    ask_list = step_def.get("ask_templates", [])
                    troubleshoot_question = random.choice(ask_list) if ask_list else "Boleh kita lanjutkan troubleshooting kak?"
                    
                    if distraction_type == "competitor":
                        combined_response = self._generate_distraction_response(
                            user_id, msg, "competitor", troubleshoot_question
                        )
                        
                        short_log(self.logger, user_id, "competitor_mention_handled", 
                                 f"Competitor detected, redirected to active troubleshooting")
                    
                    elif distraction_type in ("question", "chitchat"):
                        combined_response = self._generate_distraction_response(
                            user_id, msg, distraction_type, troubleshoot_question
                        )
                        
                        short_log(self.logger, user_id, f"{distraction_type}_handled", 
                                 f"Distraction type: {distraction_type}, redirect to troubleshooting")
                    
                    else:
                        system_msg = "Kamu adalah CS Honeywell yang ramah. Jawab SANGAT SINGKAT dan natural."
                        chitchat_prompt = f"""
                        Customer bilang: "{msg}"
                        
                        Tugas:
                        1. Jawab dengan SANGAT SINGKAT (maksimal 1 kalimat pendek, 5-7 kata)
                        2. Natural dan friendly
                        3. Jangan bertele-tele
                        
                        Contoh bagus:
                        - "wah panas ya" → "Iya kak, memang lagi panas."
                        - "berapa lama garansinya?" → "Garansi 1 tahun kak."
                        - "mahal ga?" → "Untuk harga bisa hubungi sales kak."
                        - "kapan teknisi datang?" → "Nanti kami konfirmasi jadwalnya kak."
                        
                        Contoh BURUK (terlalu panjang):
                        - "Terima kasih atas pertanyaannya. Untuk informasi garansi..." (TERLALU PANJANG)
                        
                        Jawab HANYA response-nya (tanpa tanda kutip):
                        """
                        chitchat_response = self.ollama.generate(system=system_msg, prompt=chitchat_prompt).strip()
                        combined_response = f"{chitchat_response} Oh iya kak, balik ke EAC nya, {troubleshoot_question.lower()}"
                        
                        short_log(self.logger, user_id, "chitchat_handled", 
                                 f"Chitchat detected, redirected to active troubleshooting")
                    
                    self.memstore.append_history(user_id, "bot", combined_response)
                    return self._log_and_return(user_id, {"bubbles": [{"text": combined_response}], "next": "await_reply", "status": "in_progress"}, {"context": "chitchat_distraction_handled"})
            
            # Fallback if no active intent or step_def
            return self._log_and_return(user_id, {
                "bubbles": [{
                    "text": self._generate_natural_fallback(user_id, msg, "chitchat_no_intent")
                }],
                "next": "await_reply"
            }, {"context": "chitchat_no_active_intent"})

        if has_greeting and issue_part.strip() == "":
            reply = self.handle_greeting(user_id, greeting_part, {"should_reply_greeting": True})
            return self._log_and_return(user_id, {"bubbles": [{"text": reply}], "next": "await_reply"}, {"context": "greeting_only"})

        greeting_reply = None
        if has_greeting:
            today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            last_greeted = self.memstore.get_flag(user_id, "last_greeted_date")
            if last_greeted != today:
                greeting_reply = self.handle_greeting(user_id, greeting_part, {"should_reply_greeting": True})
                if greeting_reply:
                    self.memstore.append_history(user_id, "bot", greeting_reply)
            if gateway_only and greeting_reply:
                return self._log_and_return(user_id, {"bubbles": [{"text": greeting_reply}], "next": "await_reply"}, {"context": "gateway_greeting"})

        msg_issue = issue_part.strip()
        sop_pending_flag = self.memstore.get_flag(user_id, "sop_pending")
        
        if sop_pending_flag:
            pending_just_triggered = self.memstore.get_flag(user_id, "pending_just_triggered")
            
            if pending_just_triggered:
                self.memstore.clear_flag(user_id, "pending_just_triggered")
                
                name_question = self.data_collector.generate_question(user_id, "name")
                self.memstore.append_history(user_id, "bot", name_question)
                
                return self._log_and_return(user_id, {"bubbles": [{"text": name_question}], "next": "await_reply", "status": "open"}, {"context": "pending_just_triggered"})
            
            if active_intent and active_intent != "none":
                python_additional = self._detect_additional_complaint_python(msg, active_intent)
                if python_additional != "none":
                    self._queue_additional_complaint(user_id, python_additional)
                    short_log(self.logger, user_id, "additional_complaint_queued_pending", 
                             f"Queued '{python_additional}' during pending/data collection")
            
            if sop_intent != active_intent and sop_intent != "none" and is_new_complaint:
                dc_result = self.data_collector.process_message(user_id, msg)
                
                if dc_result["action"] == "off_topic":
                    identity = self.memstore.get_identity(user_id)
                    gender = identity.get("gender")
                    salutation = "Pak" if gender == "male" else "Bu" if gender == "female" else "Kak"
                    
                    off_topic_info = dc_result.get("off_topic_info", {})
                    missing_field = off_topic_info.get("missing_field", "name")
                    field_map = {"name": "nama", "product": "produk", "address": "alamat"}
                    field_name = field_map.get(missing_field, "data")
                    msg = f"Baik {salutation}, keluhan sudah saya catat dan akan kami proses setelah data lengkap. Boleh kita lanjutkan pengisian {field_name}nya dulu?"
                    
                    self.memstore.append_history(user_id, "bot", msg)
                    return self._log_and_return(user_id, {"bubbles": [{"text": msg}], "next": "await_reply", "status": "open"}, {"context": "data_collection_off_topic_new_complaint"})
                else:
                    response = dc_result.get("response")
                    is_complete = dc_result.get("is_complete", False)
                    
                    if response:
                        self.memstore.append_history(user_id, "bot", response)
                        return self._log_and_return(user_id, {
                            "bubbles": [{"text": response}], 
                            "next": "end" if is_complete else "await_reply",
                            "status": "pending" if is_complete else "open"
                        }, {"context": "data_collection_with_new_complaint", "is_complete": is_complete})
            else:
                dc_result = self.data_collector.process_message(user_id, msg)
                
                if dc_result["action"] == "off_topic":
                    off_topic_info = dc_result.get("off_topic_info", {})
                    message_type = off_topic_info.get("message_type", "question")
                    missing_field = off_topic_info.get("missing_field", "name")
                    
                    identity = self.memstore.get_identity(user_id)
                    gender = identity.get("gender")
                    salutation = "Pak" if gender == "male" else "Bu" if gender == "female" else "Kak"
                    
                    field_map = {"name": "nama", "product": "produk", "address": "alamat"}
                    field_name = field_map.get(missing_field, "data")
                    
                    if message_type == "complaint":
                        msg = f"Baik {salutation}, keluhan sudah saya catat dan akan kami proses setelah data lengkap. Boleh kita lanjutkan pengisian {field_name}nya dulu?"
                    elif message_type == "question":
                        msg = f"Baik {salutation}, pertanyaan akan saya jawab setelah data lengkap. Boleh kita selesaikan pengisian {field_name}nya dulu?"
                    else:
                        msg = f"Baik {salutation}, boleh kita lanjutkan pengisian {field_name}nya dulu?"
                    
                    self.memstore.append_history(user_id, "bot", msg)
                    return self._log_and_return(user_id, {"bubbles": [{"text": msg}], "next": "await_reply", "status": "open"}, {"context": "data_collection_off_topic", "message_type": message_type})
                
                response = dc_result.get("response")
                is_complete = dc_result.get("is_complete", False)
                
                if response:
                    self.memstore.append_history(user_id, "bot", response)
                    return self._log_and_return(user_id, {
                        "bubbles": [{"text": response}], 
                        "next": "end" if is_complete else "await_reply",
                        "status": "pending" if is_complete else "open"
                    }, {"context": "data_collection_normal", "is_complete": is_complete})

        if sop_intent != "none":
            message_to_use = msg_issue if msg_issue else msg
            
            result = self.handle_exploration(
                user_id=user_id,
                message=message_to_use,  
                sop=sop,
                intent=sop_intent,
                is_new_complaint=is_new_complaint,
                additional_complaint=additional_complaint
            )
            
            return self._log_and_return(user_id, result, {"context": "handle_exploration", "intent": sop_intent})
        
        fallback = self._generate_natural_fallback(user_id, msg, "no_intent")
        self.memstore.append_history(user_id, "bot", fallback)
        return self._log_and_return(user_id, {"bubbles": [{"text": fallback}], "next": "await_reply"}, {"context": "no_intent_detected"})

    def _detect_and_store_identity(self, user_id: str, message: str) -> Optional[Dict[str, str]]:
        prompt = f"""
        Analisis pesan berikut dan deteksi apakah ada informasi identitas:
        "{message}"
        
        Informasi yang dicari:
        - nama (misal: "Nama saya Budi", "Saya Budi")
        - alamat (misal: "Alamat saya di Jakarta", "Saya di Bandung")
        - produk (misal: "Produk EAC", "Alat EAC")
        - serial (misal: "Nomor serial f57a", "Serial: ABC123")
        
        Jawab HANYA JSON:
        {{
          "has_identity": true/false,
          "type": "nama/alamat/produk/serial/none",
          "value": "<isi yang terdeteksi atau kosong>"
        }}
        """
        
        system_msg = "Detektor identitas pelanggan. Jawab HANYA JSON valid."
        out = self.ollama.generate_json(system=system_msg, prompt=prompt) or {}
        
        if not out.get("has_identity"):
            return None
        
        dtype = out.get("type", "none")
        value = (out.get("value") or "").strip()
        
        if not value or dtype == "none":
            return None
        
        if dtype == "nama":
            self.memstore.set_name(user_id, value)
        elif dtype == "alamat":
            self.memstore.update(user_id, {"address": value})
        elif dtype == "produk":
            self.memstore.set_product(user_id, value)
        elif dtype == "serial":
            self.memstore.update(user_id, {"serial": value})
        
        return {"type": dtype, "value": value}


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="ConversationEngine CLI")
    parser.add_argument(
        "--log-view",
        nargs="*",
        help="Filter kategori log (exploration, rag, intent, data)",
    )
    args = parser.parse_args()

    engine = ConversationEngine()
    user = input("Masukkan User ID (default: demo-user): ").strip() or "demo-user"

    while True:
        msg = input("\nYou: ").strip()
        if msg.lower() in {"exit", "quit"}:
            break
        result = engine.handle(user, msg)
        for b in result.get("bubbles", []):
            print("Bot:", b["text"])
