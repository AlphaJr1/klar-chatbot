# 📁 Rencana Restrukturisasi Proyek

## 🎯 Tujuan
Merapikan struktur proyek agar lebih profesional, maintainable, dan mengikuti best practice Python project structure.

---

## 📊 Struktur SEBELUM

```
klar-rag/
├── convo/                      # Mixed: core + tests
│   ├── conversation_llm_engine.py
│   ├── data_collector.py
│   ├── memory_store.py
│   ├── ollama_client.py
│   ├── session_logger.py
│   ├── test_comprehensive.py     ❌ Test di core folder
│   ├── test_data_collection.py   ❌ Test di core folder
│   └── test_stress_full_flow.py  ❌ Test di core folder
├── retriever/                  # RAG components (keep)
├── kb/                         # Knowledge base (keep)
├── tools/                      # Build scripts
├── session_logs/               # Runtime logs
├── qdrant_storage/             # Vector DB storage
├── memory.json                 ❌ Data di root
├── rag_api.py                  ❌ API di root
├── requirements.txt            ✅ OK
├── .env                        ✅ OK
└── .gitignore                  ✅ OK
```

**Masalah:**
1. Test files tercampur dengan core code
2. Data files (memory.json) di root
3. API file di root, tidak dalam src/
4. Session logs & storage di root level
5. Tidak ada folder docs/ untuk dokumentasi

---

## 📊 Struktur SESUDAH (Target)

```
klar-rag/
├── src/                        # ✨ Source code utama
│   ├── __init__.py
│   ├── api.py                  # Renamed dari rag_api.py
│   ├── convo/                  # Conversation engine
│   │   ├── __init__.py
│   │   ├── engine.py           # Renamed dari conversation_llm_engine.py
│   │   ├── data_collector.py
│   │   ├── memory_store.py
│   │   ├── ollama_client.py
│   │   └── session_logger.py
│   └── retriever/              # RAG retriever (moved)
│       ├── __init__.py
│       └── retriever.py
│
├── tests/                      # ✨ Semua test files
│   ├── __init__.py
│   └── convo/
│       ├── __init__.py
│       ├── test_comprehensive.py
│       ├── test_data_collection.py
│       └── test_stress_full_flow.py
│
├── data/                       # ✨ Data & storage
│   ├── kb/                     # Knowledge base (moved)
│   ├── storage/                # ✨ Runtime storage
│   │   ├── qdrant/            # Vector DB (renamed from qdrant_storage)
│   │   ├── memory.json        # User memory
│   │   └── logs/              # Session logs (moved)
│   └── .gitkeep
│
├── scripts/                    # ✨ Utility scripts (renamed from tools)
│   ├── build/
│   │   ├── build_chat.py
│   │   ├── build_manual.py
│   │   └── build_style_chat.py
│   └── ingestion/
│       ├── add_chat_pair.py
│       ├── ingest_manual_qdrant.py
│       ├── ingest_qdrant.py
│       └── ingest_style_qdrant.py
│
├── docs/                       # ✨ Documentation
│   ├── CLEANUP_REPORT.md
│   └── RESTRUCTURE_PLAN.md
│
├── .env
├── .gitignore
├── requirements.txt
└── README.md                   # ✨ To be created
```

---

## 🔄 Migration Steps

### Step 1: Create new structure
```bash
mkdir -p src/convo
mkdir -p src/retriever
mkdir -p tests/convo
mkdir -p data/kb
mkdir -p data/storage/qdrant
mkdir -p data/storage/logs
mkdir -p scripts/build
mkdir -p scripts/ingestion
mkdir -p docs
```

### Step 2: Move source files
```bash
# Move convo core files
mv convo/conversation_llm_engine.py src/convo/engine.py
mv convo/data_collector.py src/convo/
mv convo/memory_store.py src/convo/
mv convo/ollama_client.py src/convo/
mv convo/session_logger.py src/convo/

# Move retriever
mv retriever/* src/retriever/

# Move API
mv rag_api.py src/api.py
```

### Step 3: Move test files
```bash
mv convo/test_*.py tests/convo/
```

### Step 4: Move data & storage
```bash
mv kb/* data/kb/
mv memory.json data/storage/
mv session_logs/* data/storage/logs/
mv qdrant_storage/* data/storage/qdrant/
```

### Step 5: Move tools to scripts
```bash
mv tools/build_*.py scripts/build/
mv tools/add_chat_pair.py scripts/ingestion/
mv tools/ingest_*.py scripts/ingestion/
```

### Step 6: Move docs
```bash
mv CLEANUP_REPORT.md docs/
mv RESTRUCTURE_PLAN.md docs/
```

### Step 7: Cleanup old directories
```bash
rmdir convo kb session_logs qdrant_storage tools retriever
```

### Step 8: Create __init__.py files
```bash
touch src/__init__.py
touch src/convo/__init__.py
touch src/retriever/__init__.py
touch tests/__init__.py
touch tests/convo/__init__.py
touch data/.gitkeep
```

---

## 📝 Files yang perlu UPDATE

### 1. **src/api.py** (renamed from rag_api.py)
- Update imports: `from convo.` → `from src.convo.`
- Update paths untuk data/storage/

### 2. **src/convo/engine.py** (renamed from conversation_llm_engine.py)
- Update imports internal
- Update path ke kb: `kb/` → `../data/kb/`

### 3. **All test files**
- Update imports: `from convo.` → `from src.convo.`

### 4. **scripts/** 
- Update paths ke data/

### 5. **.gitignore**
- Update patterns untuk struktur baru

---

## ✅ Benefits

1. **Separation of Concerns**
   - Source code di `src/`
   - Tests di `tests/`
   - Data di `data/`
   - Utils di `scripts/`

2. **Professional Structure**
   - Mengikuti Python best practices
   - Mudah di-package sebagai library

3. **Better Organization**
   - File mudah ditemukan
   - Clear responsibility per folder

4. **Scalability**
   - Mudah add module baru
   - Testing infrastructure jelas

---

## ⚠️ Breaking Changes

### Import paths akan berubah:
```python
# Before
from convo.conversation_llm_engine import ConversationEngine

# After
from src.convo.engine import ConversationEngine
```

### File paths akan berubah:
```python
# Before
kb_path = "kb/sop.json"
memory_path = "memory.json"

# After  
kb_path = "data/kb/sop.json"
memory_path = "data/storage/memory.json"
```

---

## 🚀 Execution

Siap dijalankan? Konfirmasi untuk mulai migration.
