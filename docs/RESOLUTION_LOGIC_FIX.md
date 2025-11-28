# Resolution Logic Fix

## Masalah

Sebelumnya, sistem bisa langsung resolve ticket hanya dengan user menjawab "iya" atau "ya" pada pertanyaan konfirmasi, tanpa ada konfirmasi eksplisit bahwa masalah sudah teratasi.

## Solusi

Menambahkan validasi `_is_explicit_resolution()` pada bagian `waiting_confirm` dengan `resolve_if_yes`, sehingga sistem tidak langsung resolve hanya karena user jawab "yes", tapi harus ada konfirmasi eksplisit seperti:

- "sudah berfungsi normal"
- "sudah menyala"
- "sudah baik"
- "sudah normal"
- dll (lihat `_is_explicit_resolution()` untuk daftar lengkap)

## Perubahan Kode

File: `src/convo/engine.py`
Lokasi: Line 1878-1900 (handle_exploration - waiting_confirm section)

Sebelumnya:

```python
if user_answer_confirm == 'yes':
    if confirm_data.get("resolve_if_yes"):
        # Langsung resolve
        resolve_list = step_def.get("resolve_templates", [])
        ...
```

Sesudahnya:

```python
if user_answer_confirm == 'yes':
    if confirm_data.get("resolve_if_yes"):
        # Cek apakah ada konfirmasi eksplisit
        if not self._is_explicit_resolution(message):
            # Minta konfirmasi eksplisit
            clarify_msg = "Jadi alatnya sudah berfungsi normal kak?"
            self.memstore.append_history(user_id, "bot", clarify_msg)
            return {"bubbles": [{"text": clarify_msg}], "next": "await_reply"}

        # Baru resolve jika ada konfirmasi eksplisit
        resolve_list = step_def.get("resolve_templates", [])
        ...
```

## Flow Baru

1. Bot: "Apakah alatnya sudah berfungsi normal kak?"
2. User: "iya" → Bot: "Jadi alatnya sudah berfungsi normal kak?" (minta konfirmasi eksplisit)
3. User: "sudah berfungsi normal" → Bot: "Baik kak, saya tutup laporannya ya." (resolve)

## Test

Run: `python tests/test_explicit_resolution.py`

Test memverifikasi:

- ✅ Sistem TIDAK resolve dengan jawaban "iya" saja
- ✅ Sistem resolve dengan konfirmasi eksplisit "sudah berfungsi normal"
