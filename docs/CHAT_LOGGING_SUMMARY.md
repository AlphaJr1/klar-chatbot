# Chat Logging Implementation Summary

## ✅ Yang Sudah Dikerjakan

### 1. Chat Logger Module (`src/convo/chat_logger.py`)
- Logger terpisah khusus untuk mencatat chat masuk dan keluar
- Thread-safe dengan menggunakan threading.Lock
- File output: `data/storage/logs/chat-YYYY-MM-DD.jsonl`
- Format: JSON Lines (satu JSON per baris)

### 2. Integration ke Engine (`src/convo/engine.py`)
- Import `chat_logger` module
- Initialize `self.chat_logger` di `__init__`
- Helper method `_log_and_return()` untuk DRY logging
- **Semua return statement di function `handle()`** sudah diupdate untuk log

### 3. Logging Detail

#### Incoming Message
Mencatat:
- Timestamp
- User ID
- Message text & length
- Metadata:
  - gateway_only mode
  - sop_pending status
  - active_intent
  - user_name, user_product
  - has_address

#### Outgoing Message
Mencatat:
- Timestamp
- User ID  
- Response text & length
- Status (open/pending/resolved)
- Metadata:
  - status & next_action
  - active_intent & sop_pending
  - bubble_count
  - user data (name, product, address)
  - data_collection_complete & next_field_needed
  - **context** (untuk debugging)

#### Context Values
Semua response memiliki context tag:
- `empty_message`, `empty_message_with_pending`
- `early_distraction_handled`, `chitchat_distraction_handled`
- `greeting_only`, `gateway_greeting`
- `pending_just_triggered`
- `data_collection_*` (berbagai stage)
- `no_intent_detected`
- `handle_exploration`

### 4. Dokumentasi (`docs/CHAT_LOGGING.md`)
- Format log lengkap dengan contoh
- Real flow examples
- Cara membaca log (jq, Python)
- Tips debugging

### 5. Utility Scripts

#### `scripts/view_chat_logs.py`
Tool untuk view & analyze logs:
```bash
# Lihat semua log hari ini
python scripts/view_chat_logs.py

# Lihat log user tertentu
python scripts/view_chat_logs.py --user 5678

# Lihat hanya incoming messages
python scripts/view_chat_logs.py --direction incoming

# Lihat dengan detail
python scripts/view_chat_logs.py -v

# Lihat statistics
python scripts/view_chat_logs.py --stats

# Filter by status
python scripts/view_chat_logs.py --status pending

# Filter by context
python scripts/view_chat_logs.py --context data_collection
```

#### `scripts/test_chat_logger.py`
Test script untuk verifikasi:
```bash
python scripts/test_chat_logger.py
```

## 🎯 Contoh Output Log

### Sample Flow
```jsonl
{"ts":"2025-11-24T07:00:00Z","direction":"incoming","user_id":"628xxx","message":"AC mati","message_length":7,"metadata":{"active_intent":"none","sop_pending":false}}
{"ts":"2025-11-24T07:00:01Z","direction":"outgoing","user_id":"628xxx","response":"Baik kak, AC mati ya? Boleh dicek lampu indikatornya?","status":"unknown","metadata":{"active_intent":"mati","context":"handle_exploration"}}
{"ts":"2025-11-24T07:01:00Z","direction":"incoming","user_id":"628xxx","message":"tetap mati","message_length":10,"metadata":{"active_intent":"mati","sop_pending":false}}
{"ts":"2025-11-24T07:01:01Z","direction":"outgoing","user_id":"628xxx","response":"Baik kak, saya teruskan ke teknisi ya. | Baik Kak, boleh tahu pembeliannya atas nama siapa?","status":"open","metadata":{"sop_pending":true,"context":"pending_just_triggered","next_field_needed":"name"}}
{"ts":"2025-11-24T07:02:00Z","direction":"incoming","user_id":"628xxx","message":"Budi","message_length":4,"metadata":{"sop_pending":true,"user_name":null}}
{"ts":"2025-11-24T07:02:01Z","direction":"outgoing","user_id":"628xxx","response":"Baik Pak, untuk produknya F57A atau F90A?","status":"open","metadata":{"user_name":"Budi","next_field_needed":"product","context":"data_collection_normal"}}
```

## 📊 Kegunaan

### 1. Debugging
- Track full conversation flow
- Identify di mana bot "stuck"
- Monitor state transitions (open → pending)

### 2. Monitoring
- Hitung total messages per hari
- Lihat distribusi status (berapa yang pending, resolved)
- Track user engagement

### 3. Analytics
- Intent distribution (mati vs bau vs bunyi)
- Data collection completion rate
- Response time analysis (gap antara incoming-outgoing)

### 4. Quality Assurance
- Review actual conversations
- Find edge cases
- Improve prompts based on real data

## 🧪 Testing

```bash
# 1. Run test
python scripts/test_chat_logger.py

# 2. View hasil test
python scripts/view_chat_logs.py --user 001 -v

# 3. Check statistics
python scripts/view_chat_logs.py --stats
```

## 📁 File Structure
```
klar-rag/
├── src/convo/
│   ├── chat_logger.py          # Logger module
│   └── engine.py                # Updated with logging
├── scripts/
│   ├── view_chat_logs.py       # Log viewer tool
│   └── test_chat_logger.py     # Test script
├── docs/
│   └── CHAT_LOGGING.md         # Full documentation
└── data/storage/logs/
    └── chat-YYYY-MM-DD.jsonl   # Log files
```

## ✨ Ready to Test!

Sistem logging sudah lengkap dan siap ditest. Setiap chat masuk dan keluar akan tercatat otomatis dengan detail lengkap.
