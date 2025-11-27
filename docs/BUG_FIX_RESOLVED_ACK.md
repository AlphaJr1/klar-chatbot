# Bug Fix: Chat Aneh Setelah Tiket Ditutup

## Masalah

Ketika tiket sudah ditutup (resolved) dan customer mengirim pesan simple acknowledgement seperti "baik", bot malah menanyakan keluhan baru:

```
Customer: "baik"
Bot: "Maaf kak, boleh ceritakan keluhan alatnya secara singkat?"
```

## Root Cause

Di fungsi `handle()` pada line 2049-2113, ada logic untuk menangani `chitchat/nonsense` tapi **tidak mengecek flag `sop_resolved`** terlebih dahulu.

Flow yang terjadi:

1. Tiket ditutup → `sop_resolved=true`, `active_intent` di-clear
2. Customer bilang "baik" → terdeteksi sebagai "chitchat"
3. Karena `active_intent` sudah None, jatuh ke fallback line 2107-2113
4. Fallback menanyakan keluhan baru ❌

## Solusi

Menambahkan **early check** untuk `sop_resolved` di awal fungsi `handle()` (setelah line 1936).

Jika `sop_resolved=true` dan pesan adalah simple acknowledgement:

- Bot memberikan response natural seperti "Siap kak 👍"
- Status tetap "resolved"
- Tidak membuka troubleshooting baru

Jika `sop_resolved=true` tapi pesan bukan simple acknowledgement (keluhan baru):

- Clear flag `sop_resolved`
- Lanjutkan ke flow normal untuk handle keluhan baru

## Kode yang Ditambahkan

```python
# Line ~1937-1959 di src/convo/engine.py
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
```

## Testing

Test script: `tests/test_resolved_realistic.py`

Flow test:

1. ✅ Komplain → Bot tanya bunyi
2. ✅ Jawab "jarang" → Bot kasih instruksi
3. ✅ Konfirmasi "iya" → Bot tutup tiket (resolved)
4. ✅ Customer bilang "baik" → Bot reply "Siap kak 👍" (TIDAK nanya keluhan lagi!)

## Impact

- ✅ Bug fixed: Bot tidak lagi menanyakan keluhan setelah tiket ditutup
- ✅ User experience lebih natural
- ✅ Tidak ada side effect pada flow lainnya
