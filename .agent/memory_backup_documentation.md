# Memory Backup System - Dokumentasi

## ✅ Ya, SELALU Backup Sebelum Clear!

Kedua script clear memory **SELALU** membuat backup sebelum menghapus data.

---

## 🔒 Backup Mechanism

### 1. Script Bash: `bin/clear_memory.sh`

#### Delete Specific User (Option 1)

```bash
# Line 76-79
mkdir -p "$BACKUP_DIR"
backup_file="$BACKUP_DIR/memory_backup_$(date +%Y%m%d_%H%M%S).json"
cp "$MEMORY_FILE" "$backup_file"
echo "💾 Backup dibuat: $backup_file"

# Baru kemudian delete user
```

#### Clear All Memory (Option 2)

```bash
# Line 127-130
mkdir -p "$BACKUP_DIR"
backup_file="$BACKUP_DIR/memory_backup_$(date +%Y%m%d_%H%M%S).json"
cp "$MEMORY_FILE" "$backup_file"
echo "💾 Backup dibuat: $backup_file"

# Baru kemudian reset ke {}
echo "{}" > "$MEMORY_FILE"
```

---

### 2. Script Python: `scripts/clear_memory.py`

#### Delete Specific User

```python
# Line 129
create_backup()  # SELALU dipanggil sebelum delete
del data[user_id]
save_memory(data)
```

#### Clear All Memory

```python
# Line 152-153
create_backup()  # SELALU dipanggil sebelum clear
save_memory({})
```

#### Backup Function

```python
def create_backup():
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = BACKUP_DIR / f"memory_backup_{timestamp}.json"

    with open(MEMORY_FILE, 'r') as f:
        data = json.load(f)

    with open(backup_file, 'w') as f:
        json.dump(data, f, indent=2)

    print(f"💾 Backup dibuat: {backup_file}")
    return backup_file
```

---

## 📁 Backup Location

**Directory:** `data/storage/backups/`

**Format:** `memory_backup_YYYYMMDD_HHMMSS.json`

**Example:**

```
data/storage/backups/
├── memory_backup_20251125_145714.json  (8.4 KB)
└── memory_backup_20251125_132811.json  (380 KB)
```

---

## 🔄 Backup Flow

```
User runs clear_memory script
    ↓
Option dipilih (delete user / clear all)
    ↓
Konfirmasi (y/n atau YES)
    ↓
✅ BACKUP DIBUAT DULU  ← ALWAYS!
    ↓
Delete/Clear memory
    ↓
Save changes
    ↓
Server restart
```

---

## 🛡️ Safety Features

### 1. **Automatic Backup**

- ✅ Tidak perlu manual backup
- ✅ Timestamp otomatis di filename
- ✅ Directory auto-created jika tidak exist

### 2. **Confirmation Required**

- Delete user: `y/n` confirmation
- Clear all: `YES` confirmation (case-sensitive)

### 3. **Backup Before Action**

- ✅ Backup SELALU dibuat SEBELUM delete
- ✅ Tidak ada cara untuk skip backup
- ✅ Hard-coded di kedua script

### 4. **Server Management**

- ✅ Auto stop server sebelum clear
- ✅ Auto restart server setelah clear
- ✅ Prevents race condition

---

## 📊 Backup Examples

### Recent Backups

```bash
$ ls -lth data/storage/backups/

# Backup 1: Clear all memory (today)
memory_backup_20251125_145714.json  (8.4 KB)
# → Small size = empty/few users

# Backup 2: Before previous clear (today)
memory_backup_20251125_132811.json  (380 KB)
# → Large size = many users with data
```

---

## 🔧 Restore from Backup

Jika perlu restore (seperti yang kita lakukan tadi):

```bash
# 1. Stop server
bin/stop_all.sh

# 2. Restore dari backup
cp data/storage/backups/memory_backup_YYYYMMDD_HHMMSS.json \
   data/storage/memory.json

# 3. Start server
bin/start_daemon.sh
```

Atau menggunakan Python:

```python
import json

# Load backup
with open('data/storage/backups/memory_backup_20251125_132811.json', 'r') as f:
    backup = json.load(f)

# Restore specific user (or all)
with open('data/storage/memory.json', 'r') as f:
    current = json.load(f)

current['USER_ID'] = backup['USER_ID']

# Save
with open('data/storage/memory.json', 'w') as f:
    json.dump(current, f, indent=2)
```

---

## ⚠️ Important Notes

### Backup Retention

- **Manual deletion required** - backups tidak auto-delete
- **Disk space** - monitor jika banyak backups
- **Recommendation:** Keep last 7-14 days

### Backup Size

- Empty memory: ~2 bytes `{}`
- With users: varies (KB to MB)
- Average per user: ~1-2 KB

### What's Backed Up

✅ All user data:

- name, gender, product, address
- history (chat logs)
- flags (active_intent, sop_pending, etc.)
- slots
- timestamps

---

## 🎯 Best Practices

### Before Clearing Memory

1. ✅ Check backup directory untuk ensure ada space
2. ✅ Verify current memory size/users
3. ✅ Note timestamp untuk easy restore

### After Clearing Memory

1. ✅ Verify backup file created
2. ✅ Check backup file size (should match pre-clear)
3. ✅ Test restore jika critical

### Periodic Cleanup

```bash
# Delete backups older than 30 days
find data/storage/backups/ -name "memory_backup_*.json" -mtime +30 -delete
```

---

## ✅ Conclusion

**Ya, clear memory SELALU backup dulu!**

### Guarantees

- ✅ Automatic backup before any deletion
- ✅ Timestamped filenames
- ✅ No way to skip backup
- ✅ Safe by design

### Recovery

- ✅ Easy to restore dari backup
- ✅ Selective restore (specific user)
- ✅ Full restore (all users)

**You're safe!** 🛡️
