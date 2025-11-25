# Chat Logging Documentation

## Overview
Sistem logging chat mencatat **semua pesan masuk dan keluar** dengan detail lengkap untuk keperluan debugging dan monitoring.

## File Lokasi
- **Path**: `data/storage/logs/chat-YYYY-MM-DD.jsonl`
- **Format**: JSON Lines (satu JSON object per baris)
- **Rotation**: File baru dibuat setiap hari berdasarkan UTC timestamp

## Format Log

### 1. Incoming Message (Chat Masuk)
```json
{
  "ts": "2025-11-24T06:50:14.123456+00:00",
  "direction": "incoming",
  "user_id": "628123456789",
  "message": "AC saya mati",
  "message_length": 12,
  "metadata": {
    "gateway_only": false,
    "sop_pending": false,
    "active_intent": "none",
    "user_name": null,
    "user_product": null,
    "has_address": false
  }
}
```

**Field Explanation:**
- `ts`: Timestamp ISO8601 (UTC)
- `direction`: Selalu "incoming" untuk pesan masuk
- `user_id`: WhatsApp JID atau user identifier
- `message`: Teks pesan dari user
- `message_length`: Panjang karakter pesan
- `metadata`:
  - `gateway_only`: Apakah mode gateway only aktif
  - `sop_pending`: Status apakah sedang dalam pending state (menunggu teknisi)
  - `active_intent`: Intent aktif yang sedang diproses (mati/bau/bunyi/none)
  - `user_name`: Nama user jika sudah dikumpulkan
  - `user_product`: Produk user jika sudah dikumpulkan
  - `has_address`: Boolean apakah alamat sudah ada

### 2. Outgoing Message (Chat Keluar)
```json
{
  "ts": "2025-11-24T06:50:14.567890+00:00",
  "direction": "outgoing",
  "user_id": "628123456789",
  "response": "Baik kak, AC mati ya? Boleh dicek apakah lampu indikator menyala?",
  "response_length": 62,
  "status": "unknown",
  "metadata": {
    "status": "unknown",
    "next_action": "await_reply",
    "active_intent": "mati",
    "sop_pending": false,
    "bubble_count": 1,
    "user_name": null,
    "user_product": null,
    "user_address": null,
    "data_collection_complete": false,
    "next_field_needed": "name",
    "context": "handle_exploration"
  }
}
```

**Field Explanation:**
- `ts`: Timestamp ISO8601 (UTC)
- `direction`: Selalu "outgoing" untuk pesan keluar
- `user_id`: WhatsApp JID atau user identifier
- `response`: Teks response yang dikirim ke user (jika multi bubble, digabung dengan " | ")
- `response_length`: Panjang karakter response
- `status`: Status case saat ini (open/pending/resolved/unknown)
- `metadata`:
  - `status`: Status case
  - `next_action`: Aksi selanjutnya (await_reply/end)
  - `active_intent`: Intent yang sedang aktif
  - `sop_pending`: Apakah sedang pending untuk teknisi
  - `bubble_count`: Jumlah bubble yang dikirim
  - `user_name`: Nama user jika sudah dikumpulkan
  - `user_product`: Produk user
  - `user_address`: Alamat user
  - `data_collection_complete`: Boolean apakah data sudah lengkap
  - `next_field_needed`: Field yang masih dibutuhkan (name/product/address/null)
  - `context`: Konteks dari response (untuk debugging)

## Context Values

Context menunjukkan dari bagian mana response dihasilkan:

- `empty_message`: Pesan kosong dari user
- `empty_message_with_pending`: Pesan kosong saat pending state
- `early_distraction_handled`: Distraction handling sebelum data collection
- `chitchat_distraction_handled`: Chitchat handling saat troubleshooting aktif
- `chitchat_no_active_intent`: Chitchat tanpa intent aktif
- `greeting_only`: Hanya greeting tanpa issue
- `gateway_greeting`: Gateway mode dengan greeting
- `pending_just_triggered`: Baru saja trigger pending (akan mulai data collection)
- `data_collection_off_topic_new_complaint`: Off-topic saat data collection dengan complaint baru
- `data_collection_with_new_complaint`: Data collection dengan complaint baru
- `data_collection_off_topic`: Off-topic saat data collection
- `data_collection_normal`: Data collection flow normal
- `no_intent_detected`: Tidak ada intent yang terdeteksi
- `handle_exploration`: Dari handle_exploration (troubleshooting)

