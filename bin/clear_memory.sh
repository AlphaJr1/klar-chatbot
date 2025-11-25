#!/bin/bash

# Script untuk mengelola memory chatbot
# Fitur: hapus user tertentu, kosongkan semua memory, atau cancel

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

MEMORY_FILE="data/storage/memory.json"
BACKUP_DIR="data/storage/backups"

echo "════════════════════════════════════════════════════════════"
echo "🗑️  MEMORY MANAGEMENT TOOL"
echo "════════════════════════════════════════════════════════════"
echo ""

if [ ! -f "$MEMORY_FILE" ]; then
    echo "❌ ERROR: File memory tidak ditemukan di $MEMORY_FILE"
    exit 1
fi

echo "⏳ Menghentikan server..."
bin/stop_all.sh
echo ""

echo "════════════════════════════════════════════════════════════"
echo "PILIH AKSI:"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "1. Hapus user_id tertentu"
echo "2. Kosongkan memory total"
echo "3. Cancel (restart server tanpa perubahan)"
echo ""
read -p "Pilihan (1-3): " choice

case $choice in
    1)
        echo ""
        echo "─────────────────────────────────────────────────────────"
        echo "📋 DAFTAR USER_ID YANG ADA:"
        echo "─────────────────────────────────────────────────────────"
        
        users=$(cat "$MEMORY_FILE" | grep -o '"user_id"[[:space:]]*:[[:space:]]*"[^"]*"' | grep -o '"[^"]*"$' | tr -d '"' | sort -u)
        
        if [ -z "$users" ]; then
            echo "❌ Tidak ada user di memory"
        else
            echo "$users" | nl -w2 -s'. '
            total=$(echo "$users" | wc -l | xargs)
            echo ""
            echo "Total: $total user"
        fi
        
        echo "─────────────────────────────────────────────────────────"
        echo ""
        read -p "Masukkan user_id yang ingin dihapus: " user_id
        
        if [ -z "$user_id" ]; then
            echo "❌ User_id tidak boleh kosong!"
            echo "⏳ Restarting server..."
            bin/start_daemon.sh
            exit 1
        fi
        
        echo ""
        echo "⚠️  Apakah Anda yakin akan menghapus user: $user_id ?"
        read -p "Konfirmasi (y/n): " confirm
        
        if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
            echo "❌ Dibatalkan!"
            echo "⏳ Restarting server..."
            bin/start_daemon.sh
            exit 0
        fi
        
        mkdir -p "$BACKUP_DIR"
        backup_file="$BACKUP_DIR/memory_backup_$(date +%Y%m%d_%H%M%S).json"
        cp "$MEMORY_FILE" "$backup_file"
        echo "💾 Backup dibuat: $backup_file"
        
        temp_file=$(mktemp)
        python3 << EOF
import json
import sys

try:
    with open('$MEMORY_FILE', 'r') as f:
        data = json.load(f)
    
    if '$user_id' in data:
        del data['$user_id']
        with open('$temp_file', 'w') as f:
            json.dump(data, f, indent=2)
        print("✅ User '$user_id' berhasil dihapus!")
        sys.exit(0)
    else:
        print("❌ User '$user_id' tidak ditemukan!")
        sys.exit(1)
except Exception as e:
    print(f"❌ ERROR: {e}")
    sys.exit(1)
EOF
        
        if [ $? -eq 0 ]; then
            mv "$temp_file" "$MEMORY_FILE"
            echo "✅ Memory berhasil diupdate!"
        else
            rm -f "$temp_file"
            echo "❌ Gagal menghapus user!"
        fi
        ;;
        
    2)
        echo ""
        echo "⚠️  ==============================================="
        echo "⚠️  PERINGATAN: SEMUA DATA MEMORY AKAN DIHAPUS!"
        echo "⚠️  ==============================================="
        read -p "Apakah Anda BENAR-BENAR YAKIN? (ketik 'YES' untuk konfirmasi): " confirm
        
        if [ "$confirm" != "YES" ]; then
            echo "❌ Dibatalkan!"
            echo "⏳ Restarting server..."
            bin/start_daemon.sh
            exit 0
        fi
        
        mkdir -p "$BACKUP_DIR"
        backup_file="$BACKUP_DIR/memory_backup_$(date +%Y%m%d_%H%M%S).json"
        cp "$MEMORY_FILE" "$backup_file"
        echo "💾 Backup dibuat: $backup_file"
        
        echo "{}" > "$MEMORY_FILE"
        echo "✅ Semua memory berhasil dikosongkan!"
        ;;
        
    3)
        echo ""
        echo "❌ Dibatalkan - tidak ada perubahan"
        echo "⏳ Restarting server..."
        bin/start_daemon.sh
        exit 0
        ;;
        
    *)
        echo ""
        echo "❌ Pilihan tidak valid!"
        echo "⏳ Restarting server..."
        bin/start_daemon.sh
        exit 1
        ;;
esac

echo ""
echo "════════════════════════════════════════════════════════════"
echo "✅ PROSES SELESAI"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "⏳ Restarting server..."
bin/start_daemon.sh

echo ""
echo "════════════════════════════════════════════════════════════"
echo "✅ SELESAI - Server sudah berjalan kembali"
echo "════════════════════════════════════════════════════════════"
