# Conversation Reset Feature

## Masalah

Berdasarkan analisis chat log dari `6282216860317` dan `6287784566051`, ditemukan masalah:

1. **User say "Halo" saat pending** → System tidak detect sebagai new session
2. **User kirim message saat pending** → System tidak bisa bedakan:
   - Follow-up question (e.g., "Kapan teknisi datang?")
   - New complaint (e.g., "Sekarang ada bau juga")
   - New session (e.g., "Halo, mau nanya lagi")

**Contoh dari chat log**:

```
User: "EAC bunyi terus" → pending
Bot: "Baik Kak, boleh tahu namanya?"
User: "Halo"
Bot: (masih lanjut data collection, tidak reset) ❌
```

## Solusi

Menambahkan **intelligent conversation reset** dengan LLM-based detection:

### 1. Fungsi `_detect_new_session_or_followup()`

Analyze message saat pending dan kategorikan:

**a) "new_session"** - User memulai conversation baru

- Hanya greeting tanpa keluhan: "Halo", "Siang"
- Greeting + pertanyaan umum: "Halo, cara order gimana?"
- **Action**: Reset pending state, clear active_intent

**b) "follow_up"** - Follow-up terkait masalah yang sama

- Tanya progress: "Kapan teknisi datang?"
- Konfirmasi: "Oke siap", "Baik terima kasih"
- **Action**: Continue data collection

**c) "new_complaint"** - Komplain masalah baru

- Mention masalah berbeda: "Sekarang ada bau juga"
- **Action**: Queue complaint, continue current data collection

### 2. Integrasi di Handle Function

File: `src/convo/engine.py` (Line 2546-2607)

```python
if sop_pending_flag:
    # Detect new session vs follow-up
    session_detection = self._detect_new_session_or_followup(
        user_id, msg, active_intent, sop_pending_flag
    )
    session_type = session_detection.get("type", "follow_up")

    # Handle new session - reset state
    if session_type == "new_session":
        # Clear pending state
        self.memstore.clear_flag(user_id, "sop_pending")
        self.memstore.clear_flag(user_id, "active_intent")

        # Reply greeting
        if has_greeting:
            greeting_reply = self.handle_greeting(...)
            return greeting_reply

    # Handle new complaint - queue it
    if session_type == "new_complaint":
        ack_msg = "Keluhan baru akan kami catat..."
        self._queue_additional_complaint(user_id, sop_intent)
        return ack_msg

    # Follow-up - continue data collection
    # ... existing logic
```

## Flow Examples

### Example 1: New Session

```
1. User: "EAC bunyi terus kak"
2. Bot: "Kak, bunyinya sering atau jarang?"
3. User: "Sering"
4. Bot: "Sepertinya perlu dibersihkan. Boleh jadwalkan teknisi?" (pending)
5. Bot: "Baik Kak, boleh tahu namanya?"
6. User: "Halo" (new session detected)
7. Bot: "Halo Kak!" (pending state reset) ✅
```

### Example 2: Follow-Up

```
1. User: "EAC bunyi terus kak"
2. Bot: (trigger pending)
3. Bot: "Baik Kak, boleh tahu namanya?"
4. User: "Kapan teknisi datang?" (follow-up detected)
5. Bot: "Pertanyaan akan saya jawab setelah data lengkap..." ✅
```

### Example 3: New Complaint

```
1. User: "EAC bunyi terus kak"
2. Bot: (trigger pending)
3. Bot: "Baik Kak, boleh tahu namanya?"
4. User: "Sekarang ada bau juga nih" (new complaint detected)
5. Bot: "Keluhan baru akan kami catat..." (queued) ✅
```

## Test Results

Run: `python tests/test_conversation_reset.py`

**Hasil**: ✅ **All tests passed**

Test cases:

- ✅ Pending state direset saat new session (user say "Halo")
- ✅ Pending state tetap saat follow-up question
- ✅ Active intent cleared saat new session
- ✅ Greeting reply properly saat new session

## Impact

**Before**:

```
User: "Halo" (saat pending)
Bot: "Maaf Kak, boleh diulang namanya?" (tidak detect new session) ❌
```

**After**:

```
User: "Halo" (saat pending)
Bot: "Halo Kak!" (detect new session, reset state) ✅
Pending: None
Active intent: None
```

## Benefits

1. ✅ **Better UX** - User bisa mulai conversation baru kapan saja
2. ✅ **Intelligent detection** - System bisa bedakan:
   - New session → Reset
   - Follow-up → Continue
   - New complaint → Queue
3. ✅ **Preserve data** - History tetap tersimpan meskipun reset
4. ✅ **Natural flow** - User tidak stuck di pending state

## Files Modified

1. `src/convo/engine.py`:
   - Line 334-394: Add `_detect_new_session_or_followup()`
   - Line 2546-2607: Add conversation reset logic
2. `tests/test_conversation_reset.py` - Test suite
3. `docs/CONVERSATION_RESET.md` - Documentation
