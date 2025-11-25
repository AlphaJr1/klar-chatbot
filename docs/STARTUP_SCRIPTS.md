# Shell Scripts & Logs Organization

Scripts sudah dirapihkan ke dalam folder terpisah untuk kemudahan maintenance.

## 📁 Struktur

```
klar-rag/
├── bin/                      # Executable scripts
│   ├── dev.sh               # Quick start (recommended)
│   ├── start_daemon.sh      # Daemon mode
│   ├── start_with_ngrok.sh  # With log monitoring
│   ├── start_server.sh      # Server only (no ngrok)
│   └── stop_all.sh          # Stop all services
│
├── logs/                     # Runtime logs (gitignored)
│   ├── server.log           # FastAPI server logs
│   └── ngrok.log            # Ngrok tunnel logs
│
├── .ngrok_url                # Current ngrok URL (gitignored)
└── ...
```

## 🚀 Usage (Updated Paths)

### Start Development

```bash
# From project root
bin/dev.sh

# Or
bin/start_daemon.sh
```

### Monitor Logs

```bash
# Server logs
tail -f logs/server.log

# Ngrok logs
tail -f logs/ngrok.log
```

### Stop Services

```bash
bin/stop_all.sh
```

### Get Ngrok URL

```bash
cat .ngrok_url
```

## ✨ Benefits

✅ **Clean root directory** - Scripts di `bin/`, logs di `logs/`  
✅ **Gitignore optimized** - Semua logs di satu folder  
✅ **Easy to find** - Semua scripts di satu tempat  
✅ **Works from anywhere** - Scripts auto-detect project root

## 🔧 All Scripts Work From Project Root

```bash
# All these work from /path/to/klar-rag
bin/dev.sh
bin/stop_all.sh
tail -f logs/server.log
```

Scripts otomatis detect dan pindah ke project root, jadi bisa dipanggil dari mana saja dalam project.
