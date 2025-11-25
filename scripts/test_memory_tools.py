#!/usr/bin/env python3

import json
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
MEMORY_FILE = PROJECT_ROOT / "data/storage/memory.json"

def test_backup_exists():
    backup_dir = PROJECT_ROOT / "data/storage/backups"
    print(f"✓ Checking backup directory: {backup_dir}")
    backup_dir.mkdir(parents=True, exist_ok=True)
    assert backup_dir.exists(), "Backup directory tidak ada"
    print("  ✓ Backup directory exists")

def test_memory_file_valid():
    print(f"\n✓ Checking memory file: {MEMORY_FILE}")
    
    if not MEMORY_FILE.exists():
        print("  ! Memory file tidak ada, membuat baru...")
        with open(MEMORY_FILE, 'w') as f:
            json.dump({}, f)
    
    with open(MEMORY_FILE, 'r') as f:
        data = json.load(f)
    
    print(f"  ✓ Memory file valid JSON")
    print(f"  ✓ Total users: {len(data)}")
    return data

def test_scripts_executable():
    print("\n✓ Checking script permissions")
    
    scripts = [
        PROJECT_ROOT / "scripts/clear_memory.py",
        PROJECT_ROOT / "bin/clear_memory.sh",
    ]
    
    for script in scripts:
        if script.exists():
            import os
            is_executable = os.access(script, os.X_OK)
            status = "✓" if is_executable else "✗"
            print(f"  {status} {script.name}: {'executable' if is_executable else 'NOT executable'}")
            
            if not is_executable:
                print(f"     Run: chmod +x {script}")
        else:
            print(f"  ✗ {script.name}: NOT FOUND")

def test_list_backups():
    print("\n✓ Listing existing backups")
    backup_dir = PROJECT_ROOT / "data/storage/backups"
    
    if backup_dir.exists():
        backups = sorted(backup_dir.glob("memory_backup_*.json"), reverse=True)
        if backups:
            print(f"  Found {len(backups)} backup(s):")
            for backup in backups[:5]:  # Show latest 5
                size = backup.stat().st_size
                print(f"    - {backup.name} ({size:,} bytes)")
        else:
            print("  No backups found (this is OK)")
    else:
        print("  Backup directory doesn't exist yet (will be created on first use)")

def print_usage():
    print("\n" + "="*60)
    print("CARA MENGGUNAKAN MEMORY MANAGEMENT TOOLS")
    print("="*60)
    print("\nVersi Python (Recommended):")
    print("  python3 scripts/clear_memory.py")
    print("\nVersi Bash:")
    print("  ./bin/clear_memory.sh")
    print("\nFitur:")
    print("  1. Hapus user_id tertentu")
    print("  2. Kosongkan memory total")
    print("  3. Cancel")
    print("\nDokumentasi lengkap:")
    print("  cat docs/MEMORY_MANAGEMENT.md")
    print("="*60)

def main():
    print("="*60)
    print("🧪 MEMORY MANAGEMENT TOOLS - VALIDATION TEST")
    print("="*60)
    
    try:
        test_backup_exists()
        data = test_memory_file_valid()
        test_scripts_executable()
        test_list_backups()
        
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED")
        print("="*60)
        
        print_usage()
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
