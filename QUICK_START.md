# Quick Start Guide

## 1. Install Ollama

```bash
# MacOS
brew install ollama

# Linux
curl -fsSL https://ollama.com/install.sh | sh
```

## 2. Setup Ollama

```bash
# Terminal 1: Start Ollama server
ollama serve

# Terminal 2: Pull Qwen2.5 (4.7GB)
ollama pull qwen2.5:7b-instruct

# Test
ollama run qwen2.5:7b-instruct "Hello"
```

## 3. Clone & Setup Project

```bash
git clone <repository-url>
cd klar-rag

# Setup Python venv
python -m venv .venv
source .venv/bin/activate  # MacOS/Linux
# atau .venv\Scripts\activate di Windows

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Edit .env sesuai kebutuhan
```

## 4. Run Server

```bash
# Pastikan Ollama berjalan!
# Terminal 1: ollama serve

# Terminal 2: Run API
uvicorn src.api:app --host 0.0.0.0 --port 8080 --reload
```

## 5. Test

```bash
# Health check
curl http://localhost:8080/health

# Test chat
curl -X POST http://localhost:8080/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test123", "text": "Halo"}'

# Atau run test
python tests/quick_validation.py
```

## Troubleshooting

**Ollama error:**

```bash
curl http://localhost:11434/api/tags
ollama list
```

**Port sudah dipakai:**

```bash
lsof -ti:8080 | xargs kill -9
```

Lihat `README.md` untuk detail lengkap!
