# Klar RAG - Conversation Engine

Intelligent conversation engine untuk Honeywell Electronic Air Cleaner customer support dengan troubleshooting automation dan data collection.

## 📋 Prerequisites

### 1. Python Environment

- Python 3.10 atau lebih tinggi
- pip untuk manajemen package

```bash
python --version  # pastikan >= 3.10
```

### 2. Ollama & Qwen2.5:7B-Instruct

**Install Ollama:**

```bash
# MacOS
brew install ollama

# Linux
curl -fsSL https://ollama.com/install.sh | sh

# Windows
# Download dari https://ollama.com/download
```

**Jalankan Ollama Server:**

```bash
ollama serve
```

**Download dan Test Qwen2.5:7B-Instruct:**

```bash
# Download model (sekitar 4.7GB)
ollama pull qwen2.5:7b-instruct

# Test model
ollama run qwen2.5:7b-instruct "Hello, how are you?"
```

Pastikan Ollama berjalan di `http://localhost:11434` (default port)

## 🚀 Setup Project

### 1. Clone Repository

```bash
git clone <repository-url>
cd klar-rag
```

### 2. Setup Python Virtual Environment

```bash
# Buat virtual environment
python -m venv .venv

# Aktifkan virtual environment
# MacOS/Linux:
source .venv/bin/activate

# Windows:
.venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Setup Environment Variables

Buat file `.env` di root directory:

```bash
cp .env.example .env  # atau buat manual
```

Isi `.env`:

```bash
APP_PORT=8080
NODE_SERVER_URL=https://your-webhook-url.ngrok-free.dev/api/send
OLLAMA_BASE_URL=http://localhost:11434
```

### 5. Setup Data Directories

```bash
# Pastikan struktur folder sudah benar
mkdir -p data/storage/logs
mkdir -p data/storage/backups
mkdir -p logs
```

## ▶️ Running the Server

**PENTING:** Jalankan dari root directory project!

### Development Mode (Recommended)

```bash
# Pastikan Ollama sudah berjalan
# Terminal 1:
ollama serve

# Terminal 2:
uvicorn src.api:app --host 0.0.0.0 --port 8080 --reload
```

### Production Mode

```bash
uvicorn src.api:app --host 0.0.0.0 --port 8080
```

### Verifikasi Server

Test endpoint:

```bash
# Health check
curl http://localhost:8080/health

# Test chat
curl -X POST http://localhost:8080/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test123", "text": "Halo"}'
```

Expected response:

```json
{
  "user_id": "test123",
  "reply": "Halo! Ada yang bisa saya bantu?",
  "memory": {...}
}
```

## 🧪 Testing

### Run Test Suite

```bash
# Test sederhana
python tests/test_smart_company.py

# Test natural response
python tests/test_natural_response.py

# Test comprehensive
python -m pytest tests/ -v
```

### Manual Testing

```bash
# Test konversi singkat
python tests/quick_validation.py

# Stress test
python tests/stress_test_api.py
```

## 📁 Project Structure

```
klar-rag/
├── src/
│   ├── api.py              # FastAPI server
│   ├── convo/
│   │   ├── engine.py       # Main conversation engine
│   │   ├── data_collector.py
│   │   ├── memory_store.py
│   │   ├── ollama_client.py
│   │   └── session_logger.py
│   └── retriever/
│       └── retriever.py
│
├── tests/
│   ├── test_smart_company.py
│   ├── test_natural_response.py
│   └── quick_validation.py
│
├── data/
│   ├── kb/
│   │   └── sop.json        # Standard Operating Procedures
│   └── storage/
│       ├── logs/           # Session & LLM logs
│       ├── backups/        # Memory backups
│       └── memory.json     # User memory & state
│
├── scripts/
│   ├── clear_memory.py
│   └── view_chat_logs.py
│
└── requirements.txt
```

## 🔧 Troubleshooting

### Ollama Connection Error

```bash
# Pastikan Ollama berjalan
curl http://localhost:11434/api/tags

# Restart Ollama jika perlu
pkill ollama
ollama serve
```

### Model Not Found

```bash
# List model yang ada
ollama list

# Re-pull model jika perlu
ollama pull qwen2.5:7b-instruct
```

### Port Already in Use

```bash
# Gunakan port lain
uvicorn src.api:app --host 0.0.0.0 --port 9000 --reload

# Atau kill process yang menggunakan port
lsof -ti:8080 | xargs kill -9
```

### Memory Issues

```bash
# Clear memory dengan backup otomatis
python scripts/clear_memory.py
```

## 📝 API Endpoints

### POST `/chat`

Main conversation endpoint

```json
{
  "user_id": "string",
  "text": "string"
}
```

### GET `/health`

Health check endpoint

### POST `/summarize`

Generate conversation summary

```json
{
  "session_id": "string",
  "use_local_logs": false
}
```

### POST `/admin/reset-memory`

Reset user memory (backup otomatis)

```json
{
  "user_id": "string"
}
```

## 🛠️ Development Commands

```bash
# Aktifkan virtual environment
source .venv/bin/activate

# Install dependencies baru
pip install <package-name>
pip freeze > requirements.txt

# View chat logs
python scripts/view_chat_logs.py

# Clear memory
python scripts/clear_memory.py
```

## 📊 Features

- **Intelligent Troubleshooting:** SOP-based automated troubleshooting flow
- **Data Collection:** Natural conversation-based user data collection
- **Memory Management:** Persistent user state dengan backup otomatis
- **Session Logging:** Comprehensive logging untuk debugging
- **RAG Integration:** Vector-based knowledge retrieval
- **LLM-Powered:** Natural language understanding menggunakan Qwen2.5
- **Spam Filter:** Deteksi spam dan irrelevant messages
- **Intent Detection:** Smart intent detection untuk better UX

## 🗂️ Data Storage

- **Memory:** `data/storage/memory.json` - User state dan conversation history
- **Logs:** `data/storage/logs/` - Session logs dan LLM interactions
- **Backups:** `data/storage/backups/` - Memory backups otomatis
- **Knowledge Base:** `data/kb/sop.json` - Troubleshooting SOPs

## 📄 License

Internal project

## 👥 Maintainers

Development Team
