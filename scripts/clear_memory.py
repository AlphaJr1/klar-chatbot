#!/usr/bin/env python3

import json
import os
import sys
import subprocess
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
MEMORY_FILE = PROJECT_ROOT / "data/storage/memory.json"
BACKUP_DIR = PROJECT_ROOT / "data/storage/backups"
STOP_SCRIPT = PROJECT_ROOT / "bin/stop_all.sh"
START_SCRIPT = PROJECT_ROOT / "bin/start_daemon.sh"

def print_header(text):
    print("\n" + "=" * 60)
    print(text)
    print("=" * 60 + "\n")

def print_separator():
    print("-" * 60)

def stop_server():
    print("⏳ Menghentikan server...")
    try:
        subprocess.run([str(STOP_SCRIPT)], check=True, cwd=str(PROJECT_ROOT))
        print()
    except subprocess.CalledProcessError:
        print("⚠️  Warning: Gagal menghentikan server dengan script")
        subprocess.run(["lsof", "-ti:8081"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def start_server():
    print("\n⏳ Restarting server...")
    try:
        subprocess.run([str(START_SCRIPT)], check=True, cwd=str(PROJECT_ROOT))
    except subprocess.CalledProcessError:
        print("❌ ERROR: Gagal restart server!")
        print(f"   Jalankan manual: {START_SCRIPT}")

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

def load_memory():
    if not MEMORY_FILE.exists():
        print(f"❌ ERROR: File memory tidak ditemukan di {MEMORY_FILE}")
        sys.exit(1)
    
    with open(MEMORY_FILE, 'r') as f:
        return json.load(f)

def save_memory(data):
    with open(MEMORY_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def list_users():
    data = load_memory()
    users = sorted(data.keys())
    
    print_separator()
    print("📋 DAFTAR USER_ID YANG ADA:")
    print_separator()
    
    if not users:
        print("❌ Tidak ada user di memory")
        return []
    
    for idx, user_id in enumerate(users, 1):
        user_data = data[user_id]
        name = user_data.get('name', 'N/A')
        product = user_data.get('product', 'N/A')
        created = user_data.get('created_at', 'N/A')
        print(f"{idx:2d}. {user_id}")
        print(f"     Nama: {name}, Produk: {product}, Dibuat: {created}")
    
    print(f"\nTotal: {len(users)} user")
    print_separator()
    
    return users

def delete_user(user_id):
    data = load_memory()
    
    if user_id not in data:
        print(f"❌ User '{user_id}' tidak ditemukan!")
        return False
    
    print(f"\n📝 Detail user yang akan dihapus:")
    user_data = data[user_id]
    print(f"   User ID: {user_id}")
    print(f"   Nama: {user_data.get('name', 'N/A')}")
    print(f"   Produk: {user_data.get('product', 'N/A')}")
    print(f"   Dibuat: {user_data.get('created_at', 'N/A')}")
    
    confirm = input(f"\n⚠️  Apakah Anda yakin akan menghapus user ini? (y/n): ").strip().lower()
    
    if confirm not in ['y', 'yes']:
        print("❌ Dibatalkan!")
        return False
    
    create_backup()
    del data[user_id]
    save_memory(data)
    
    print(f"✅ User '{user_id}' berhasil dihapus!")
    return True

def clear_all_memory():
    data = load_memory()
    total_users = len(data)
    
    print(f"\n⚠️  {'=' * 50}")
    print(f"⚠️  PERINGATAN: SEMUA DATA MEMORY AKAN DIHAPUS!")
    print(f"⚠️  Total {total_users} user akan dihapus permanen!")
    print(f"⚠️  {'=' * 50}")
    
    confirm = input("\nApakah Anda BENAR-BENAR YAKIN? (ketik 'YES' untuk konfirmasi): ").strip()
    
    if confirm != 'YES':
        print("❌ Dibatalkan!")
        return False
    
    create_backup()
    save_memory({})
    
    print(f"✅ Semua memory berhasil dikosongkan! ({total_users} user dihapus)")
    return True

def main():
    print_header("🗑️  MEMORY MANAGEMENT TOOL")
    
    stop_server()
    
    print_header("PILIH AKSI:")
    print("1. Hapus user_id tertentu")
    print("2. Kosongkan memory total")
    print("3. Cancel (restart server tanpa perubahan)")
    
    try:
        choice = input("\nPilihan (1-3): ").strip()
        
        changed = False
        
        if choice == "1":
            users = list_users()
            if users:
                print("\nMasukkan user_id yang ingin dihapus")
                print("(bisa copy-paste dari daftar di atas)")
                user_id = input("\nUser ID: ").strip()
                
                if user_id:
                    changed = delete_user(user_id)
                else:
                    print("❌ User_id tidak boleh kosong!")
        
        elif choice == "2":
            changed = clear_all_memory()
        
        elif choice == "3":
            print("\n❌ Dibatalkan - tidak ada perubahan")
        
        else:
            print("\n❌ Pilihan tidak valid!")
        
        if changed:
            print_header("✅ PROSES SELESAI")
        
    except KeyboardInterrupt:
        print("\n\n❌ Dibatalkan oleh user (Ctrl+C)")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        start_server()
        print_header("✅ SELESAI - Server sudah berjalan kembali")

if __name__ == "__main__":
    main()
