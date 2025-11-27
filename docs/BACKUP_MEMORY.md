# Fitur Backup Memory Otomatis

## Deskripsi

Setiap kali memory user direset (baik melalui API `/dev reset` atau endpoint `/admin/reset-memory`), sistem akan otomatis membuat backup file sebelum menghapus data.

## Lokasi Backup

- **Folder**: `data/storage/backups/`
- **Format file**: `memory_backup_{user_id}_{timestamp}.json`
- **Contoh**: `memory_backup_628123456789_20251127_062550.json`

## Format Data Backup

```json
{
  "user_id": "628123456789",
  "backup_timestamp": "2025-11-27T06:25:50Z",
  "record": {
    "user_id": "628123456789",
    "session_token": "f504043440b76ce5",
    "name": "Budi",
    "product": "Electronic Air Cleaner F57A",
    "history": [...],
    "flags": {...},
    "slots": {...}
  }
}
```

## Cara Menggunakan

### 1. Reset via Chat API dengan `/dev reset`

```bash
curl -X POST http://localhost:8080/chat \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "628123456789",
    "text": "/dev reset dev_reset_2024"
  }'
```

### 2. Reset via Admin Endpoint

```bash
curl -X POST "http://localhost:8080/admin/reset-memory?user_id=628123456789&secret=dev_reset_2024"
```

## Restore Manual dari Backup

Jika perlu restore data dari backup:

1. Buka file backup di `data/storage/backups/`
2. Copy data dari field `record`
3. Masukkan kembali ke `data/storage/memory.json` untuk user yang bersangkutan

## Keamanan

- Folder backup di-gitignore (tidak ter-push ke repository)
- Hanya file `.gitkeep` yang di-track oleh git
- Secret key diperlukan untuk reset memory
