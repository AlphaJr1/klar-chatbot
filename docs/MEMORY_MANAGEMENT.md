# Memory Management Tools

## Overview

Alat bantu untuk mengelola memory chatbot dengan aman dan mudah. Tersedia dalam 2 versi:

- **Python script** (`scripts/clear_memory.py`) - Recommended, lebih detail
- **Bash script** (`bin/clear_memory.sh`) - Lebih cepat, lebih simple

## Fitur Utama

### 1. Hapus User Tertentu

- Menampilkan list semua user_id yang ada
- Menampilkan detail user (nama, produk, waktu dibuat)
- Hapus user secara selektif
- Konfirmasi sebelum menghapus

### 2. Kosongkan Memory Total

- Menghapus semua data user sekaligus
- Konfirmasi ganda untuk keamanan
- Backup otomatis sebelum menghapus

### 3. Cancel

- Kembali tanpa melakukan perubahan
- Server tetap di-restart

## Cara Penggunaan

### Versi Python (Recommended)

```bash
cd /Users/adrianalfajri/Projects/klar-rag
python3 scripts/clear_memory.py
```

**Output Example:**

```
============================================================
🗑️  MEMORY MANAGEMENT TOOL
============================================================

⏳ Menghentikan server...

============================================================
PILIH AKSI:
============================================================

1. Hapus user_id tertentu
2. Kosongkan memory total
3. Cancel (restart server tanpa perubahan)

Pilihan (1-3): 1

------------------------------------------------------------
📋 DAFTAR USER_ID YANG ADA:
------------------------------------------------------------
 1. test_happy_male
     Nama: Budi Santoso, Produk: F57A, Dibuat: 2025-11-21T07:21:45Z
 2. test_happy_female
     Nama: Siti Nurhaliza, Produk: F90A, Dibuat: 2025-11-21T07:21:53Z

Total: 2 user
------------------------------------------------------------

Masukkan user_id yang ingin dihapus
(bisa copy-paste dari daftar di atas)

User ID: test_happy_male

📝 Detail user yang akan dihapus:
   User ID: test_happy_male
   Nama: Budi Santoso
   Produk: F57A
   Dibuat: 2025-11-21T07:21:45Z

⚠️  Apakah Anda yakin akan menghapus user ini? (y/n): y

💾 Backup dibuat: data/storage/backups/memory_backup_20251125_132207.json
✅ User 'test_happy_male' berhasil dihapus!

============================================================
✅ PROSES SELESAI
============================================================

⏳ Restarting server...
```

### Versi Bash

```bash
cd /Users/adrianalfajri/Projects/klar-rag
./bin/clear_memory.sh
```

**Lebih simple, tanpa detail user tetapi tetap fungsional**

## Backup System

### Lokasi Backup

Semua backup disimpan di: `data/storage/backups/`

### Format Nama File

`memory_backup_YYYYMMDD_HHMMSS.json`

Contoh: `memory_backup_20251125_132207.json`

### Restore dari Backup

Jika ingin restore backup:

```bash
# 1. Stop server
./bin/stop_all.sh

# 2. List backup yang tersedia
ls -lht data/storage/backups/

# 3. Copy backup ke memory.json
cp data/storage/backups/memory_backup_20251125_132207.json data/storage/memory.json

# 4. Start server
./bin/start_daemon.sh
```

## Flow Diagram

