# Clarification Loop Limiter

## Overview

Membatasi jumlah clarification yang bot bisa minta untuk intent yang sama. Setelah 3x clarification, bot auto-escalate ke pending (jadwalkan teknisi).

## Problem

Dari chat log user 6282216860317 (lines 116-122):

```
User: "Iya, cukup mengganggu"
Bot: "Boleh dijelaskan sedikit lagi kak supaya saya bisa bantu lebih tepat?"
User: "Waktu dinyalakan suka ada bunyi kretek kretek gitu"
Bot: "Bisa dijelaskan sedikit lagi kak, biar saya cekkan kondisinya."
User: "Yaaa gitu, dinyalakan sebentar langsung ada bunyi2 nya"
Bot: "Boleh dijelaskan sedikit lagi kak supaya saya bisa bantu lebih tepat?"
User: "Bunyi kretek kretek"
Bot: "Boleh dijelaskan sedikit lagi kak supaya saya bisa bantu lebih tepat?"
```

❌ **Bot stuck di clarification loop tanpa batas**

## Solution

### 1. Clarification Counter

Track berapa kali bot minta clarification untuk setiap intent:

- Counter disimpan di `memstore` dengan key `{intent}_clarify_count`
- Increment setiap kali bot minta clarification
- Reset ke 0 saat user kasih jawaban yang jelas

### 2. Auto-Escalation

Setelah 3x clarification:

- Bot auto-escalate ke pending
- Trigger data collection untuk jadwalkan teknisi
- Counter di-reset ke 0

### 3. Counter Preservation

- Counter di-preserve saat `is_new_issue` tapi intent sama
- Counter di-reset hanya saat intent benar-benar berubah
- Counter di-reset saat user kasih jawaban jelas (bukan unclear)

## Implementation

### Locations

1. `src/convo/engine.py` - Line ~1551: Action "clarify" handler
2. `src/convo/engine.py` - Line ~1900: User answer "unclear" handler
3. `src/convo/engine.py` - Line ~1925: Reset counter saat answer jelas
4. `src/convo/engine.py` - Line ~764: Clear counter di reset_troubleshoot_state
5. `src/convo/engine.py` - Line ~1771: Preserve counter saat is_new_issue

### Code Flow

```python
# 1. Increment counter saat clarify
if action == "clarify":
    clarify_count = self.memstore.get_flag(user_id, f"{intent}_clarify_count") or 0
    clarify_count += 1
    self.memstore.set_flag(user_id, f"{intent}_clarify_count", clarify_count)

    # 2. Auto-escalate setelah 3x
    if clarify_count >= 3:
        self.memstore.set_flag(user_id, f"{intent}_clarify_count", 0)
        escalate_msg = "Baik kak, sepertinya perlu pengecekan lebih detail oleh teknisi kami..."
        self.memstore.set_flag(user_id, "sop_pending", True)
        return {"bubbles": [{"text": escalate_msg}], "status": "open"}

    # 3. Return clarification message
    clarify_msg = "Boleh dijelaskan sedikit lagi kak?"
    return {"bubbles": [{"text": clarify_msg}]}

# 4. Reset counter saat answer jelas
if user_answer != 'unclear':
    self.memstore.set_flag(user_id, f"{intent}_clarify_count", 0)
```

## Testing

### Run Tests

```bash
python scripts/test_clarify_simple.py
```

### Expected Output

```
Test 1: EAC berbunyi
Bot: Kak, bunyinya muncul sesekali atau sering?

Test 2: bunyi aneh (unclear #1)
Bot: Bisa dijelaskan sedikit lagi kak...
Count: 1, Status: unknown

Test 3: bunyi aneh (unclear #2)
Bot: Saya kurang menangkap maksudnya kak...
Count: 2, Status: unknown

Test 4: bunyi aneh (unclear #3)
Bot: Baik kak, sepertinya perlu pengecekan lebih detail oleh teknisi kami...
Count: 0, Status: open
✅ ESCALATED!
```

## Benefits

### Before

```
User: "bunyi aneh"
Bot: "Boleh dijelaskan sedikit lagi kak?"
User: "bunyi aneh gitu"
Bot: "Boleh dijelaskan sedikit lagi kak?"
User: "bunyi kretek"
Bot: "Boleh dijelaskan sedikit lagi kak?"
User: "bunyi kretek kretek"
Bot: "Boleh dijelaskan sedikit lagi kak?"
```

❌ Loop tanpa batas, user frustasi

### After

```
User: "bunyi aneh"
Bot: "Boleh dijelaskan sedikit lagi kak?"
User: "bunyi aneh gitu"
Bot: "Bisa dijelaskan sedikit lagi kak?"
User: "bunyi kretek"
Bot: "Baik kak, sepertinya perlu pengecekan lebih detail oleh teknisi kami. Boleh saya bantu jadwalkan kunjungan teknisi?"
```

✅ Auto-escalate setelah 3x, langsung solusi

## Edge Cases

### 1. Clear Answer Resets Counter

```
Unclear #1 → count=1
Unclear #2 → count=2
Clear answer (e.g., "sering kak") → count=0
Unclear #3 → count=1 (start over)
```

### 2. Intent Change Resets Counter

```
Intent "bunyi" → count=2
Intent change to "mati" → count=0 for "mati"
Back to "bunyi" → count=0 (reset)
```

### 3. Preserve Counter for Same Intent

```
Intent "bunyi" → count=2
is_new_issue=true but intent still "bunyi" → count=2 (preserved)
```

## Notes

- Threshold: 3 clarifications (configurable)
- Escalation message: "Baik kak, sepertinya perlu pengecekan lebih detail oleh teknisi kami..."
- Counter per intent (bunyi_clarify_count, mati_clarify_count, dll)
- Auto-trigger pending flow setelah escalation
