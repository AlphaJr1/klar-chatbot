# Premature Resolution Fix

## Overview

Mencegah bot resolve ticket sebelum user explicitly confirm bahwa masalah sudah selesai.

## Problem

Dari chat log dan testing, bot sering premature resolve:

### Case 1: Ambiguous Answer

```
User: "EAC saya mati"
Bot: "Coba tekan LOW di remote"
User: "sudah dicoba semua"
Bot: "Sip kak, sudah dicek semuanya ya." (status: resolved)
```

❌ Bot resolve padahal user hanya bilang "sudah dicoba", bukan "sudah berfungsi"

### Case 2: Negative Confirmation

```
User: "Apakah sudah berfungsi?"
User: "Baik ka, saya sudah coba namun masih tetap tidak nyala"
Bot: Resolve (BUG!)
```

❌ Bot resolve padahal user bilang "masih tidak nyala"

## Root Causes

### 1. LLM/SOP Logic Premature Resolve

LLM atau SOP logic bisa decide action="resolve" terlalu cepat tanpa explicit confirmation dari user.

**Location:**

- `make_troubleshoot_decision_via_llm()` → action="resolve" (line ~1657)
- `handle_exploration()` → logic.get("resolve") (line ~1983)

### 2. Weak Answer Parsing

`_parse_user_answer()` parse "sudah dicoba semua" sebagai 'yes' karena ada kata "sudah", padahal ini ambiguous.

**Location:** `_parse_user_answer()` (line ~1147)

## Solution

### 1. Validation Before Resolve

Tambahkan check `_is_explicit_resolution()` sebelum resolve. Jika user message tidak contain explicit resolution pattern, bot confirm dulu:

```python
if action == "resolve":
    if not self._is_explicit_resolution(message):
        # Don't resolve yet, ask confirmation first
        confirm_msg = "Apakah alatnya sudah berfungsi normal kak?"
        self.memstore.set_flag(user_id, f"{active_step_id}_waiting_confirm", True)
        return {"bubbles": [{"text": confirm_msg}], "next": "await_reply"}

    # Only resolve if explicit confirmation
    resolve_msg = "Baik kak, saya tutup laporannya ya."
    self.memstore.set_flag(user_id, "sop_resolved", True)
    return {"bubbles": [{"text": resolve_msg}], "status": "resolved"}
```

**Applied to:**

- Line ~1657: LLM action="resolve" handler
- Line ~1983: SOP logic.resolve handler

### 2. Ambiguous Phrase Detection

Tambahkan check untuk ambiguous phrases yang tidak boleh di-parse sebagai 'yes':

```python
ambiguous_phrases = [
    'sudah dicoba', 'sudah coba', 'sudah saya coba',
    'sudah saya', 'sudah aku', 'sudah kucoba'
]
if any(phrase in msg_lower for phrase in ambiguous_phrases):
    return 'unclear'  # Don't parse as 'yes'
```

**Location:** `_parse_user_answer()` line ~1212

### 3. Explicit Resolution Patterns

Function `_is_explicit_resolution()` sudah bagus, dengan:

- ✅ Negative indicators check: "tidak", "belum", "masih", "gak", dll
- ✅ Resolution patterns: "sudah menyala", "sudah berfungsi", "kembali normal", dll

## Implementation

### Files Modified

1. `src/convo/engine.py` line ~1657: Add validation in LLM resolve handler
2. `src/convo/engine.py` line ~1983: Add validation in SOP logic resolve handler
3. `src/convo/engine.py` line ~1212: Add ambiguous phrase detection

### Code Changes

#### Change 1: LLM Resolve Handler

```python
if action == "resolve":
    if not self._is_explicit_resolution(message):
        short_log(self.logger, user_id, "prevent_premature_resolve",
                 f"LLM want resolve but no explicit confirmation from user")

        confirm_msg = "Apakah alatnya sudah berfungsi normal kak?"
        self.memstore.append_history(user_id, "bot", confirm_msg)

        if active_step_id:
            self.memstore.set_flag(user_id, f"{active_step_id}_waiting_confirm", True)
            self.memstore.set_flag(user_id, f"{active_step_id}_confirm_data", {
                "resolve_if_yes": True,
                "pending_if_no": True
            })

        return {"bubbles": [{"text": confirm_msg}], "next": "await_reply"}

    # Continue with normal resolve...
```

#### Change 2: SOP Logic Resolve Handler

```python
if logic.get("resolve"):
    if not self._is_explicit_resolution(message):
        # Same validation as above
        confirm_msg = "Apakah alatnya sudah berfungsi normal kak?"
        # Set waiting_confirm flag
        return {"bubbles": [{"text": confirm_msg}], "next": "await_reply"}

    # Continue with normal resolve...
```

#### Change 3: Ambiguous Phrase Detection

```python
if 'yes' in expected_result or 'no' in expected_result:
    ambiguous_phrases = [
        'sudah dicoba', 'sudah coba', 'sudah saya coba', 'sudah di coba',
        'sudah saya', 'sudah aku', 'sudah kucoba', 'sudah ku coba'
    ]
    if any(phrase in msg_lower for phrase in ambiguous_phrases):
        return 'unclear'

    # Continue with normal yes/no parsing...
```

## Testing

### Run Tests

```bash
python scripts/test_premature_resolution.py
```

### Test Results

```
Test Case 1: 'sudah dicoba semua' should NOT resolve
✅ CORRECT: Not resolved, asking for clarification

Test Case 2: Explicit resolution should work
✅ CORRECT: Resolved after explicit confirmation

Test Case 3: 'masih tidak nyala' should NOT resolve
✅ CORRECT: Not resolved when user says 'masih tidak nyala'
```

## Benefits

### Before

```
User: "sudah dicoba semua"
Bot: "Sip kak, sudah dicek semuanya ya." (status: resolved)
```

❌ Premature resolve - user belum confirm masalah selesai

### After

```
User: "sudah dicoba semua"
Bot: "Apakah alatnya sudah berfungsi normal kak?"
User: "iya sudah menyala"
Bot: "Baik kak, saya tutup laporannya ya." (status: resolved)
```

✅ Confirm dulu sebelum resolve

## Edge Cases

### 1. Explicit Resolution Still Works

```
User: "alat sudah menyala kembali kak"
Bot: "Baik kak, saya tutup laporannya ya." (status: resolved)
```

✅ Langsung resolve jika user explicit confirm

### 2. Negative Confirmation Detected

```
User: "sudah saya coba namun masih tetap tidak nyala"
Bot: (Continue troubleshooting, NOT resolve)
```

✅ Tidak resolve jika ada negative indicators

### 3. Ambiguous Phrases Handled

```
User: "sudah dicoba", "sudah saya coba", "sudah aku coba"
Bot: "Boleh dijelaskan sedikit lagi kak?"
```

✅ Minta clarification untuk ambiguous phrases

## Notes

- Validation berjalan di 2 tempat: LLM decision handler & SOP logic handler
- `_is_explicit_resolution()` adalah single source of truth untuk detect resolution
- Ambiguous phrases di-detect SEBELUM yes/no parsing untuk avoid false positive
- Confirmation message: "Apakah alatnya sudah berfungsi normal kak?"