## Status Values

- `open`: Case masih terbuka, troubleshooting berlangsung
- `pending`: Case pending, menunggu teknisi (data collection selesai)
- `resolved`: Case sudah diselesaikan
- `in_progress`: Troubleshooting sedang berlangsung
- `unknown`: Status tidak diketahui (biasanya saat fallback)

## Contoh Real Flow

### 1. User Complaint Baru
```jsonl
{"ts":"2025-11-24T06:50:00Z","direction":"incoming","user_id":"628xxx","message":"AC saya mati","message_length":12,"metadata":{"sop_pending":false,"active_intent":"none"}}
{"ts":"2025-11-24T06:50:01Z","direction":"outgoing","user_id":"628xxx","response":"Baik kak, AC mati ya? Boleh dicek lampu indikatornya?","status":"unknown","metadata":{"active_intent":"mati","context":"handle_exploration"}}
```

### 2. Escalation ke Teknisi
```jsonl
{"ts":"2025-11-24T06:51:00Z","direction":"incoming","user_id":"628xxx","message":"tetap tidak menyala","message_length":20,"metadata":{"sop_pending":false,"active_intent":"mati"}}
{"ts":"2025-11-24T06:51:01Z","direction":"outgoing","user_id":"628xxx","response":"Baik kak, saya teruskan ke teknisi ya. | Baik Kak, boleh tahu pembeliannya atas nama siapa?","status":"open","metadata":{"sop_pending":true,"context":"pending_just_triggered"}}
```

### 3. Data Collection
```jsonl
{"ts":"2025-11-24T06:52:00Z","direction":"incoming","user_id":"628xxx","message":"Budi","message_length":4,"metadata":{"sop_pending":true,"active_intent":"mati","user_name":null}}
{"ts":"2025-11-24T06:52:01Z","direction":"outgoing","user_id":"628xxx","response":"Baik Pak, untuk produknya F57A atau F90A?","status":"open","metadata":{"sop_pending":true,"user_name":"Budi","data_collection_complete":false,"next_field_needed":"product","context":"data_collection_normal"}}
```

### 4. Data Complete
```jsonl
{"ts":"2025-11-24T06:53:00Z","direction":"incoming","user_id":"628xxx","message":"Jl. Sudirman 123, Jakarta Selatan","message_length":35,"metadata":{"sop_pending":true,"user_name":"Budi","user_product":"F57A"}}
{"ts":"2025-11-24T06:53:01Z","direction":"outgoing","user_id":"628xxx","response":"Terima kasih Pak Budi. Data sudah kami terima. Teknisi akan menghubungi.","status":"pending","metadata":{"sop_pending":true,"data_collection_complete":true,"next_field_needed":null,"context":"data_collection_normal"}}
```

## Cara Membaca Log

### Menggunakan jq (Command line)
```bash
# Lihat semua incoming messages hari ini
cat data/storage/logs/chat-2025-11-24.jsonl | jq 'select(.direction=="incoming")'

# Lihat semua outgoing dengan status pending
cat data/storage/logs/chat-2025-11-24.jsonl | jq 'select(.direction=="outgoing" and .status=="pending")'

# Lihat flow untuk user tertentu
cat data/storage/logs/chat-2025-11-24.jsonl | jq 'select(.user_id=="628xxx")'

# Hitung jumlah message per status
cat data/storage/logs/chat-2025-11-24.jsonl | jq -r '.metadata.status' | sort | uniq -c
```

### Menggunakan Python
```python
import json

with open('data/storage/logs/chat-2025-11-24.jsonl', 'r') as f:
    for line in f:
        log = json.loads(line)
        if log['direction'] == 'incoming':
            print(f"User {log['user_id']}: {log['message']}")
        else:
            print(f"Bot: {log['response']} (status: {log['status']})")
```

## Tips Debugging

1. **Cek Flow User**: Lihat semua log untuk satu user_id tertentu
2. **Monitor Status Transition**: Track perubahan status dari open → pending
3. **Data Collection Issues**: Filter context="data_collection_*"
4. **Performance**: Check timestamp gap antara incoming dan outgoing

## Thread Safety
Logger menggunakan threading.Lock untuk memastikan concurrent writes aman.
