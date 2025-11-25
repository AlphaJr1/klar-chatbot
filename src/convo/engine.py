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

        LOGIC PRIORITAS:
        
        1. Jika active_intent SUDAH ADA (bukan "none"):
           a) Intent TETAP = active_intent (JANGAN ubah!)
           b) DETEKSI keluhan TAMBAHAN (additional_complaint):
              ⚠️ PENTING: Hanya deteksi jika pesan JELAS dan EKSPLISIT menyebut keluhan EAC baru.
              JANGAN deteksi jika substring kebetulan ada dalam kata lain (misal: "bunyi" dalam "terimakasih").
              
              - Jika JELAS menyebut masalah bau EAC → additional_complaint="bau"
                Contoh: "EAC juga bau", "bau menyengat dari EAC", "ada bau aneh"
              
              - Jika JELAS menyebut masalah bunyi EAC → additional_complaint="bunyi"
                Contoh: "EAC juga berisik", "mengeluarkan bunyi aneh", "suara berisik"
              
              - Jika JELAS menyebut masalah mati/tidak nyala → additional_complaint="mati"
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
        Balas greeting berikut dengan sopan dan profesional.
        Maksimal 1 kalimat.
        Hindari kata 'Anda'.
        Greeting pelanggan: "{greet_text}"
            Kamu asisten CS Honeywell.
            Mulai proses pengumpulan data dengan satu pertanyaan:
            minta nama pelanggan dengan sopan, maksimal 2 kalimat.
            Analisis pesan pelanggan berikut:
            "{message}"

            Tentukan apakah pesan ini mengandung informasi identitas (nama, alamat, produk, company, serial).
            Jawab hanya JSON:
            {{
              "type": "nama / alamat / produk / company / serial / none",
              "value": "<isi yang dideteksi>"
            }}
            Data pelanggan telah lengkap:
            - Nama: {name or '-'}
            - Alamat: {address or '-'}
            - Produk: {product or '-'}

            Tulis pesan penutup sopan 2–3 kalimat tanpa tanda tanya.
            Fokus: data sudah diterima, teknisi akan menghubungi kembali.
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