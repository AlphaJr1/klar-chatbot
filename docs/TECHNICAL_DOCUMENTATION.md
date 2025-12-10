# Technical Documentation & Testing Report: Klar RAG Conversation Engine

**Version**: 1.0  
**Date**: December 10, 2025  
**Status**: Development  
**Repository**: [https://github.com/AlphaJr1/klar-chatbot](https://github.com/AlphaJr1/klar-chatbot)

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [System Architecture](#system-architecture)
3. [Implemented Features](#implemented-features)
4. [Not Yet Implemented Components](#not-yet-implemented-components)
5. [API Endpoints](#api-endpoints)
6. [Testing Results](#testing-results)
7. [Deployment](#deployment)
8. [Known Issues & Limitations](#known-issues--limitations)
9. [Recommendations](#recommendations)

---

## Executive Summary

Klar RAG is a conversation engine for Honeywell Electronic Air Cleaner (EAC) customer support. The system uses LLM (Qwen3:4B-Instruct via Ollama) to understand customer complaints and guide troubleshooting based on predefined Standard Operating Procedures (SOP).

---

## System Architecture

### Main Components

**Backend Framework**

- FastAPI 0.115.x
- Uvicorn server
- Python 3.10+

**AI/ML**

- LLM: Qwen3:4B-Instruct via Ollama (localhost:11434)
- Embeddings: Sentence Transformers (E5, BGE)
- Vector DB: Qdrant Client

**Storage**

- Memory: JSON-based (`data/storage/memory.json`)
- Logs: JSONL format (`data/storage/logs/`)
- Conversations: JSON (`data/storage/conversations.json`)

**Integration**

- WhatsApp: Via Node.js webhook (Baileys)
- Sync: Periodic background sync (60s interval)

### Architecture Diagrams

#### 1. System Architecture Overview

```mermaid
graph TB
    subgraph "Client Layer"
        A[WhatsApp User]
    end

    subgraph "Integration Layer"
        B[Node.js Webhook<br/>Baileys]
    end

    subgraph "Application Layer"
        C[FastAPI Server<br/>Port 8080]
        D[ConversationEngine]
        E[DataCollector]
        F[MemoryStore]
        G[TextNormalizer]
    end

    subgraph "AI/ML Layer"
        H[Ollama Server<br/>Port 11434]
        I[Qwen3:4B-Instruct]
        J[SentenceTransformers<br/>E5, BGE]
    end

    subgraph "Storage Layer"
        K[memory.json]
        L[conversations.json]
        M[logs/*.jsonl]
        N[sop.json]
    end

    subgraph "Optional Components"
        O[Qdrant Vector DB]
        P[Retriever<br/>Not Integrated]
    end

    A -->|Message| B
    B -->|POST /chat| C
    C --> D
    D --> E
    D --> F
    D --> G
    D -->|LLM Calls| H
    H --> I
    D -.->|Not Used| P
    P -.->|Not Used| O
    P -.->|Not Used| J
    F --> K
    C --> L
    D --> M
    D --> N
    C -->|Response| B
    B -->|Reply| A
```

#### 2. Conversation Flow Detail

```mermaid
sequenceDiagram
    participant U as User
    participant W as WhatsApp Webhook
    participant API as FastAPI
    participant E as Engine
    participant LLM as Ollama/Qwen3
    participant M as MemoryStore
    participant S as SOP

    U->>W: Send message
    W->>API: POST /chat
    API->>E: handle(user_id, text)

    E->>M: Get user history
    M-->>E: Return history

    E->>LLM: Detect intent
    LLM-->>E: Intent classification

    E->>S: Load SOP for intent
    S-->>E: Return steps

    E->>LLM: Generate response
    LLM-->>E: Natural response

    E->>M: Update history

    alt Escalation needed
        E->>E: Trigger data collection
        E->>LLM: Generate question
        LLM-->>E: Data collection question
    end

    E-->>API: Response bubbles
    API-->>W: JSON response
    W->>U: WhatsApp message
```

#### 3. Intent Detection Flow

```mermaid
flowchart TD
    A[User Message] --> B[Text Normalization]
    B --> C{Active Intent<br/>Exists?}

    C -->|Yes| D[Keep Active Intent]
    C -->|No| E[LLM Intent Detection]

    E --> F{Intent Type}
    F -->|mati| G[Load SOP: mati]
    F -->|bunyi| H{Intensity<br/>Detected?}
    F -->|bau| I[Load SOP: bau]
    F -->|none| J[Chitchat Handler]

    H -->|Yes| K[Skip Frequency<br/>Direct Escalate]
    H -->|No| L[Load SOP: bunyi]

    G --> M[Execute SOP Steps]
    K --> M
    L --> M
    I --> M

    M --> N{Step Result}
    N -->|Resolve| O[Mark Resolved]
    N -->|Pending| P[Trigger Data Collection]
    N -->|Next Step| Q[Continue SOP]
```

#### 4. Data Collection Flow

```mermaid
stateDiagram-v2
    [*] --> CheckPending: Escalation triggered

    CheckPending --> AskName: pending=true

    AskName --> ValidateName: User responds
    ValidateName --> AskProduct: Name valid
    ValidateName --> ClarifyName: Name unclear
    ClarifyName --> AskName: Retry

    AskProduct --> ValidateProduct: User responds
    ValidateProduct --> AskAddress: Product valid
    ValidateProduct --> ClarifyProduct: Product unclear
    ClarifyProduct --> AskProduct: Retry

    AskAddress --> ValidateAddress: User responds
    ValidateAddress --> Complete: Address valid
    ValidateAddress --> ClarifyAddress: Address unclear
    ClarifyAddress --> AskAddress: Retry

    Complete --> [*]: Data collection done
```

#### 5. Component Interaction

```mermaid
graph LR
    subgraph "ConversationEngine"
        A[handle]
        B[detect_intent_via_llm]
        C[handle_sop_flow]
        D[handle_data_collection]
        E[parse_answer_via_llm]
    end

    subgraph "External Dependencies"
        F[OllamaClient]
        G[MemoryStore]
        H[DataCollector]
        I[TextNormalizer]
    end

    A --> B
    A --> C
    A --> D
    B --> F
    C --> E
    E --> F
    D --> H
    H --> F
    A --> G
    A --> I
```

#### 6. Storage Structure

```mermaid
graph TD
    subgraph "data/storage/"
        A[memory.json]
        B[conversations.json]
        C[logs/]
        D[backups/]
    end

    subgraph "memory.json structure"
        E[user_id]
        E --> F[history]
        E --> G[identity]
        E --> H[flags]
        E --> I[slots]
    end

    subgraph "conversations.json"
        J[phone_number]
        J --> K[messages array]
        J --> L[last_sync]
    end

    subgraph "logs/"
        M[wa-YYYYMMDD.jsonl]
        N[llm_log.json]
        O[feedback.jsonl]
    end
```

---

## Implemented Features

### 1. Intent Detection

**Implementation**: `src/convo/engine.py:detect_intent_via_llm()`

**How It Works**:

- LLM classifies user messages into intents: `mati`, `bunyi`, `bau`, `none`
- Uses conversation history for context
- Text normalization to handle typos

**Supported Intents**:

- `mati`: Device not turning on, dead, powered off
- `bunyi`: Device making abnormal sounds
- `bau`: Device emitting unpleasant odors
- `none`: Chitchat, greetings, or out-of-domain

**Test Results**:

- Intent "mati": 6/6 test cases PASS (100% accuracy)
- Variations tested: "EAC saya mati nih", "alat tidak menyala", "unit padam total", "tidak hidup sama sekali", "mati total kak", "tidak berfungsi"

**Notes**:

- Accuracy depends on LLM prompt quality
- Some edge cases still need improvement

---

### 2. SOP-Based Troubleshooting

**Implementation**: `data/kb/sop.json` + `src/convo/engine.py`

**SOP Coverage**:

**Intent "mati"** (3 steps):

1. Check if cover is properly closed
2. Check remote LOW mode
3. Check MCB ON/OFF

**Intent "bunyi"** (1 step):

1. Ask frequency (frequent/rare)
   - Frequent → Escalate to technician
   - Rare → Resolve (normal)

**Intent "bau"** (1 step):

1. Direct escalation (pending_on_first_ask)

**Special Features**:

- Intensity detection: Skips frequency question if detects words like "banget", "parah", "sangat"
- Multi-template responses: Variations for natural conversation

**Test Results**:

- Multi-step flow works according to SOP (Step 1 → Step 2 → Step 3)
- Intensity detection works (skips frequency question)
- Pending on first ask works (2 bubbles generated)

**Limitations**:

- SOP is still simple, only 3 main intents
- Does not cover all troubleshooting scenarios
- Template responses are still limited

---

### 3. Data Collection

**Implementation**: `src/convo/data_collector.py`

**Data Collected**:

1. Customer/company name
2. Product (EAC model)
3. Address

**How It Works**:

- Automatically triggered upon escalation to technician
- Questions asked one by one
- LLM extracts information from user answers
- Validation and clarification loop if unclear

**Features**:

- Company name detection (PT/CV/UD/Toko)
- Gender detection for appropriate greetings
- Automatic backup before reset

**Test Results**:

- Data collection trigger works (name question appears after escalation)
- Flow: Escalation → Ask Name → Ask Product → Ask Address

---

### 4. Natural Language Processing

**Text Normalization** (`src/convo/text_normalizer.py`):

- Typo correction: "eac" → "EAC"
- Slang mapping: "ga" → "tidak", "udah" → "sudah"
- Punctuation cleanup

**Response Naturalization**:

- Transformation: "silakan" → "coba", "jika" → "kalau"
- Blacklist formal words: "Anda"
- Softening words: "sepertinya", "mungkin"

**Context Management**:

- Sliding window: Last 10 messages
- Deduplication to avoid repeated questions
- Per-user memory state

---

### 5. Spam Detection & Rate Limiting

**Implementation**: `src/convo/engine.py:_get_spam_level()`

**Spam Detection**:

- Irrelevant messages (emoji only, gibberish)
- Repetitive messages in short time

**Rate Limiting**:

- Level 1 (3-5 spam): Warning
- Level 2 (6-9 spam): Block 5 minutes
- Level 3 (10+ spam): Block 30 minutes

**Admin Controls**:

- `/admin/spam-status`: Check spam status
- `/admin/clear-spam`: Clear spam flags

**Test Results**:

- Test 2.1: Normal message → PASS
- Test 2.2: Soft limit (3x spam) → PASS, warning triggered
- Test 2.3: Medium limit (5x spam) → PASS, user blocked 59 minutes
- Test 2.4: Block status check → PASS
- Test 2.5: Hard limit (47x spam) → PASS, permanent spam flag set
- Success Rate: 5/5 (100%)

---

### 6. Memory & Session Management

**Memory Store** (`src/convo/memory_store.py`):

- Per-user state persistence
- Conversation history
- Flag-based state (pending, resolved, spam)
- Automatic backup before reset

**Session Logging**:

- JSONL logs per session
- LLM interaction logging
- Timestamp and metadata

**Sync Service** (`src/sync/conversation_sync.py`):

- Periodic sync every 60 seconds
- Updates `conversations.json`

---

## Not Yet Implemented Components

### RAG Retrieval

**Status**: Code exists in `src/retriever/retriever.py` but NOT integrated into conversation engine

**What Exists**:

- Retriever class with 3 collections:
  - `chat_history_pairs`: Chat history examples
  - `manual_book`: EAC manual
  - `style_guide`: Style examples
- Query translation (ID → EN)
- Semantic search via Qdrant

**What's Missing**:

- Not called from `ConversationEngine`
- Not used for response generation
- Qdrant collections may not be populated

**Reason**: Current system is fully SOP-based, does not use retrieval

---

## API Endpoints

### Core Endpoints

**POST `/chat`**

```json
Request:
{
  "user_id": "628123456789",
  "text": "alat saya mati"
}

Response:
{
  "bubbles": [{"type": "text", "text": "..."}],
  "next": "await_reply",
  "status": "open",
  "meta": {"took_ms": 1234}
}
```

**GET `/health`**

```json
{
  "ok": true,
  "engine_ready": true,
  "version": "1.0-clean"
}
```

### Admin Endpoints

- `POST /admin/reset-memory`: Reset user memory
- `GET /admin/memory-stats`: Memory statistics
- `GET /admin/spam-status`: Check spam status
- `POST /admin/clear-spam`: Clear spam flags
- `POST /admin/reset-conversations`: Reset conversations.json

### Other Endpoints

- `POST /summarize`: Generate conversation summary
- `POST /sync/now`: Manual sync trigger
- `GET /sync/status`: Sync status
- `POST /feedback`: Submit feedback

---

## Testing Results

### Test Summary

| Test Suite       | Total Cases | Pass | Fail | Success Rate |
| ---------------- | ----------- | ---- | ---- | ------------ |
| Final Complete   | 4           | 1    | 3    | 25%          |
| Spam Handling    | 5           | 5    | 0    | 100%         |
| Intent Detection | 6           | 6    | 0    | 100%         |

### Test Suite 1: Final Complete Test

**File**: `tests/test_final_complete.py`

#### Test Case 1.1: Intensity Detection

**Scenario**: Customer complaint with high intensity words

```text
Input: "alat saya berisik banget"

Expected:
- Skip frequency question
- 2 bubbles response
- Keywords: 'bunyi', 'teknisi', 'nama'

Actual Output:
Bubble 1: "Kak, sepertinya unitnya perlu dibersihkan ya, karena ada
          kotoran yang menyangkut. Kami jadwalkan teknisinya nanti."
Bubble 2: "Boleh tahu kemarin pembeliannya atas nama siapa Kak?"

Result: FAIL
Reason: Expected keywords don't match
```

**Analysis**:

- System successfully skipped frequency question
- System successfully triggered data collection (2 bubbles)
- Failure because test expects keyword "bunyi" in response, but LLM generated more natural response without explicitly mentioning "bunyi"
- Functionality actually WORKS, just different wording

#### Test Case 1.2: Normal Sound Flow

**Scenario**: Customer complaint about sound without intensity words

```text
Input: "alat saya berbunyi"

Expected: Keywords 'sering atau jarang'
Actual: "Kak, bunyinya sering terjadi atau hanya sesekali saja?"

Result: FAIL
Reason: Wording variation

Follow-up: "sering sih kak" → PASS
```

**Analysis**:

- System works well
- LLM generates more natural wording variations
- Test expectations too strict with exact keyword matching

#### Test Case 1.3: Odor - Pending on First Ask

```text
Input: "kok bau ya dari eac"

Expected: Keywords 'carbon filter' (English)
Actual: "filter karbon" (Indonesian)

Result: FAIL
Reason: Language mismatch
```

**Analysis**:

- System works according to logic (pending on first ask)
- 2 bubbles generated correctly
- Failure only due to language (carbon filter vs filter karbon)
- Functionality CORRECT

#### Test Case 1.4: Dead Device - Multi-step Troubleshooting

```text
Input: "eac mati"
Output: Check cover instruction

Follow-up: "sudah rapat"
Output: Check remote LOW instruction

Result: Multi-step flow works according to SOP
```

### Test Suite 2: Spam Handling

**File**: `tests/test_spam_handling.py`

**All Tests**: 5/5 PASS (100%)

- Normal message: No spam detection
- Soft limit (3x spam): Warning triggered
- Medium limit (5x spam): User blocked 59 minutes
- Block status check: Blocking works
- Hard limit (47x spam): Permanent spam flag set

### Test Suite 3: Intent Detection

**File**: `tests/test_intent_detection.py`

**All Tests**: 6/6 PASS (100%)

Variations tested:

- "EAC saya mati nih"
- "alat tidak menyala"
- "unit padam total"
- "tidak hidup sama sekali"
- "mati total kak"
- "tidak berfungsi"

### Important Notes About Test Failures

Test failures in "Final Complete" are not because the system doesn't work, but because:

1. **Keyword Matching Too Strict**: Tests expect exact keywords, but LLM generates natural variations
2. **Language Mismatch**: Tests expect English, LLM generates Indonesian
3. **Natural Variations**: LLM responses vary each run

**Actual Functionality**:

- Intensity detection: WORKS
- Pending on first ask: WORKS
- Data collection trigger: WORKS
- Multi-step flow: WORKS

### Issues Found

**Issue 1: Response Wording Variability**

- Problem: LLM generates different wording each run
- Example: "sering atau jarang?" vs "sering terjadi atau hanya sesekali saja?"
- Impact: Test failures despite correct functionality
- Recommendation: Use semantic similarity or set temperature=0

**Issue 2: Keyword Language Mismatch**

- Problem: Tests expect English, LLM generates Indonesian
- Example: "carbon filter" vs "filter karbon"
- Impact: False negatives in test results
- Recommendation: Update test expectations to accept both languages

**Issue 3: Limited Test Coverage**

- Problem: Only tests happy path
- Missing: Multiple intents, context switching, invalid input, LLM timeout
- Recommendation: Expand test suite

### Performance Metrics

**Response Time** (from test observations):

- Average: 1-3 seconds per response
- Variability: Depends on LLM load

**Accuracy**:

- Intent detection: 100% (for intent "mati")
- Spam detection: 100%
- Overall conversation flow: Functional but test failures due to strict assertions

---

## Deployment

### System Requirements

- CPU: 4 cores minimum
- RAM: 8GB minimum (for Ollama + Qwen3:4B)
- Storage: 20GB
- OS: Linux/MacOS

### Dependencies

**Python**:

- FastAPI, Uvicorn, Pydantic
- Sentence Transformers, Qdrant Client
- NLTK, RapidFuzz for text processing

**External Services**:

- Ollama server with Qwen3:4B-Instruct model
- Node.js for WhatsApp webhook
- (Optional) Qdrant server for RAG

### Setup Steps

1. Install Ollama and pull model:

```bash
ollama serve
ollama pull qwen3:4B-instruct
```

2. Setup Python environment:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

3. Configure `.env`:

```bash
APP_PORT=8080
NODE_SERVER_URL=https://your-webhook-url/api/send
OLLAMA_BASE_URL=http://localhost:11434
```

4. Start services:

```bash
uvicorn src.api:app --host 0.0.0.0 --port 8080
```

### Monitoring & Logging

**Log Files**:

- Session logs: `data/storage/logs/wa-*.jsonl`
- LLM logs: `data/storage/logs/llm_log.json`
- Feedback: `data/storage/logs/feedback.jsonl`

**Monitoring Endpoints**:

- `/health`: System health check
- `/sync/status`: Conversation sync status
- `/admin/memory-stats`: Memory usage statistics

---

## Known Issues & Limitations

### Current Issues

1. **Test Failures**: Some test cases fail due to overly strict keyword matching
2. **Response Variability**: LLM responses are not always consistent
3. **RAG Not Integrated**: Retriever code exists but is not used

### Limitations

1. **Language**: Indonesian only
2. **SOP Coverage**: Only 3 main intents (mati, bunyi, bau)
3. **No Image Support**: Does not support image troubleshooting
4. **No Voice Support**: Does not support voice messages
5. **Single Intent**: Does not handle multiple intents in one message well

### Technical Debt

1. **Code Size**: `engine.py` is 3942 lines, needs refactoring
2. **LLM Dependency**: Heavily dependent on LLM quality
3. **No Caching**: Every request hits LLM, no caching layer
4. **JSON Storage**: Production should use proper database

---

## Recommendations

### For Test Suite

1. Refactor test assertions to not be too strict on exact keyword matching
2. Use semantic similarity or regex patterns
3. Accept language variations (English/Indonesian)
4. Add test cases for edge cases
5. Implement proper test fixtures and mocking

### For System

1. Set temperature=0 for more consistent LLM output
2. Implement response caching for common queries
3. Add more logging for debugging
4. Improve error handling for LLM failures
5. Add metrics collection for monitoring

### For Production

1. **Testing**: Fix test suite, don't be too strict on keyword matching
2. **Monitoring**: Setup proper monitoring (Prometheus, Grafana)
3. **Database**: Migrate from JSON to PostgreSQL
4. **Caching**: Implement Redis for common queries
5. **Load Testing**: Not yet done
6. Setup staging environment for testing before production
7. Implement proper error tracking (Sentry, etc)
8. Add health checks for all dependencies (Ollama, etc)

### For Development

1. **Refactoring**: Split `engine.py` into smaller modules
2. **RAG Integration**: Integrate retriever or remove if not used
3. **SOP Expansion**: Add coverage for more troubleshooting scenarios
4. **Error Handling**: Improve error handling and fallback mechanisms
5. **Documentation**: Inline code documentation is still minimal

---

## Conclusion

The conversation engine system works for basic troubleshooting flow with SOP-based approach. Uses LLM for intent detection and response generation. Some advanced features like RAG retrieval are not yet integrated.

**Implementation Status**:

- Core conversation flow: Implemented
- Intent detection: Implemented (100% accuracy for intent "mati")
- SOP-based troubleshooting: Implemented (3 intents)
- Data collection: Implemented
- Spam handling: Implemented (100% test pass)
- Memory management: Implemented
- RAG retrieval: Not integrated
- Multi-language: Not implemented
- Image/Voice support: Not implemented

**Functional Status**:

- Intent detection: Working
- Spam handling: Working
- Data collection: Working
- Multi-step troubleshooting: Working
- Response generation: Working (but variable)

**Test Status**:

- Need to refactor test suite
- Need to expand test coverage
- Need to fix overly strict test assertions

**Next Steps**:

1. Fix test suite
2. Add more test cases
3. Run load testing
4. Address LLM response variability
5. Improve error handling

**Note**: System is still in development stage with some test failures (not bugs, but test suite issues) and technical debt that needs to be addressed before production deployment.

---

_Document created: December 10, 2025_  
_Based on actual codebase and test results_
