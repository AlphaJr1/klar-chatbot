#!/usr/bin/env python3

import os
import json
import sys
from datetime import datetime, timezone
from typing import Optional

def get_log_path(date: Optional[str] = None) -> str:
    if date is None:
        date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, "data", "storage", "logs", f"chat-{date}.jsonl")

def format_timestamp(ts: str) -> str:
    try:
        dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
        return dt.strftime("%H:%M:%S")
    except:
        return ts

def print_log_entry(log: dict, verbose: bool = False, prev_log: dict = None):
    ts = format_timestamp(log.get("ts", ""))
    direction = log.get("direction")
    user_id = log.get("user_id", "")[-4:]  # Last 4 digits
    
    # Add separator if switching from outgoing to incoming
    if prev_log and prev_log.get("direction") == "outgoing" and direction == "incoming":
        print()
    
    if direction == "incoming":
        message = log.get("message", "")
        meta = log.get("metadata", {})
        active_intent = meta.get("active_intent", "none")
        sop_pending = "✓" if meta.get("sop_pending") else " "
        
        print(f"[{ts}] 👤 User {user_id}: {message}")
        if verbose:
            print(f"         Intent: {active_intent} | Pending: [{sop_pending}]")
    
    elif direction == "outgoing":
        response = log.get("response", "")
        status = log.get("status", "unknown")
        meta = log.get("metadata", {})
        context = meta.get("context", "")
        
        # Truncate long responses
        if len(response) > 100 and not verbose:
            response = response[:97] + "..."
        
        print(f"[{ts}] 🤖 Bot:  {response}")
        if verbose:
            print(f"         Status: {status} | Context: {context}")
            if meta.get("data_collection_complete"):
                print(f"         ✓ Data collection complete")
            elif meta.get("next_field_needed"):
                print(f"         Next field: {meta['next_field_needed']}")

def view_logs(date: Optional[str] = None, user_id: Optional[str] = None, 
              direction: Optional[str] = None, verbose: bool = False,
              status: Optional[str] = None, context: Optional[str] = None):
    
    log_path = get_log_path(date)
    
    if not os.path.exists(log_path):
        print(f"❌ Log file not found: {log_path}")
        return
    
    print(f"📋 Reading: {log_path}")
    print("=" * 80)
    
    count = 0
    prev_log = None
    with open(log_path, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                log = json.loads(line)
                
                # Apply filters
                if user_id and not log.get("user_id", "").endswith(user_id):
                    continue
                
                if direction and log.get("direction") != direction:
                    continue
                
                if status and log.get("status") != status:
                    continue
                
                if context:
                    log_context = log.get("metadata", {}).get("context", "")
                    if context not in log_context:
                        continue
                
                print_log_entry(log, verbose, prev_log)
                prev_log = log
                count += 1
                
            except json.JSONDecodeError:
                continue
    
    print("=" * 80)
    print(f"Total entries: {count}")

def show_stats(date: Optional[str] = None):
    log_path = get_log_path(date)
    
    if not os.path.exists(log_path):
        print(f"❌ Log file not found: {log_path}")
        return
    
    stats = {
        "incoming": 0,
        "outgoing": 0,
        "users": set(),
        "statuses": {},
        "contexts": {},
        "intents": {}
    }
    
    with open(log_path, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                log = json.loads(line)
                direction = log.get("direction")
                
                if direction == "incoming":
                    stats["incoming"] += 1
                    stats["users"].add(log.get("user_id"))
                    meta = log.get("metadata", {})
                    intent = meta.get("active_intent", "none")
                    stats["intents"][intent] = stats["intents"].get(intent, 0) + 1
                
                elif direction == "outgoing":
                    stats["outgoing"] += 1
                    status = log.get("status", "unknown")
                    stats["statuses"][status] = stats["statuses"].get(status, 0) + 1
                    
                    context = log.get("metadata", {}).get("context", "unknown")
                    stats["contexts"][context] = stats["contexts"].get(context, 0) + 1
                    
            except json.JSONDecodeError:
                continue
    
    print(f"📊 Statistics for {date or 'today'}")
    print("=" * 80)
    print(f"Total Messages:")
    print(f"  Incoming: {stats['incoming']}")
    print(f"  Outgoing: {stats['outgoing']}")
    print(f"  Unique Users: {len(stats['users'])}")
    print()
    print("Status Distribution:")
    for status, count in sorted(stats["statuses"].items(), key=lambda x: -x[1]):
        print(f"  {status}: {count}")
    print()
    print("Intent Distribution:")
    for intent, count in sorted(stats["intents"].items(), key=lambda x: -x[1]):
        print(f"  {intent}: {count}")
    print()
    print("Top Contexts:")
    for context, count in sorted(stats["contexts"].items(), key=lambda x: -x[1])[:10]:
        print(f"  {context}: {count}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Chat Log Viewer")
    parser.add_argument("--date", help="Date (YYYY-MM-DD), default: today")
    parser.add_argument("--user", help="Filter by user ID (last 4 digits)")
    parser.add_argument("--direction", choices=["incoming", "outgoing"], help="Filter by direction")
    parser.add_argument("--status", help="Filter by status (open/pending/resolved)")
    parser.add_argument("--context", help="Filter by context")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed metadata")
    parser.add_argument("--stats", action="store_true", help="Show statistics instead of logs")
    
    args = parser.parse_args()
    
    if args.stats:
        show_stats(args.date)
    else:
        view_logs(
            date=args.date,
            user_id=args.user,
            direction=args.direction,
            verbose=args.verbose,
            status=args.status,
            context=args.context
        )
