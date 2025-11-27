# Intent Detection Improvement

## Overview

Meningkatkan kemampuan bot untuk detect intent dari berbagai variasi keluhan, termasuk produk selain EAC (seperti water heater).

## Problem

Dari chat log user 6282216860317 (lines 227-228):

```
Line 227: User: "water heater ku tidak panas"
Line 228: Bot: "Maaf kak, saya belum menangkap keluhan spesifiknya."
```

❌ **Bot gagal detect intent untuk "water heater" karena prompt terlalu fokus ke "EAC"**

## Root Causes

### 1. Product-Specific Prompt

Prompt LLM terlalu fokus ke "EAC" dan tidak recognize produk lain:

- Hanya mention "EAC" di contoh
- Tidak ada mapping untuk produk lain

### 2. Limited Symptom Mapping

Tidak ada mapping untuk symptoms yang specific ke produk tertentu:

- "tidak panas" (water heater) tidak di-map ke intent "mati"
- Hanya ada mapping untuk EAC symptoms

## Solution

### 1. Add Product Recognition

Tambahkan list produk Honeywell di prompt:

```
PRODUK HONEYWELL:
- EAC (Electronic Air Cleaner) / Air Purifier / Pembersih Udara
- Water Heater / Pemanas Air
- Produk lainnya
```

### 2. Expand Symptom Mapping

Tambahkan mapping symptoms yang lebih comprehensive:

```
MAPPING KELUHAN KE INTENT:

Intent "mati":
- Tidak menyala, tidak hidup, mati total, padam, off, tidak berfungsi
- Tidak panas (untuk water heater)  ← NEW!
- Tidak ada respon sama sekali

Intent "bau":
- Bau tidak sedap, bau aneh, bau menyengat
- Aroma tidak enak

Intent "bunyi":
- Bunyi aneh, berisik, suara berisik
- Bunyi kretek-kretek, bunyi berdengung
- Noise, berisik
```

### 3. Generic Examples

Update contoh untuk tidak terlalu specific ke "EAC":

**Before:**

```
- Jika JELAS menyebut masalah bau EAC → additional_complaint="bau"
  Contoh: "EAC juga bau", "bau menyengat dari EAC"
```

**After:**

```
- Jika JELAS menyebut masalah bau → additional_complaint="bau"
  Contoh: "juga bau", "bau menyengat", "ada bau aneh"
```

## Implementation

### Location

`src/convo/engine.py` - `detect_intent_via_llm()` line ~155-195

### Code Changes

```python
prompt = f"""
    ...

    PRODUK HONEYWELL:
    - EAC (Electronic Air Cleaner) / Air Purifier / Pembersih Udara
    - Water Heater / Pemanas Air
    - Produk lainnya

    MAPPING KELUHAN KE INTENT:

    Intent "mati":
    - Tidak menyala, tidak hidup, mati total, padam, off, tidak berfungsi
    - Tidak panas (untuk water heater)
    - Tidak ada respon sama sekali

    Intent "bau":
    - Bau tidak sedap, bau aneh, bau menyengat
    - Aroma tidak enak

    Intent "bunyi":
    - Bunyi aneh, berisik, suara berisik
    - Bunyi kretek-kretek, bunyi berdengung
    - Noise, berisik

    ...
"""
```

## Testing

### Run Test

```bash
python scripts/test_intent_detection.py
```

### Test Results

```
✅ 'Standard EAC mati' - Detected: mati
✅ 'EAC tidak menyala' - Detected: mati
✅ 'EAC bunyi' - Detected: bunyi
✅ 'EAC bau' - Detected: bau
✅ 'Water heater tidak panas' - Detected: mati
✅ 'Pemanas air tidak panas' - Detected: mati
✅ 'Water heater mati' - Detected: mati
✅ 'Tidak hidup' - Detected: mati
✅ 'Bunyi kretek' - Detected: bunyi
✅ 'Bau menyengat' - Detected: bau

RESULTS: 10 passed, 0 failed
🎉 All tests passed!
```

## Benefits

### Before

```
User: "water heater ku tidak panas"
Bot: "Maaf kak, saya belum menangkap keluhan spesifiknya."
```

❌ **Gagal detect intent**

### After

```
User: "water heater ku tidak panas"
Bot: "Kak, cek covernya ya. Kalau belum tertutup rapat..."
(Masuk ke troubleshooting flow "mati")
```

✅ **Intent detected correctly**

## Coverage

### Product Recognition

- ✅ EAC / Electronic Air Cleaner / Air Purifier
- ✅ Water Heater / Pemanas Air
- ✅ Generic "alat" / "unit"

### Symptom Mapping

#### Intent "mati"

- ✅ Tidak menyala, tidak hidup, mati total
- ✅ Tidak panas (water heater specific)
- ✅ Padam, off, tidak berfungsi

#### Intent "bau"

- ✅ Bau tidak sedap, bau aneh
- ✅ Bau menyengat, aroma tidak enak

#### Intent "bunyi"

- ✅ Bunyi aneh, berisik, suara berisik
- ✅ Bunyi kretek-kretek, berdengung
- ✅ Noise

## Limitations

### SOP Coverage

Current SOP (`sop.json`) hanya cover 3 intents:

- "mati" - untuk masalah tidak menyala/tidak panas
- "bau" - untuk masalah bau
- "bunyi" - untuk masalah bunyi

Untuk produk-specific issues yang tidak fit ke 3 intent ini, bot akan fallback ke natural response.

### Future Improvements

1. **Expand SOP**: Tambah intent specific untuk water heater (e.g., "bocor", "suhu tidak stabil")
2. **Product-Specific Flows**: Buat SOP terpisah untuk setiap produk
3. **Multi-Product Support**: Support multiple products dalam satu conversation

## Notes

- Improvement ini fokus pada **better prompt engineering** untuk existing SOP
- Tidak memerlukan perubahan di SOP structure
- LLM sekarang lebih robust untuk product variations
- Symptom mapping lebih comprehensive
- Fallback response tetap natural dan helpful
