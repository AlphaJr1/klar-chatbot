# Update: Deteksi Nama Perusahaan (LLM-based)

## Problem

1. Bot memanggil "kak {nama PT}" untuk nama perusahaan
2. Nama perusahaan tidak selalu punya inisiator PT/CV/UD (misal: "Sejahtera Abadi", "Toko Berkah")

## Solution

Gunakan LLM untuk deteksi cerdas berdasarkan pola nama, bukan hanya keyword.

## Changes

### 1. `data_collector.py` - Deteksi Berbasis LLM

**Sebelum:**

- Deteksi keyword sederhana: `pt`, `cv`, `ud`
- Tidak bisa deteksi "Sejahtera Abadi" sebagai perusahaan

**Setelah:**

```python
Kriteria PERUSAHAAN (is_company: true):
- Ada inisiator: PT, CV, UD, Yayasan, Toko, Koperasi
- Nama berbentuk institusi: "Sejahtera Jaya", "Maju Bersama"
- Pola nama bisnis: Jaya, Sejahtera, Mandiri, Abadi, Sentosa, Makmur, Karya
- Nama terlalu formal/tidak lazim untuk personal

Kriteria PERSONAL (is_company: false):
- Nama orang Indonesia: Budi, Ahmad, Siti, Dewi
- Pola: [Nama Depan] [Nama Belakang]
```

### 2. `api.py` - Dev Mode untuk Testing

**Command baru:**

```
/dev pending dev_reset_2024
```

Langsung trigger mode data collection tanpa harus melalui flow troubleshooting.

## Test Results

### Deteksi Nama Perusahaan

```
✅ "Sejahtera Abadi" → is_company: true (tanpa PT/CV/UD!)
✅ "Toko Makmur Jaya" → is_company: true
✅ "PT Karya Mandiri" → is_company: true
✅ "Siti Nurhaliza" → is_company: false, gender: female
```

### Sapaan Bot

```
Perusahaan:
  "Data Sejahtera Abadi sudah kami terima..." ✅
  "Data Toko Makmur Jaya sudah kami terima..." ✅

Personal:
  "Data Bu Siti sudah kami terima..." ✅
  "Data Pak Budi sudah kami terima..." ✅
```

## Dev Testing

### Cara Test

```bash
python tests/test_final_company.py
```

### Manual Test via API

```bash
# 1. Trigger pending mode
curl -X POST http://localhost:8080/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test123", "text": "/dev pending dev_reset_2024"}'

# 2. Input nama perusahaan
curl -X POST http://localhost:8080/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test123", "text": "Sejahtera Abadi"}'

# 3. Input produk
curl -X POST http://localhost:8080/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test123", "text": "F57A"}'

# 4. Input alamat
curl -X POST http://localhost:8080/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test123", "text": "Jl. Sudirman No. 123, Jakarta Selatan"}'
```

## Files Modified

- `src/convo/data_collector.py` - LLM-based company detection
- `src/convo/memory_store.py` - Field `is_company`
- `src/convo/engine.py` - Sapaan berdasarkan `is_company`
- `src/api.py` - Dev command `/dev pending`
- `tests/test_final_company.py` - Test script

## Keuntungan

1. ✅ Deteksi lebih pintar tanpa heuristik rumit
2. ✅ Bisa deteksi nama perusahaan tanpa PT/CV/UD
3. ✅ Testing lebih mudah dengan dev mode
4. ✅ Hemat token dengan test script (tidak perlu manual chat)
