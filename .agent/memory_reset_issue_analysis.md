# Analisis: Memory Reset Issue - User 6282216860317

## Masalah

Bot selalu merespons dengan **"Selamat datang! Bagaimana saya bisa membantu Anda hari ini?"** untuk user `6282216860317`, meskipun user mengatakan "eac saya rusak", "saya ingin bertanya mengenai EAC", dll.

## Root Cause

### Penyebab Utama

Memory user **6282216860317** ter-**reset/dihapus** pada sekitar jam **06:38:46 UTC (13:38 WIB)**.

### Bukti

1. **Backup sebelum reset** (`memory_backup_20251125_132811.json`):

   ```json
   {
     "name": "Pak Budi",
     "product": "F57A",
     "address": "jalan gatot subroto, no 45, jakarta selatan",
     "flags": {
       "active_intent": "bunyi",
       "sop_pending": true
     }
   }
   ```

2. **Memory setelah reset**:
   ```json
   {
     "name": null,
     "product": null,
     "address": null,
     "flags": {
       "last_activity": "2025-11-25T06:38:46Z",
       "last_greeted_date": "2025-11-25"
     }
   }
   ```

### Flow Masalah

```
User sends: "halo eac saya rusak"
    ↓
Engine load memory → semua null
    ↓
LLM Intent Detection → "has_greeting": true, "issue_part": ""
    ↓
masuk ke greeting_only handler (line 1925 engine.py)
    ↓
Response: "Selamat datang! Bagaimana saya bisa membantu Anda hari ini?"
```

## Investigasi: Apakah Auto-Delete Saat Startup?

### ✅ Clear Memory Script **TIDAK** Auto-Run

**File:** `bin/clear_memory.sh`

- Script ini adalah **interactive tool** yang memerlukan manual input
- **TIDAK dipanggil** oleh `start_daemon.sh` atau script startup lainnya
- Hanya untuk manual cleanup memory

```bash
# start_daemon.sh TIDAK memanggil clear_memory.sh
# Hanya: cleanup port, start uvicorn, start ngrok
```

### ✅ Memory Store **TIDAK** Auto-Delete

**File:** `src/convo/memory_store.py`

1. **`__init__` method**:

   - Hanya create file `{}` jika tidak exist
   - Load data dari file
   - **TIDAK ada auto-delete**

2. **`_load` method**:

   - Ada fallback reset ke `{}` **HANYA** jika JSON corrupted/invalid
   - Error message: `"Failed to load: {e}. Resetting memory.json to empty {}"`
   - **Tidak ada log error ini** di server log

3. **No Auto-Clear Calls**:
   ```bash
   # Dicek di seluruh codebase:
   grep -r "reset_all\|memstore.clear" src/
   # Result: Tidak ada pemanggilan otomatis
   ```

## Kemungkinan Penyebab Reset

Setelah investigasi menyeluruh, berikut kemungkinan penyebab:

### 1. ✅ **Manual Deletion via Scripts**

Paling mungkin: Seseorang menjalankan salah satu dari:

- `bin/clear_memory.sh` → pilih option 1 (delete specific user) atau 2 (clear all)
- `scripts/clear_memory.py` → sama, interactive

**Bukti:**

- Backup created: `memory_backup_20251125_132811.json` (13:28 WIB)
- Memory reset terjadi sekitar 13:38 WIB (10 menit kemudian)
- Ini pattern dari clear_memory script (create backup → delete)

### 2. ❓ **Corrupt JSON (Low Probability)**

Jika `memory.json` ter-corrupt, `MemoryStore._load()` akan reset ke `{}`.

**Namun:**

- Tidak ada error log `"Failed to load"`
- Backup menunjukkan JSON valid pada 13:28

### 3. ❓ **External Process/Tool**

Kemungkinan kecil: IDE, text editor, atau tool lain mengoverwrite file.

**Namun:**

- Atomic write protection sudah ada di `memory_store.py`
- File lock protection via `threading.RLock`

## Timeline Issue

- **06:24** - User memiliki data lengkap, status pending
- **13:28** - Backup created (masih ada data user)
- **13:38** - Memory ter-reset (semua data jadi null) ← **RESET TERJADI DI SINI**
- **14:17** - User mulai komplain bot tidak respon dengan benar
- **14:24** - Issue terdeteksi dan di-fix dengan restore dari backup

## Solusi yang Diterapkan

### Fix Immediate

1. **Restore dari backup**:

   ```python
   # Restore user data
   current['6282216860317'] = backup['6282216860317']
   ```

2. **Restart server** untuk reload memory:
   ```bash
   bin/stop_all.sh
   bin/start_daemon.sh
   ```

### Hasil

✅ Bot sekarang merespons dengan benar:

```json
{
  "text": "Terima kasih, Pak Budi. Data yang Anda berikan telah kami terima..."
}
```

## Pencegahan di Masa Depan

### Rekomendasi Immediate

1. **⚠️ Warning di Clear Memory Scripts**

   Update `bin/clear_memory.sh` dan `scripts/clear_memory.py`:

   ```bash
   # Tambahkan warning
   echo "⚠️  WARNING: User dengan sop_pending=true akan terhapus!"
   echo "⚠️  Cek dulu apakah ada active cases sebelum delete!"
   ```

2. **Protected Users - Prevent Accidental Delete**

   Tambahkan protection untuk active users:

   ```python
   # Di clear_memory.py
   def is_protected_user(user_data):
       """User dengan active case tidak boleh dihapus"""
       flags = user_data.get("flags", {})
       return (
           flags.get("sop_pending") or
           flags.get("active_intent") or
           user_data.get("name")  # User yang sudah isi data
       )
   ```

3. **Audit Log**

   Log setiap memory modification:

   ```python
   # audit_log.json
   {
     "ts": "2025-11-25T13:38:46Z",
     "action": "delete_user",
     "user_id": "6282216860317",
     "deleted_by": "clear_memory.sh",
     "data_before": {...}
   }
   ```

4. **Auto-Backup Before Cleanup**

   Sudah ada, tapi bisa ditingkatkan:

   - Retention: Keep last 7 days
   - Auto-restore prompt jika ada error

### Rekomendasi Long-term

1. **Memory Version Control**

   - Track changes dengan git-like versioning
   - Easy rollback jika terjadi accident

2. **Web-based Memory Manager**

   - UI untuk view/edit/delete users
   - Visual indicators untuk protected users
   - Confirmation modal sebelum delete

3. **Monitoring Dashboard**
   - Alert jika ada mass deletion
   - Track active users count
   - Show protected vs deletable users

## Kesimpulan

### ✅ Konfirmasi

**BUKAN** karena auto-delete saat startup. Script `clear_memory.sh` dan `start_daemon.sh` **tidak** otomatis menghapus memory.

### 🎯 Root Cause (High Probability)

Memory user ter-reset karena **manual deletion** via `clear_memory` script sekitar jam 13:38 WIB.

### 📋 Action Items

1. ✅ Memory sudah di-restore
2. ⚠️ Add protection untuk active users
3. 📊 Implement audit logging
4. 🔔 Add warning di clear_memory scripts

## Catatan Penting

⚠️ **Memory deletion bisa terjadi kapan saja** jika script cleanup dijalankan. Pastikan:

- ✅ Selalu ada backup berkala (sudah ada)
- ⚠️ Warning jelas sebelum delete (perlu ditambahkan)
- 📊 Audit trail untuk tracking (perlu diimplementasi)
- 🛡️ Protection untuk active users (perlu diimplementasi)
