# Klar RAG - Conversation Engine

Intelligent conversation engine untuk Honeywell Electronic Air Cleaner customer support dengan troubleshooting automation dan data collection.

## 📁 Project Structure

```
klar-rag/
├── src/                    # Source code
│   ├── api.py             # FastAPI server
│   ├── convo/             # Conversation engine
│   │   ├── engine.py      # Main conversation engine
│   │   ├── data_collector.py
│   │   ├── memory_store.py
│   │   ├── ollama_client.py
│   │   └── session_logger.py
│   └── retriever/         # RAG retriever components
│       └── retriever.py
│
├── tests/                  # Test files
│   └── convo/
│       ├── test_comprehensive.py
│       ├── test_data_collection.py
│       └── test_stress_full_flow.py
│
├── data/                   # Data & storage
│   ├── kb/                # Knowledge base
│   │   └── sop.json       # Standard Operating Procedures
│   └── storage/           # Runtime data
│       ├── logs/          # Session & LLM logs
│       ├── qdrant/        # Vector database storage
│       └── memory.json    # User memory & state
│
├── scripts/                # Utility scripts
│   ├── build/             # Build scripts
│   └── ingestion/         # Data ingestion scripts
│
└── docs/                   # Documentation
    ├── CLEANUP_REPORT.md
    └── RESTRUCTURE_STATUS.md
```

## 🚀 Quick Start

### Prerequisites

```bash
# Python 3.10+
python --version

# Install dependencies
pip install -r requirements.txt
```

### Running the API

**⚠️ IMPORTANT:** Must run from project root directory!

```bash
cd /Users/adrianalfajri/Projects/klar-rag
```

**Option 1: Quick Start Script** (Recommended)

```bash
# Development mode with auto-reload
./start_server.sh

# Custom port
./start_server.sh 9000

# Production mode
./start_server.sh 8080 prod
```

**Option 2: Direct uvicorn command**

```bash
# Development mode (auto-reload on code changes)
uvicorn src.api:app --host 0.0.0.0 --port 8080 --reload

# Production mode (better performance)
uvicorn src.api:app --host 0.0.0.0 --port 8080

# Localhost only (more secure for development)
uvicorn src.api:app --host 127.0.0.1 --port 8080 --reload
```

**Testing if server is running:**

```bash
# Health check
curl http://localhost:8080/health

# Test chat endpoint
curl -X POST http://localhost:8080/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test123", "text": "Halo"}'
```

### Running Tests

```bash
# Run all tests
python -m pytest tests/

# Run specific test
python tests/convo/test_comprehensive.py
```

### Memory Management

Mengelola memory chatbot (hapus user atau kosongkan semua):

```bash
# Versi Python (Recommended)
python3 scripts/clear_memory.py

# Versi Bash
./bin/clear_memory.sh
```

**Fitur:**

- **Opsi 1:** Hapus user_id tertentu (dengan list semua user)
- **Opsi 2:** Kosongkan memory total
- **Opsi 3:** Cancel (tidak ada perubahan)

**Catatan:**

- Script akan **otomatis stop server** sebelum proses
- **Backup otomatis** dibuat di `data/storage/backups/`
- Server akan **auto-restart** setelah selesai

## 🔧 Configuration

Environment variables (`.env`):

```bash
APP_PORT=8080
NODE_SERVER_URL=https://your-webhook-url.ngrok-free.dev/api/send
```

## 📊 Features

- **Intelligent Troubleshooting:** SOP-based automated troubleshooting flow
- **Data Collection:** Natural conversation-based user data collection
- **Memory Management:** Persistent user state and conversation history
- **Session Logging:** Comprehensive logging for debugging and analytics
- **RAG Integration:** Vector-based knowledge retrieval (optional)
- **Webhook Integration:** Real-time updates to external systems

## 🧪 Testing

The project includes comprehensive test suites:

- `test_comprehensive.py` - End-to-end data collection tests
- `test_data_collection.py` - LLM-simulated customer interactions
- `test_stress_full_flow.py` - Stress testing with distractions

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

### POST `/feedback`

User feedback submission

### POST `/summarize`

Generate conversation summary using LLM

```json
{
  "session_id": "string",
  "messages": [optional array of message objects],
  "use_local_logs": false,
  "send_to_node": false
}
```

Returns:

```json
{
  "success": true,
  "session_id": "string",
  "summary": "formatted summary text",
  "message_count": 10,
  "metadata": {
    "generated_at": "timestamp",
    "source": "local_logs | node_server"
  }
}
```

### GET `/admin/logs`

Retrieve recent session logs

## 🗂️ Data Storage

- **Memory:** `data/storage/memory.json` - User state and conversation history
- **Logs:** `data/storage/logs/` - Session logs and LLM interactions
- **Vector DB:** `data/storage/qdrant/` - Qdrant vector database
- **Knowledge Base:** `data/kb/sop.json` - Troubleshooting SOPs

## 🔄 Migration from Old Structure

This project was recently restructured for better organization:

- Old structure backup: `/Users/adrianalfajri/Projects/klar-rag-old-structure-*`
- See `docs/RESTRUCTURE_STATUS.md` for details

## 📄 License

Internal project - Honeywell Indonesia

## 👥 Maintainers

- Development Team
