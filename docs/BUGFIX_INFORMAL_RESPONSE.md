# Bug Fix: Natural Response Terlalu Informal

## Masalah yang Ditemukan

Setelah implementasi natural response, ditemukan beberapa respons bot yang **terlalu informal dan aneh**:

### Contoh Respons Bermasalah

- ❌ "teruskan dong..."
- ❌ "buat nyambung aja..."
- ❌ "di cek bersama..."
- ❌ "gimana kak?"

### Root Cause

LLM terlalu creative dalam naturalisasi template, menghasilkan bahasa yang:

1. Terlalu gaul/informal (dong, aja, gitu, sih)
2. Mengubah konteks dari template asli
3. Menambah informasi yang tidak perlu
4. Tidak sesuai dengan standar CS profesional

## Solusi yang Diterapkan

### 1. Update Prompt Naturalisasi

Menambahkan aturan lebih ketat di `_naturalize_template()`:

```python
Aturan WAJIB:
1. PERTAHANKAN semua informasi dari template - jangan tambah, kurang, atau ubah
2. Tetap profesional dan sopan sebagai customer service
3. Gunakan bahasa Indonesia yang baik dan benar
4. DILARANG gunakan bahasa gaul: "dong", "aja", "gitu", "sih", "gimana", "ngga"
5. DILARANG gunakan kata serapan salah: "teknisian" (gunakan "teknisi")
6. Gunakan "kak" untuk sapaan
7. Tidak gunakan kata "Anda"
8. Maksimal 3 kalimat
9. Hindari tanda kutip
10. Jangan bertele-tele
11. JANGAN mengarang atau mengubah konteks - ikuti template dengan ketat
```

### 2. Tambah Contoh Konkret

Memberikan contoh BENAR dan SALAH:

```
Contoh konversi yang BENAR:
Template: "Baik kak, saya teruskan ke teknisi ya."
Natural: "Baik kak, saya bantu teruskan ke teknisi ya."

Contoh konversi yang SALAH:
Template: "Baik kak, saya teruskan ke teknisi ya."
SALAH: "Teruskan dong ke teknisi ya..." ❌ (bahasa gaul)
SALAH: "Buat nyambung aja kita cek..." ❌ (mengubah makna)
```

### 3. Cleanup Otomatis

Tambah post-processing untuk remove tanda kutip:

```python
reply = reply.replace('"', '').replace("'", '')
```

## Hasil Perbaikan

### Sebelum Perbaikan

```
Customer: "sering kak"
Bot: "Teruskan dong ke teknisi ya..." ❌
```

### Setelah Perbaikan

```
Customer: "sering kak"
Bot: "Baik kak, silakan matikan unit, bersihkan pre-filter sesuai buku manual. Jika bunyi masih muncul, kami sarankan pemeriksaan oleh teknisi." ✅
```

## Testing

Test script: `tests/test_professional_response.py`

Validasi:

- ✅ Tidak ada bahasa gaul (dong, aja, gitu, sih)
- ✅ Tidak ada kata serapan salah (teknisian)
- ✅ Tetap profesional dan sopan
- ✅ Natural tapi tidak berlebihan
- ✅ Tidak mengubah konteks/makna template

## Trade-off

### Kelebihan

- Respons tetap natural
- Profesional dan sopan
- Sesuai standar CS
- Tidak ada bahasa gaul

### Kekurangan

- Mungkin sedikit lebih formal dibanding sebelumnya
- Variasi respons lebih terbatas (lebih predictable)

## Best Practice

**Prinsip Naturalisasi yang Baik:**

1. **Pertahankan informasi** - Jangan ubah, tambah, atau kurangi
2. **Natural ≠ Gaul** - Natural bisa tetap profesional
3. **Konteks tetap sama** - Jangan mengubah maksud template
4. **Sopan dan jelas** - CS yang baik ramah tapi profesional

## Monitoring

Perhatikan LLM log di `src/convo/llm_log/llm_log.json` untuk:

- Kata-kata gaul yang muncul
- Template yang sering diubah konteksnya
- Response pattern yang aneh

Jika menemukan pattern baru yang bermasalah, update prompt naturalisasi dengan contoh konkret.
