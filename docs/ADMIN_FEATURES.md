# Admin Features - Memory Reset

## Fitur Hack: Reset Memory User dari Webhook

Fitur ini memungkinkan developer untuk reset memory user langsung dari WhatsApp tanpa perlu akses ke server FastAPI.

---

## 🔐 Security

Secret key disimpan di `.env`:

```bash
ADMIN_SECRET_KEY=dev_reset_2024
```

**PENTING**: Ganti secret key ini dengan value yang lebih secure di production!

---

## 🎯 Cara Penggunaan

### 1. Reset Memory via WhatsApp (Webhook)

Kirim pesan ke nomor WhatsApp dengan format:

```
/dev reset dev_reset_2024
```

**Format**:

```
/dev reset {SECRET_KEY}
```

**Respon Sukses**:

```
✅ Memory reset berhasil untuk user: 6281234567890
```

**Respon Gagal (Secret Invalid)**:

```
❌ Invalid secret key
```

**Catatan**:

- Command ini akan menghapus seluruh memory untuk user yang mengirim pesan
- User ID diambil otomatis dari `payload.user_id`
- Pesan ini TIDAK diteruskan ke conversation engine

---

### 2. Reset Memory via API Endpoint

Jika tidak bisa kirim via WhatsApp, bisa gunakan endpoint API langsung:

**Endpoint**: `POST /admin/reset-memory`

**Method**: POST

**Query Params**:

- `user_id` (required): ID user yang mau direset
- `secret` (required): Secret key admin

**Contoh cURL**:

```bash
curl -X POST "http://localhost:8000/admin/reset-memory?user_id=6281234567890&secret=dev_reset_2024"
```

**Response**:

```json
{
  "ok": true,
  "message": "Memory reset berhasil untuk user: 6281234567890",
  "user_id": "6281234567890"
}
```

---

### 3. Cek Memory Stats (Bonus Feature)

**Endpoint**: `GET /admin/memory-stats`

**Query Params**:

- `secret` (required): Secret key admin

**Contoh cURL**:

```bash
curl "http://localhost:8000/admin/memory-stats?secret=dev_reset_2024"
```

**Response**:

```json
{
  "ok": true,
  "stats": {
    "total_users": 5,
    "total_messages": 127,
    "last_updated": "2025-11-25T09:30:45Z"
  },
  "user_ids": ["6281234567890", "6281234567891", "6281234567892"],
  "total_users": 3
}
```

---

## 🧪 Testing

### Test via WhatsApp

1. Buka WhatsApp
2. Kirim pesan ke bot: `/dev reset dev_reset_2024`
3. Cek apakah memory sudah terhapus dengan kirim pesan biasa

### Test via API

```bash
# Reset memory user specific
curl -X POST "http://localhost:8000/admin/reset-memory?user_id=TEST_USER&secret=dev_reset_2024"

# Cek stats
curl "http://localhost:8000/admin/memory-stats?secret=dev_reset_2024"
```

---

## 🛡️ Security Notes

1. **Jangan share secret key** di file yang di-commit ke git
2. **Gunakan secret yang complex** di production (bukan `dev_reset_2024`)
3. **Command ini powerful** - bisa menghapus seluruh conversation history user
4. **Log setiap penggunaan** - check terminal untuk log `[MemoryStore] Session token refreshed`

---

## 📝 Implementation Details

### Flow Diagram

```
WhatsApp User
    |
    | "/dev reset dev_reset_2024"
    v
Node.js Server (server2_1.js)
    |
    | POST /chat
    v
FastAPI (api.py)
    |
    | Check if text starts with "/dev reset "
    v
Extract secret from message
    |
    | Compare with ADMIN_SECRET_KEY
    v
    [Valid?]
    |
    +-- NO --> Return "Invalid secret key"
    |
    +-- YES --> engine.memory.clear(user_id)
                    |
                    v
                Return "Memory reset berhasil"
```

### Code Location

- Main logic: `src/api.py` line 93-120
- Admin endpoints: `src/api.py` line 278-315
- Memory clear method: `src/convo/memory_store.py` line 171-177

---

## 🔧 Troubleshooting

### Error: "Invalid secret key"

- Pastikan secret key di message sama persis dengan value di `.env`
- Cek tidak ada extra space: `/dev reset dev_reset_2024` ✅
- Wrong: `/dev reset  dev_reset_2024` ❌ (ada 2 spasi)

### Error: "Gagal reset memory"

- Check log error di terminal server FastAPI
- Pastikan `memory.json` tidak corrupt
- Restart server FastAPI

### Command tidak detected

- Pastikan format **exact**: `/dev reset {SECRET}`
- Case sensitive untuk secret key
- Harus ada spasi setelah "reset"

---

## 📚 Use Cases

1. **User complain bot ngaco**: Reset memory langsung dari WA
2. **Testing flow baru**: Reset user test tanpa restart server
3. **User data corrupt**: Clear memory untuk fresh start
4. **Emergency troubleshooting**: Fast reset tanpa akses server

---

## ⚠️ Warnings

- ❌ **TIDAK ADA UNDO**: Memory yang sudah dihapus tidak bisa dikembalikan
- ❌ **TIDAK ADA CONFIRMATION**: Langsung execute begitu secret valid
- ❌ **Menghapus SEMUA data user**: Name, product, address, history, semua hilang
- ✅ **User ID tetap ada**: Record kosong baru akan dibuat otomatis saat user chat lagi

---

## 🎓 Advanced: Custom Commands

Bisa extend dengan command lain, contoh:

```python
# Di api.py, tambahkan setelah check reset command:

elif user_text.startswith("/dev stats "):
    parts = user_text.split()
    if len(parts) >= 3 and parts[2] == ADMIN_SECRET:
        stats = engine.memory.get(payload.user_id)
        return {
            "bubbles": [{"type": "text", "text": f"User stats:\n{json.dumps(stats, indent=2)}"}],
            "next": "await_reply",
            "status": "open"
        }
```

Happy hacking! 🚀
