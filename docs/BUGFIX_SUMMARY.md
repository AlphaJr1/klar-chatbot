# Summary: Perbaikan Natural Response

## Masalah yang Diperbaiki

### 1. ❌ Respons Terlalu Informal/Aneh (FIXED ✅)

**Masalah:**

- "teruskan dong..."
- "buat nyambung aja..."
- "di cek bersama..."

**Penyebab:**

- LLM terlalu creative dalam naturalisasi
- Tidak ada guideline yang cukup ketat
- Bahasa gaul dan informal tidak dilarang eksplisit

**Solusi:**

- Update prompt dengan aturan lebih ketat
- Tambah contoh konkret BENAR vs SALAH
- Larang eksplisit bahasa gaul: "dong", "aja", "gitu", "sih", "gimana", "ngga"

### 2. ❌ Bahasa Asing Muncul di Response (FIXED ✅)

**Masalah:**

- Kadang LLM menghasilkan teks dengan bahasa Mandarin/asing

**Solusi:**

- Tambah safety check untuk detect karakter CJK (Chinese, Japanese, Korean)
- Jika terdeteksi bahasa asing, fallback ke template asli
- Tambah instruksi eksplisit: "JANGAN gunakan bahasa asing"

### 3. ❌ Kata Serapan Salah (FIXED ✅)

**Masalah:**

- "teknisian" → seharusnya "teknisi"

**Solusi:**

- Tambah aturan eksplisit untuk kata serapan yang benar
- Contoh di prompt

## Implementasi Perbaikan

### File yang Diubah

- `src/convo/engine.py` - Fungsi `_naturalize_template()`

### Aturan Baru di Prompt

```python
Aturan WAJIB:
1. PERTAHANKAN semua informasi dari template - jangan tambah, kurang, atau ubah
2. Tetap profesional dan sopan sebagai customer service
3. Gunakan bahasa Indonesia yang baik dan benar - JANGAN gunakan bahasa asing
4. DILARANG gunakan bahasa gaul: "dong", "aja", "gitu", "sih", "gimana", "ngga"
5. DILARANG gunakan kata serapan salah: "teknisian" (gunakan "teknisi")
6. Gunakan "kak" untuk sapaan
7. Tidak gunakan kata "Anda"
8. Maksimal 3 kalimat
9. Hindari tanda kutip
10. Jangan bertele-tele
11. JANGAN mengarang atau mengubah konteks - ikuti template dengan ketat
```

### Safety Check Baru

```python
# Detect bahasa asing (CJK)
cjk_pattern = r'[\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff\uac00-\ud7af]'
if re.search(cjk_pattern, reply):
    reply = template_text  # fallback ke template asli
```

## Hasil Setelah Perbaikan

### Contoh 1: Pending Message

**Sebelum:** ❌

```
"Teruskan dong ke teknisi ya..."
```

**Sesudah:** ✅

```
"Baik kak, saya bantu teruskan ke teknisi ya."
```

### Contoh 2: Instruksi

**Sebelum:** ❌

```
"Buat nyambung aja kita cek covernya..."
```

**Sesudah:** ✅

```
"Kak, boleh dicek apakah covernya sudah tertutup rapat?"
```

### Contoh 3: Pertanyaan

**Sebelum:** ❌

```
"Gimana kak bunyinya? Sering atau jarang gitu?"
```

**Sesudah:** ✅

```
"Kak, apakah bunyinya terjadi sesekali atau sering?"
```

## Testing

### Test Script

- `tests/test_professional_response.py`

### Validasi

✅ Tidak ada bahasa gaul
✅ Tidak ada kata serapan salah
✅ Tidak ada bahasa asing
✅ Tetap profesional
✅ Natural tapi sopan

## Best Practice Going Forward

1. **Monitor LLM Log** - Cek `src/convo/llm_log/llm_log.json` untuk pattern aneh
2. **Update Prompt** - Jika ada pattern baru yang bermasalah, tambah ke contoh SALAH
3. **Balance** - Natural ≠ Gaul. Bisa ramah tapi tetap profesional
4. **Safety First** - Gunakan template asli jika output LLM tidak valid

## Trade-off Final

### Kelebihan ✅

- Respons natural dan enak dibaca
- Tetap profesional sebagai CS
- Tidak ada bahasa gaul/informal
- Safety mechanism untuk fallback

### Kekurangan ⚠️

- Sedikit lebih formal (tapi masih natural)
- Lebih predictable (variasi terbatas)
- Perlu monitoring pattern baru

**Kesimpulan:** Trade-off ini worth it untuk menjaga profesionalisme dan kualitas CS.
