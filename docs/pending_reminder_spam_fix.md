# Pending State Reminder Spam Fix

## Overview

Mencegah bot spam reminder message saat pending state sudah complete dan user hanya kirim simple acknowledgment atau emoji.

## Problem

Dari chat log user 6287784566051 (lines 223, 237, 354):

```
Line 223: User: "Baik kak"
          Bot: "Baik Kak, boleh tahu kemarin pembeliannya atas nama siapa?"

Line 237: User: "👍"
          Bot: "Baik Kak, boleh tahu kemarin pembeliannya atas nama siapa?"

Line 354: User: "🙏"
          Bot: "Baik Kak, boleh tahu kemarin pembeliannya atas nama siapa?"
```

❌ **Bot terus-menerus repeat pending reminder meskipun user hanya kirim acknowledgment/emoji**

## Root Cause

Setiap kali user kirim message (termasuk simple ack atau emoji), bot check `sop_pending` dan `is_complete`, lalu kirim closing message lagi. Tidak ada tracking apakah closing message sudah pernah dikirim.

## Solution

### 1. Tracking Flag

Tambahkan flag `pending_closing_sent` untuk track apakah closing message sudah dikirim:

```python
if is_complete:
    pending_closing_sent = self.memstore.get_flag(user_id, "pending_closing_sent")

    if pending_closing_sent:
        # Closing already sent, check if simple ack
        ...

    # First time - send closing message
    closing_msg = f"Data {name} sudah kami terima..."
    self.memstore.set_flag(user_id, "pending_closing_sent", True)
    return closing_msg
```

### 2. Simple Acknowledgment Detection

Jika closing sudah dikirim dan user kirim simple ack, respond minimal:

```python
if pending_closing_sent:
    simple_ack = self._is_simple_acknowledge(msg)

    common_acks = [
        'baik kak', 'baik ka', 'oke kak', 'ok kak', 'siap kak',
        'terima kasih', 'makasih', 'thanks', 'thank you',
        'sip kak', 'iya kak', 'ya kak'
    ]
    is_common_ack = any(ack in msg.lower() for ack in common_acks)

    if simple_ack or is_common_ack or len(msg) <= 3:
        ack_responses = ["🙏", "Siap kak 👍", "Terima kasih kak 😊"]
        return random.choice(ack_responses)
```

### 3. Common Acknowledgment Patterns

Tambahkan check untuk common patterns yang sering digunakan user:

- "baik kak", "baik ka"
- "oke kak", "ok kak", "siap kak"
- "terima kasih", "makasih", "thanks"
- "sip kak", "iya kak", "ya kak"
- Emoji atau message <= 3 karakter

## Implementation

### Location

`src/convo/engine.py` line ~2267-2295

### Code Changes

```python
if sop_pending_flag:
    collection_state = self.data_collector.get_collection_state(user_id)
    is_complete = collection_state.get("is_complete", False)

    if is_complete:
        pending_closing_sent = self.memstore.get_flag(user_id, "pending_closing_sent")

        # If closing already sent, check for simple ack
        if pending_closing_sent:
            simple_ack = self._is_simple_acknowledge(msg)

            common_acks = [
                'baik kak', 'baik ka', 'oke kak', 'ok kak', 'siap kak',
                'terima kasih', 'makasih', 'thanks', 'thank you',
                'sip kak', 'iya kak', 'ya kak'
            ]
            is_common_ack = any(ack in msg.lower() for ack in common_acks)

            if simple_ack or is_common_ack or len(msg) <= 3:
                short_log(self.logger, user_id, "pending_complete_ack",
                         f"Simple ack after pending complete, minimal response")

                ack_responses = ["🙏", "Siap kak 👍", "Terima kasih kak 😊"]
                ack_msg = random.choice(ack_responses)
                self.memstore.append_history(user_id, "bot", ack_msg)
                return {"bubbles": [{"text": ack_msg}], "next": "end", "status": "pending"}

        # First time - send closing message
        closing_msg = f"Data {greeting_name} sudah kami terima. Teknisi kami akan segera menghubungi untuk konfirmasi jadwal kunjungan."
        self.memstore.append_history(user_id, "bot", closing_msg)
        self.memstore.set_flag(user_id, "pending_closing_sent", True)

        return {"bubbles": [{"text": closing_msg}], "next": "end", "status": "pending"}
```

## Testing

### Run Test

```bash
python scripts/test_pending_fresh.py
```

### Test Results

```
1. First message after pending complete (should send closing)
   Bot: 'Data Pak Budi sudah kami terima. Teknisi kami akan segera menghubungi...'
   ✅ Closing message sent
   ✅ Flag set correctly

2. User sends 'Baik kak' (should be minimal)
   Bot: 'Siap kak 👍'
   ✅ CORRECT: Minimal response, no spam

3. User sends '👍'
   Bot: '🙏'
   ✅ CORRECT: Minimal response

4. User sends '🙏'
   Bot: '🙏'
   ✅ CORRECT: Minimal response
```

## Benefits

### Before

```
User: "Baik kak"
Bot: "Baik Kak, boleh tahu kemarin pembeliannya atas nama siapa?"
User: "👍"
Bot: "Baik Kak, boleh tahu kemarin pembeliannya atas nama siapa?"
User: "🙏"
Bot: "Baik Kak, boleh tahu kemarin pembeliannya atas nama siapa?"
```

❌ **Spam reminder - user frustasi**

### After

```
User: (Data collection complete)
Bot: "Data Pak Budi sudah kami terima. Teknisi kami akan segera menghubungi..."
User: "Baik kak"
Bot: "Siap kak 👍"
User: "👍"
Bot: "🙏"
User: "🙏"
Bot: "🙏"
```

✅ **Minimal response - tidak spam**

## Edge Cases

### 1. First Message After Complete

```
Data complete → User: "ok"
Bot: "Data Pak Budi sudah kami terima..." (closing message)
pending_closing_sent = True
```

✅ Closing message dikirim pertama kali

### 2. Subsequent Simple Acknowledgments

```
pending_closing_sent = True → User: "Baik kak"
Bot: "Siap kak 👍" (minimal)
```

✅ Tidak repeat closing message

### 3. Common Patterns Detected

```
"baik kak", "terima kasih", "ok kak", "👍", "🙏"
→ All return minimal response
```

✅ Semua pattern di-handle

### 4. Emoji and Short Messages

```
len(msg) <= 3 → "ok", "ya", "👍", "🙏"
→ Minimal response
```

✅ Short messages tidak trigger reminder

## Notes

- Flag `pending_closing_sent` di-set setelah closing message pertama kali dikirim
- Common acknowledgment patterns include: "baik kak", "terima kasih", "ok kak", dll
- Minimal responses: "🙏", "Siap kak 👍", "Terima kasih kak 😊"
- Check berjalan HANYA jika `sop_pending=True` dan `is_complete=True`
