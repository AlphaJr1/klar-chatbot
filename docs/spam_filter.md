# Spam/Profanity Filter

## Overview

Filter untuk mendeteksi dan menangani spam/profanity di awal conversation flow, mencegah bot stuck di fallback loop.

## Fitur

### 1. Profanity Detection

Mendeteksi kata-kata kasar dalam bahasa Indonesia dan Inggris:

- Indonesia: anjg, anjing, asu, babi, bangsat, kontol, memek, ngentot, jancok, tolol, goblok, tai, sial, kampret, cok, njing, njir, asw
- English: fuck, shit, bitch, damn, cunt, dick, pussy, ass

**Response:** Bot hanya reply dengan emoji 🙏

### 2. Spam Detection

Mendeteksi message yang tidak jelas/nonsense:

- Message <= 3 karakter tanpa huruf (contoh: "...", "!!!")
- Nonsense patterns: al, ohokkk, affh, tll, maksa, ga, gaa, gaaa
- Message <= 3 karakter alphabet yang bukan keyword valid (kecuali: eac, iya, ya, ok, oke)

**Response:** Bot reply dengan emoji 🙏

### 3. Spam Counter

- Setiap spam message, counter bertambah
- Setelah 3x spam, bot kasih helpful message: "Kak, kalau ada keluhan EAC bisa langsung ceritakan ya 😊"
- Counter reset ke 0 setelah user kirim message normal

## Implementasi

### Location

`src/convo/engine.py` - fungsi `handle()` line ~2012

### Flow

```
User Message
    ↓
Spam/Profanity Check
    ↓
├─ Profanity → Return 🙏
├─ Spam (count < 3) → Return 🙏
├─ Spam (count >= 3) → Return helpful message + reset counter
└─ Normal → Reset counter, lanjut normal flow
```

### Code

```python
def _check_spam_or_profanity(self, user_id: str, message: str) -> Dict[str, bool]:
    # Check profanity keywords
    # Check spam patterns
    # Return {"is_spam": bool, "is_profanity": bool}
```

## Testing

### Run Tests

```bash
python scripts/test_spam_filter.py
python scripts/test_real_spam_case.py
```

### Test Cases

- ✅ Profanity detection (anjg, cok, fuck, dll)
- ✅ Spam detection (al, ga, tll, dll)
- ✅ Spam counter (3x threshold)
- ✅ Counter reset after normal message
- ✅ Real case replay (user 6287784566051)

## Benefits

### Before

```
User: "Anjg"
Bot: "Maaf kak, boleh ceritakan keluhan alatnya secara singkat?"
User: "Al"
Bot: "Maaf kak, boleh ceritakan keluhan alatnya secara singkat?"
User: "Ga boleh"
Bot: "Maaf kak, boleh ceritakan keluhan alatnya secara singkat?"
```

❌ Stuck di fallback loop

### After

```
User: "Anjg"
Bot: "🙏"
User: "Al"
Bot: "🙏"
User: "Ga"
Bot: "Kak, kalau ada keluhan EAC bisa langsung ceritakan ya 😊"
User: "EAC saya mati"
Bot: "Kak, matikan dulu, pastikan covernya tertutup rapat..."
```

✅ Minimal response, tidak spam user dengan fallback message

## Notes

- Filter berjalan SEBELUM intent detection untuk efisiensi
- Tidak mempengaruhi normal conversation flow
- Counter disimpan di memstore per user
- Profanity langsung return tanpa increment counter