```
┌─────────────────────────────────┐
│   Jalankan Script               │
└──────────┬──────────────────────┘
           │
           ▼
┌─────────────────────────────────┐
│   Stop Server Otomatis          │
└──────────┬──────────────────────┘
           │
           ▼
┌─────────────────────────────────┐
│   Tampilkan Menu:               │
│   1. Hapus user tertentu        │
│   2. Kosongkan semua            │
│   3. Cancel                     │
└──────────┬──────────────────────┘
           │
           ▼
    ┌──────┴──────┐
    │   Pilihan?  │
    └──────┬──────┘
           │
    ┌──────┼──────┬──────────┐
    ▼      ▼      ▼          ▼
  [1]    [2]    [3]      [Invalid]
    │      │      │          │
    │      │      │          ▼
    │      │      │      Tampilkan
    │      │      │        Error
    │      │      │          │
    │      │      └──────────┤
    │      │                 │
    │      ▼                 │
    │  ┌────────────────┐   │
    │  │ Konfirmasi YES │   │
    │  └────────┬───────┘   │
    │           │            │
    ▼           ▼            │
┌────────────────────────┐  │
│  Backup Otomatis      │  │
└──────┬─────────────────┘  │
       │                    │
       ▼                    │
┌────────────────────────┐  │
│  Proses Perubahan     │  │
└──────┬─────────────────┘  │
       │                    │
       └────────────────────┤
                            │
                            ▼
                 ┌─────────────────────┐
                 │  Restart Server     │
                 └─────────────────────┘
                            │
                            ▼
                        [Selesai]
```

## Safety Features

1. **Auto Stop Server**: Server dihentikan otomatis sebelum modifikasi
2. **Auto Backup**: Backup dibuat sebelum setiap perubahan
3. **Konfirmasi**: Meminta konfirmasi sebelum delete
4. **Double Confirm**: Untuk clear all, harus ketik "YES"
5. **Auto Restart**: Server restart otomatis setelah selesai
6. **Error Handling**: Menangani error dengan graceful

## Troubleshooting

### Script tidak bisa dijalankan

```bash
# Make sure script executable
chmod +x scripts/clear_memory.py
chmod +x bin/clear_memory.sh
```

### Server tidak berhenti

```bash
# Manual stop
./bin/stop_all.sh

# Atau kill manual
lsof -ti:8081 | xargs kill -9
pkill -f ngrok
```

### Memory.json corrupt

```bash
# Restore dari backup
cp data/storage/backups/memory_backup_XXXXXX.json data/storage/memory.json

# Atau reset dengan empty
echo "{}" > data/storage/memory.json
```

### Server tidak restart

```bash
# Manual restart
./bin/start_daemon.sh

# Atau
uvicorn src.api:app --host 0.0.0.0 --port 8081 --reload
```

## Best Practices

1. **Regular Cleanup**: Bersihkan test users secara berkala
2. **Check Backup**: Pastikan backup tercipta sebelum clear all
3. **Production**: Hati-hati saat clear production data
4. **Monitor Size**: Jika memory.json > 10MB, pertimbangkan cleanup
5. **Document**: Catat alasan cleanup untuk reference

## Advanced Usage

### View Backup Content

```bash
# List semua backup
ls -lht data/storage/backups/

# View isi backup
cat data/storage/backups/memory_backup_20251125_132207.json | jq .

# Count users in backup
cat data/storage/backups/memory_backup_20251125_132207.json | jq 'keys | length'
```

### Selective Restore

```python
# Restore hanya user tertentu dari backup
import json

# Load backup
with open('data/storage/backups/memory_backup_20251125_132207.json') as f:
    backup = json.load(f)

# Load current
with open('data/storage/memory.json') as f:
    current = json.load(f)

# Restore specific user
user_id = 'test_user_123'
if user_id in backup:
    current[user_id] = backup[user_id]

# Save
with open('data/storage/memory.json', 'w') as f:
    json.dump(current, f, indent=2)
```

### Scheduled Cleanup

```bash
# Crontab untuk cleanup otomatis setiap minggu
# Edit crontab: crontab -e

# Setiap minggu, Minggu jam 2 pagi, clear test users
0 2 * * 0 cd /Users/adrianalfajri/Projects/klar-rag && python3 scripts/scheduled_cleanup.py
```

## Related Files

- `data/storage/memory.json` - File memory utama
- `data/storage/backups/` - Folder backup
- `bin/stop_all.sh` - Script stop server
- `bin/start_daemon.sh` - Script start server
- `scripts/clear_memory.py` - Python version
- `bin/clear_memory.sh` - Bash version
