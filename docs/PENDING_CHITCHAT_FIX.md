# Pending State Chitchat Handling Fix

## Masalah

Sebelumnya, ketika user dalam state `sop_pending` (sudah dijadwalkan teknisi) dan mengirim chitchat seperti:

- "Iya, cukup mengganggu"
- "Waktu dinyalakan suka ada bunyi kretek kretek gitu"
- "Bunyi kretek kretek"

Sistem masih merespons dengan meminta data collection berulang kali:

- "Baik Kak, boleh kita lanjutkan pengisian namanya dulu?"
- "Maaf Kak, boleh diulang namanya?"

Ini membuat user bingung dan pengalaman tidak natural.

## Solusi

Menambahkan deteksi chitchat saat pending state. Jika user mengirim chitchat (bukan complaint baru atau data), sistem hanya acknowledge saja tanpa meminta data collection lagi.

## Perubahan Kode

File: `src/convo/engine.py`
Lokasi: Line 2483-2520 (pending state data collection section)

Sebelumnya:

```python
if dc_result["action"] == "off_topic":
    off_topic_info = dc_result.get("off_topic_info", {})
    message_type = off_topic_info.get("message_type", "question")

    # Langsung minta data lagi
    if message_type == "complaint":
        msg = f"Baik {salutation}, keluhan sudah saya catat..."
    elif message_type == "question":
        msg = f"Baik {salutation}, pertanyaan akan saya jawab..."
    else:
        msg = f"Baik {salutation}, boleh kita lanjutkan..."
```

Sesudahnya:

```python
if dc_result["action"] == "off_topic":
    off_topic_info = dc_result.get("off_topic_info", {})
    message_type = off_topic_info.get("message_type", "question")

    # Jika chitchat, hanya acknowledge
    if message_type == "chitchat":
        acknowledge_responses = [
            f"Baik {salutation}.",
            f"Oke {salutation}.",
            f"Siap {salutation}."
        ]
        ack_msg = random.choice(acknowledge_responses)
        return {"bubbles": [{"text": ack_msg}], ...}

    # Jika complaint atau question, baru minta data
    if message_type == "complaint":
        msg = f"Baik {salutation}, keluhan sudah saya catat..."
    ...
```

## Flow Baru

1. User: "EAC bunyi terus kak, sering banget"
2. Bot: "Sepertinya perlu dibersihkan. Boleh jadwalkan teknisi?" (pending triggered)
3. Bot: "Baik Kak, boleh tahu pembeliannya atas nama siapa?"
4. User: "Iya, cukup mengganggu" (chitchat)
5. Bot: "Baik Kak." (acknowledge saja, tidak minta data lagi) ✅
6. User: "Budi" (kasih nama)
7. Bot: "Terima kasih Pak Budi, boleh tahu produknya?" (lanjut ke field berikutnya)

## Test

Run: `python tests/test_pending_chitchat.py`

Test memverifikasi:

- ✅ Bot tidak minta data berulang saat user chitchat di pending state
- ✅ Bot hanya acknowledge dengan response singkat
- ✅ Bot tetap lanjut data collection saat user kasih data yang diminta
