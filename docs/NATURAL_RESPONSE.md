# Natural Response Enhancement

## Ringkasan Perubahan

Fitur baru untuk membuat respons bot lebih natural dan conversational, sambil tetap mengikuti template SOP yang ada.

## Masalah Sebelumnya

Bot merespons terlalu kaku berdasarkan template di `sop.json`. Contoh:

- Customer: "hmm bisa dibilang sering sih kak"
- Bot (kaku): "Bunyi sering menandakan ada kotoran yang tersangkut di pre-filter/collector cell. Mohon matikan unit..."

## Solusi

Menambahkan fungsi `_naturalize_template()` yang menggunakan LLM untuk:

1. Mengambil template dari SOP
2. Mengubahnya menjadi lebih natural sesuai konteks percakapan
3. Mempertahankan semua informasi penting dari template

## Implementasi

### 1. Fungsi Helper Baru

```python
def _naturalize_template(self, user_id: str, template_text: str, action_type: str) -> str:
    # Mengambil pesan terakhir customer
    # Menggunakan LLM untuk membuat template lebih natural
    # Mempertahankan isi/pesan utama dari SOP
```

### 2. Update di `_execute_llm_decision`

Semua action type sekarang menggunakan naturalisasi:

- `ask`: Pertanyaan troubleshooting
- `instruct`: Instruksi untuk customer
- `confirm`: Konfirmasi hasil
- `resolve`: Penutup case resolved
- `pending`: Penutup case pending
- `offer`: Penawaran solusi
- `next`: Transisi ke step berikutnya

### 3. Update di `handle_exploration`

Consistency di semua bagian flow troubleshooting.

## Hasil

### Sebelum

```
Customer: "hmm bisa dibilang sering sih kak"
Bot: "Bunyi sering menandakan ada kotoran yang tersangkut di pre-filter/collector cell. Mohon matikan unit, bersihkan pre-filter sesuai buku manual (keringkan sempurna), lalu nyalakan kembali. Jika bunyi tetap muncul, kami sarankan pemeriksaan teknisi. Jika ingin kami bantu bersihkan juga bisa kak, apakah kakak ingin dibantu membersihkan alatnya oleh tim teknisi kami?"
```

### Sesudah

```
Customer: "hmm bisa dibilang sering sih kak"
Bot: "Tahu sih, kadang-kadang memang terlihat kotor. Kita bisa jadwalkan teknisinya untuk membersihkan unitmu, kak."
```

## Testing

Jalankan test:

```bash
python tests/test_natural_response.py
```

Test mencakup:

- ✅ Komplain bunyi → natural question
- ✅ Jawaban "sering" → natural pending message
- ✅ Komplain mati → natural instructions
- ✅ Multiple steps troubleshooting → consistency

## Trade-off

### Kelebihan

- Respons lebih natural dan friendly
- Tetap mengikuti SOP
- Tidak kehilangan informasi penting
- Context-aware (sesuai chat sebelumnya)

### Kekurangan

- Lebih banyak LLM call (latency ~200-500ms per response)
- Konsumsi token lebih tinggi
- Response bisa bervariasi (tidak selalu sama persis)

## Konfigurasi Prompt

Prompt naturalisasi mengikuti aturan:

- Maksimal 3 kalimat
- Gunakan "kak" untuk sapaan
- Tidak gunakan kata "Anda"
- Sesuaikan dengan chat customer sebelumnya
- Pertahankan info penting dari template

## Log LLM Call

Semua naturalisasi di-log ke `src/convo/llm_log/llm_log.json` untuk monitoring.
