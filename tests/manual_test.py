#!/usr/bin/env python3
"""Manual test helper untuk debugging chat flow"""
import requests
import json
import sys

BASE_URL = "http://localhost:8081"

def reset_user(user_id: str):
    """Reset memory user"""
    try:
        resp = requests.post(
            f"{BASE_URL}/admin/reset-memory",
            params={"user_id": user_id, "secret": "dev_reset_2024"},
            timeout=5
        )
        resp.raise_for_status()
        print(f"✓ Memory reset untuk {user_id}\n")
    except Exception as e:
        print(f"✗ Reset failed: {e}\n")

def send_chat(user_id: str, text: str):
    """Kirim chat dan tampilkan response"""
    print(f"👤 USER: {text}")
    
    try:
        resp = requests.post(
            f"{BASE_URL}/chat",
            json={"user_id": user_id, "text": text},
            timeout=30
        )
        resp.raise_for_status()
        result = resp.json()
        
        # Extract response text
        bubbles = result.get("bubbles", [])
        for i, bubble in enumerate(bubbles, 1):
            text = bubble.get("text", "")
            print(f"🤖 BOT [{i}]: {text}")
        
        # Show metadata
        status = result.get("status", "unknown")
        next_action = result.get("next", "unknown")
        print(f"📊 Status: {status} | Next: {next_action}")
        print("-" * 70)
        
        return result
        
    except Exception as e:
        print(f"✗ Error: {e}")
        return {}

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 manual_test.py <user_id> [message]")
        print("Example: python3 manual_test.py test_001 'EAC saya mati'")
        sys.exit(1)
    
    user_id = sys.argv[1]
    
    if len(sys.argv) == 2:
        # Interactive mode
        print(f"=== Interactive Test Mode ===")
        print(f"User ID: {user_id}")
        print(f"Commands: /reset, /quit")
        print("=" * 70 + "\n")
        
        while True:
            try:
                msg = input("👤 YOU: ").strip()
                if not msg:
                    continue
                if msg == "/quit":
                    break
                if msg == "/reset":
                    reset_user(user_id)
                    continue
                
                send_chat(user_id, msg)
                print()
                
            except KeyboardInterrupt:
                print("\n\nBye!")
                break
    else:
        # Single message mode
        message = " ".join(sys.argv[2:])
        send_chat(user_id, message)
