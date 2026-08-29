---
title: Advanced RAG Chatbot
emoji: 🧠
colorFrom: indigo
colorTo: purple
sdk: gradio
sdk_version: 4.44.0
app_file: app.py
pinned: false
license: mit
---

# 🧠 Enterprise AI Knowledge Assistant — Advanced Multi-Tenant RAG Platform

<div align="center">

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg?style=for-the-badge&logo=FastAPI&logoColor=white)](https://fastapi.tiangolo.com)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.38+-FF4B4B.svg?style=for-the-badge&logo=Streamlit&logoColor=white)](https://streamlit.io)
[![Qdrant](https://img.shields.io/badge/Qdrant-Vector%20DB-DC2626.svg?style=for-the-badge&logo=qdrant&logoColor=white)](https://qdrant.tech)
[![Groq](https://img.shields.io/badge/Groq-LPU%20Inference-F97316.svg?style=for-the-badge)](https://groq.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1.svg?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED.svg?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com)
[![Python](https://img.shields.io/badge/Python-3.12+-3776AB.svg?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org)
[![Pytest](https://img.shields.io/badge/Tests-32%2F32%20Passed-22C55E.svg?style=for-the-badge&logo=pytest&logoColor=white)](https://pytest.org)

<p align="center">
  <b>A production-ready, multi-tenant Advanced Retrieval-Augmented Generation (RAG) platform with multi-strategy query optimization, hybrid search (BM25 + BGE), cross-encoder reranking, corrective self-reflection (CRAG), strict source grounding, and dual interactive frontends.</b>
</p>

[System Architecture](#-system-architecture) •
[RAG Pipeline](#-advanced-rag-pipeline-lifecycle) •
[Key Features](#-key-features) •
[Quickstart Guide](#-step-by-step-setup-guide) •
[Docker Compose](#-docker-compose-quickstart) •
[API Reference](#-rest-api-reference) •
[Cloud Deployment](#-cloud-deployment-guide)

---

</div>

## 📌 Overview

The **Enterprise AI Knowledge Assistant** bridges organizational knowledge silos by converting raw corporate documents (PDF, DOCX, TXT, MD) into an interactive, multi-turn conversational knowledge system. 

Unlike standard naive RAG implementations that suffer from hallucination, context dilution, and poor lexical precision, this system implements a **multi-stage retrieval and validation pipeline**:
1. **Intelligent Query Routing:** Directs incoming queries to Direct QA, Multi-turn Query Rewriting, or Hypothetical Document Embeddings (HyDE).
2. **Dense + Sparse Hybrid Search:** Combines semantic vector similarity (`BAAI/bge-small-en-v1.5`) with exact lexical matching (`BM25Okapi`).
3. **Reciprocal Rank Fusion (RRF):** Merges multi-modal rank lists without score calibration discrepancies.
4. **Cross-Encoder Reranking:** Computes cross-attention relevance scores (`ms-marco-MiniLM-L-6-v2`) to eliminate false-positive candidates.
5. **Corrective RAG (CRAG):** Evaluates context relevance before synthesis, triggering automated query reformulation if retrieved context is insufficient.
6. **Strict Grounded Generation:** Synthesizes answers using high-speed Groq LPUs (`Llama 3.3 70B` / `GPT-OSS 120B`) with verifiable citations (file name, page numbers, and exact text snippets).

---

## 🏗️ System Architecture

### High-Level Topology

```text
 ┌──────────────────────────────────────────────────────────────────────────────────────────┐
 │                                   CLIENT INTERFACES                                      │
 │   ┌─────────────────────────────────────────┐  ┌─────────────────────────────────────┐   │
 │   │  Streamlit Multi-Page Web App (Port 8501)│  │ Modern Glassmorphism Web App (Port  │   │
 │   │  (KB Manager, Document Upload, Chat)    │  │ 3000 / index.html + script.js)      │   │
 │   └────────────────────┬────────────────────┘  └──────────────────┬──────────────────┘   │
 └────────────────────────┼──────────────────────────────────────────┼──────────────────────┘
                          │ REST API (JSON / Multipart Form-Data)    │
                          ▼                                          ▼
 ┌──────────────────────────────────────────────────────────────────────────────────────────┐
 │                               FASTAPI BACKEND SERVICE (Port 8000)                        │
 │  ┌────────────────────────────────────────────────────────────────────────────────────┐  │
 │  │ API Routers: /auth  •  /users  •  /knowledge-bases  •  /documents  •  /chat        │  │
 │  ├────────────────────────────────────────────────────────────────────────────────────┤  │
 │  │ Core Services: JWT Auth (bcrypt) • Pydantic v2 • Multi-Key Failover Pool • Logging  │  │
 │  └─────────────────┬──────────────────────────┬───────────────────────────┬───────────┘  │
 └────────────────────┼──────────────────────────┼───────────────────────────┼──────────────┘
                      │                          │                           │
                      ▼                          ▼                           ▼
        ┌───────────────────────────┐ ┌─────────────────────┐ ┌─────────────────────────────┐
        │    PostgreSQL 16 / Neon   │ │   Qdrant Vector DB  │ │     Groq LPU LLM Engine     │
        │  Relational Storage & ACID│ │ Multi-Vector Store  │ │  Ultra-Low Latency Inference│
        │  • Users & Auth           │ │ • Dense Vectors     │ │  • Query Routing & Rewrite  │
        │  • Knowledge Bases        │ │ • Sparse BM25 Index │ │  • HyDE Generation          │
        │  • Document Metadata      │ │ • Tenant Payloads   │ │  • CRAG Confidence Eval     │
        │  • Conversations & Msgs   │ │ • Payload Filters   │ │  • Grounded Synthesis       │
        └───────────────────────────┘ └─────────────────────┘ └─────────────────────────────┘
```

### System Component Diagram (Mermaid)

```mermaid
graph TB
    subgraph Frontend["User Presentation Layer"]
        UI_Streamlit["Streamlit UI (Port 8501)<br/>• Auth & Session State<br/>• KB & Document Manager<br/>• Multi-Turn Chat & Citations"]
        UI_Web["Modern Glassmorphic Web App<br/>• Standalone Vanilla JS/CSS<br/>• Realtime Stream & Dark Theme"]
    end

    subgraph Backend["FastAPI Application Layer (Port 8000)"]
        API_Gateway["FastAPI Gateway & CORS"]
        Auth_Module["Auth Service (JWT / bcrypt)"]
        Doc_Service["Document Ingestion Service<br/>(PyPDF, python-docx, Chunker)"]
        RAG_Orchestrator["Advanced RAG Pipeline Orchestrator"]
    end

    subgraph RAG_Engine["RAG Retrieval & Generation Core"]
        Router["LLM Query Router"]
        Rewriter["Query Rewriter & HyDE"]
        Hybrid["Hybrid Search (Dense + Sparse BM25)"]
        RRF["Reciprocal Rank Fusion (RRF)"]
        Reranker["Cross-Encoder (ms-marco-MiniLM-L-6-v2)"]
        CRAG["Corrective RAG (CRAG) Evaluator"]
        Generator["Grounded Answer Generator"]
    end

    subgraph Data_Storage["Data & Model Storage"]
        PG[(PostgreSQL / Neon DB<br/>Users, KBs, Docs, Chats)]
        Qdrant[(Qdrant Vector DB<br/>Dense & Sparse Vectors)]
        Groq["Groq LPU Engine<br/>Llama 3.3 70B / Multi-Key Pool"]
        EmbedModel["FastEmbed / BAAI BGE-Small"]
    end

    UI_Streamlit -->|HTTP / JSON| API_Gateway
    UI_Web -->|HTTP / JSON| API_Gateway
    API_Gateway --> Auth_Module
    API_Gateway --> Doc_Service
    API_Gateway --> RAG_Orchestrator

    Doc_Service --> PG
    Doc_Service --> EmbedModel
    EmbedModel --> Qdrant

    RAG_Orchestrator --> Router
    Router --> Rewriter
    Rewriter --> Groq
    Rewriter --> Hybrid
    Hybrid --> Qdrant
    Hybrid --> RRF
    RRF --> Reranker
    Reranker --> CRAG
    CRAG -->|Relevant| Generator
    CRAG -->|Ambiguous| Rewriter
    Generator --> Groq
    RAG_Orchestrator --> PG
```

---

## ⚡ Advanced RAG Pipeline Lifecycle

The query pipeline executes a resilient, multi-stage retrieval flow designed to guarantee high answer fidelity:

```mermaid
flowchart TD
    Start([User Question + History]) --> RouteCheck{Query Router}
    
    RouteCheck -->|Direct Question| Standalone[Pass Standalone Query]
    RouteCheck -->|Follow-up / Ambiguous| Rewrite[Context-Aware Query Rewriter]
    RouteCheck -->|Complex / Abstract| HyDE[HyDE Hypothetical Passage]
    
    Rewrite --> MergeQueries[Unified Query Plan]
    Standalone --> MergeQueries
    HyDE --> MergeQueries
    
    MergeQueries --> SearchParallel{Parallel Hybrid Search}
    
    SearchParallel -->|Dense Path| Dense[BGE-Small-en-v1.5 384d Dense Vector Search]
    SearchParallel -->|Sparse Path| Sparse[BM25 Lexical Keyword Search]
    
    Dense --> RRF[Reciprocal Rank Fusion k=60]
    Sparse --> RRF
    
    RRF --> Candidates[Top 20 Merged Candidate Chunks]
    Candidates --> Rerank[Cross-Encoder Reranker: ms-marco-MiniLM-L-6-v2]
    Rerank --> TopChunks[Top 6-8 High-Scoring Chunks]
    
    TopChunks --> CRAGEval{CRAG Relevance Assessment}
    
    CRAGEval -->|Score >= 0.6: High Relevance| ContextBuild[Build Augmented Grounding Context]
    CRAGEval -->|Score < 0.6 & Retries Left| ExpandQuery[Perform Corrective Query Expansion]
    ExpandQuery --> SearchParallel
    CRAGEval -->|Score < 0.6 & Max Retries Exceeded| Fallback[Grounded Insufficient Context Fallback]
    
    ContextBuild --> LLMGen[Groq LLM Synthesis: Llama 3.3 70B]
    LLMGen --> ParseCitations[Format Answer + Inline Citations]
    Fallback --> ParseCitations
    
    ParseCitations --> SaveMsg[(Persist to PostgreSQL)]
    SaveMsg --> Finish([Return JSON Response to Client])
```

---

## 🚀 Key Features

* 🏢 **True Multi-Tenancy & Data Isolation:** Complete tenant boundaries at DB (PostgreSQL `user_id` foreign keys), vector search (Qdrant `must` payload filters), and physical storage (`uploads/{user_id}/{kb_id}/`).
* 🔀 **Intelligent Query Routing:** LLM-powered router classifies queries dynamically into Direct QA, Coreference-Resolved Query Rewriting, or HyDE passage generation.
* ⚡ **Dense + Sparse Hybrid Search:** Merges dense semantic embeddings (`BAAI/bge-small-en-v1.5`) and sparse lexical representations (`BM25Okapi`) via Reciprocal Rank Fusion ($k=60$).
* 🎯 **Cross-Encoder Precision Reranker:** Evaluates joint query-passage attention with `ms-marco-MiniLM-L-6-v2` to strip noisy or misleading chunks.
* 🛡️ **Self-Correcting RAG (CRAG):** Assesses chunk relevance before synthesis; initiates iterative query expansion if retrieved context is weak.
* 📑 **Verifiable Source Grounding:** Strict grounding prompts prevent hallucination and format verified citations linking directly to file names, page numbers, and exact chunk snippets.
* 🔑 **Multi-Key Groq Failover Pool:** Intelligent key rotation and automatic failover across multiple API keys to prevent rate-limit interruptions.
* 🎨 **Dual Frontend Options:**
  - **Streamlit Enterprise UI:** Multi-page dashboard with authentication, Knowledge Base CRUD, document drag-and-drop, interactive chat, and live RAG telemetry metrics.
  - **Modern Glassmorphism Web App:** Sleek standalone UI with interactive animations, token usage meters, and real-time response rendering.
* 🧪 **Automated Testing Suite:** 32 comprehensive unit and integration tests covering auth, document ingestion, Qdrant vectors, hybrid search, Reranking, CRAG, and chat workflows.

---

## 🛠️ Technology Stack

| Layer | Technology | Details / Rationale |
|---|---|---|
| **Backend Framework** | [FastAPI](https://fastapi.tiangolo.com) | Python 3.12, Async REST, Pydantic v2 schemas, OpenAPI docs |
| **Frontend Framework** | [Streamlit](https://streamlit.io) & Vanilla HTML5/CSS3/JS | Multi-page Streamlit 1.38+ app + Modern standalone web app |
| **LLM Inference** | [Groq Cloud LPU](https://groq.com) | Ultra-fast inference with `llama-3.3-70b-versatile` / `openai/gpt-oss-120b` |
| **Dense Embeddings** | [FastEmbed](https://qdrant.github.io/fastembed/) | `BAAI/bge-small-en-v1.5` (384 dims, ONNX CPU/GPU runtime) |
| **Sparse Retrieval** | BM25 Engine | Custom alphanumeric BM25Okapi lexical index |
| **Reranking** | [Sentence Transformers](https://www.sbert.net) | Cross-Encoder `cross-encoder/ms-marco-MiniLM-L-6-v2` |
| **Vector Database** | [Qdrant](https://qdrant.tech) | Persistent vector & payload index (Cloud managed or Docker, with in-memory fallback) |
| **Relational Database** | [PostgreSQL 16](https://www.postgresql.org) / [Neon](https://neon.tech) | SQLAlchemy 2.0 ORM, Alembic schema migrations, UUID keys |
| **Security & Auth** | OAuth2 Bearer + JWT | Password hashing via `bcrypt`, JSON Web Tokens (HS256) |
| **Document Parsers** | `pypdf`, `python-docx` | Robust text extraction across `.pdf`, `.docx`, `.txt`, `.md` |
| **Testing** | `pytest`, `httpx`, `pytest-asyncio` | 32 unit and end-to-end integration tests |
| **Orchestration** | Docker & Docker Compose | Multi-container setup with healthchecks and volume mapping |

---

## 🗄️ Database Schema & Entity Relationships

```mermaid
erDiagram
    USERS ||--o{ KNOWLEDGE_BASES : "owns"
    USERS ||--o{ CONVERSATIONS : "initiates"
    KNOWLEDGE_BASES ||--o{ DOCUMENTS : "contains"
    KNOWLEDGE_BASES ||--o{ CONVERSATIONS : "scopes"
    CONVERSATIONS ||--o{ MESSAGES : "includes"

    USERS {
        uuid id PK
        string email UK
        string username UK
        string hashed_password
        boolean is_active
        boolean is_superuser
        timestamp created_at
        timestamp updated_at
    }

    KNOWLEDGE_BASES {
        uuid id PK
        string name
        string description
        uuid user_id FK
        timestamp created_at
        timestamp updated_at
    }

    DOCUMENTS {
        uuid id PK
        string filename
        string original_filename
        string content_type
        integer file_size
        string status
        string error_message
        integer chunk_count
        uuid knowledge_base_id FK
        uuid user_id FK
        timestamp created_at
        timestamp updated_at
    }

    CONVERSATIONS {
        uuid id PK
        string title
        uuid user_id FK
        uuid knowledge_base_id FK
        timestamp created_at
        timestamp updated_at
    }

    MESSAGES {
        uuid id PK
        uuid conversation_id FK
        string role
        text content
        json citations
        json message_metadata
        timestamp created_at
    }
```

---

## 📂 Project Directory Structure

```text
Advanced-RAG-Chatbot/
├── backend/
│   ├── alembic/                         # Database migrations
│   │   ├── versions/                    # Migration version scripts
│   │   ├── env.py                       # Alembic environment config
│   │   └── script.py.mako
│   ├── app/
│   │   ├── api/                         # API routers and endpoints
│   │   │   ├── v1/
│   │   │   │   ├── endpoints/
│   │   │   │   │   ├── auth.py          # User registration & login
│   │   │   │   │   ├── users.py         # User profile routes
│   │   │   │   │   ├── knowledge_bases.py # KB CRUD operations
│   │   │   │   │   ├── documents.py     # Ingestion & upload routes
│   │   │   │   │   └── chat.py          # Conversations & RAG chat
│   │   │   │   └── router.py            # Central v1 router aggregator
│   │   │   └── deps.py                  # Dependency injection (Auth, DB)
│   │   ├── core/                        # Application configuration & security
│   │   │   ├── config.py                # Pydantic BaseSettings (.env loading)
│   │   │   ├── exceptions.py            # Custom exception classes & handlers
│   │   │   ├── logging.py               # Structured logging setup
│   │   │   └── security.py              # JWT token generation & bcrypt hashing
│   │   ├── db/                          # SQLAlchemy database session & base
│   │   │   ├── base.py                  # Declarative base & GUID type decorator
│   │   │   └── session.py               # DB engine & session factory
│   │   ├── models/                      # SQLAlchemy ORM database models
│   │   │   ├── user.py
│   │   │   ├── knowledge_base.py
│   │   │   ├── document.py
│   │   │   ├── conversation.py
│   │   │   └── message.py
│   │   ├── schemas/                     # Pydantic validation & response schemas
│   │   │   ├── auth.py
│   │   │   ├── user.py
│   │   │   ├── knowledge_base.py
│   │   │   ├── document.py
│   │   │   ├── chat.py
│   │   │   ├── rag.py
│   │   │   └── common.py
│   │   ├── services/                    # Business logic services
│   │   │   ├── auth_service.py
│   │   │   ├── kb_service.py
│   │   │   ├── document_service.py
│   │   │   ├── llm_service.py           # Multi-key Groq pool & fallback
│   │   │   └── vector_service.py        # Qdrant client & collection management
│   │   ├── rag/                         # Core Advanced RAG modules
│   │   │   ├── parser.py                # Multi-format document parser
│   │   │   ├── chunker.py               # Recursive text chunking with overlap
│   │   │   ├── embeddings.py            # FastEmbed dense vector generator
│   │   │   ├── sparse.py                # BM25 lexical token indexer
│   │   │   ├── hybrid_search.py         # Dense + Sparse search + RRF merger
│   │   │   ├── reranker.py              # Cross-Encoder precision reranker
│   │   │   ├── router.py                # LLM query classifier
│   │   │   ├── rewriter.py              # Contextual query rewriter
│   │   │   ├── hyde.py                  # Hypothetical Document Embeddings
│   │   │   ├── corrective.py            # CRAG relevance evaluator & expansion
│   │   │   ├── generator.py             # Grounded prompt answer generator
│   │   │   └── pipeline.py              # Complete end-to-end RAG orchestrator
│   │   └── main.py                      # FastAPI application entrypoint
│   ├── tests/                           # Pytest automated test suite
│   │   ├── conftest.py                  # Test database fixtures & client mocks
│   │   ├── test_auth.py                 # User auth & JWT tests
│   │   ├── test_kb.py                   # Knowledge base CRUD tests
│   │   ├── test_documents.py            # Document parsing & chunking tests
│   │   ├── test_rag_pipeline.py         # Vector search, Rerank & CRAG tests
│   │   └── test_chat.py                 # Chat API & citation tests
│   ├── alembic.ini                      # Alembic CLI configuration
│   ├── Dockerfile                       # Backend container definition
│   └── requirements.txt                 # Backend Python dependencies
│
├── frontend/
│   ├── pages/                           # Streamlit multi-page views
│   │   ├── 1_📚_Knowledge_Bases.py      # Knowledge Base management UI
│   │   ├── 2_📄_Documents.py            # Document upload & status table
│   │   └── 3_💬_Chat.py                 # Interactive chat & citations view
│   ├── components/                      # Reusable UI widgets
│   │   ├── auth.py                      # Login / Registration widget
│   │   ├── citations.py                 # Formatted citation pill renderer
│   │   └── sidebar.py                   # Sidebar KB switcher & nav
│   ├── services/
│   │   └── api_client.py                # HTTP client wrapper for Backend API
│   ├── app.py                           # Streamlit root application
│   ├── Dockerfile                       # Frontend container definition
│   └── requirements.txt                 # Frontend Python dependencies
│
├── index.html                           # Modern Standalone Glassmorphic UI
├── style.css                            # Modern Web UI styling & theme
├── script.js                            # Modern Web UI state & API bridge
├── docker-compose.yml                   # 4-Service container orchestration
├── .env.example                         # Example environment variables template
├── .gitignore                           # Git ignore rules
├── ARCHITECTURE.md                      # Comprehensive architectural specification
├── PROJECT_STATE.md                     # Current project state & roadmap
└── README.md                            # Complete project guide & documentation
```

---

## 📦 Step-by-Step Setup Guide

### 1. Prerequisites
Ensure you have the following installed on your machine:
* **Python 3.12+** ([python.org](https://www.python.org/downloads/))
* **Git** ([git-scm.com](https://git-scm.com/))
* *(Optional)* **Docker & Docker Compose** ([docker.com](https://www.docker.com/products/docker-desktop/))

---

### 2. Clone the Repository
```bash
git clone https://github.com/your-username/Advanced-RAG-Chatbot.git
cd "Advanced RAG Chatbot"
```

---

### 3. Configure Environment Variables
Create your local `.env` configuration by copying the template:

```bash
# On Windows (PowerShell):
Copy-Item .env.example .env

# On Linux / macOS:
cp .env.example .env
```

Open `.env` in your editor and configure your credentials:

```ini
# --- Mandatory Credentials ---
GROQ_API_KEY=gsk_your_groq_api_key_here

# --- Database Selection ---
# Option A: Cloud Neon PostgreSQL / Self-hosted Postgres (Recommended for Production)
DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/rag_knowledge_db

# Option B: SQLite (Quick Local Development with zero setup)
# DATABASE_URL=sqlite:///./rag_app.db

# --- Vector Database Selection ---
# Option A: Qdrant Cloud Cluster / Self-hosted Qdrant (Port 6333)
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_API_KEY=

# Option B: In-Memory Qdrant (Automatic fallback if QDRANT_HOST is empty or unreachable)
# QDRANT_HOST=memory
```

> [!TIP]
> If you don't have local PostgreSQL or Qdrant running, you can use **SQLite** (`sqlite:///./rag_app.db`) and **In-Memory Qdrant** (`QDRANT_HOST=memory`) for instant testing without installing any external database services.

---

### 4. Create & Activate Virtual Environment

<details open>
<summary><b>Windows (PowerShell)</b></summary>

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```
</details>

<details>
<summary><b>Windows (Command Prompt / CMD)</b></summary>

```cmd
python -m venv .venv
.venv\Scripts\activate.bat
```
</details>

<details>
<summary><b>macOS / Linux</b></summary>

```bash
python3 -m venv .venv
source .venv/bin/activate
```
</details>

---

### 5. Install Dependencies
Install all backend and frontend dependencies:

```bash
pip install --upgrade pip
pip install -r backend/requirements.txt -r frontend/requirements.txt
```

---

### 6. Run Database Migrations (Optional / If using PostgreSQL)
If using PostgreSQL, apply the initial schema migrations:

```bash
alembic upgrade head
```

---

### 7. Run the Automated Test Suite
Verify that your environment and all RAG pipeline components are fully operational:

```bash
pytest backend/tests -v
```
*(All 32 tests should execute and pass).*

---

### 8. Launch the Application

#### Option A: Unified Launcher (Frontend Web UI + Backend API) — Recommended
Run the complete application with a single command:
```bash
python run.py
```
*(or run via uvicorn directly)*:
```bash
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

* 🖥️ **Frontend Web UI:** [http://localhost:8000](http://localhost:8000)
* 📖 **Interactive Swagger UI Docs:** [http://localhost:8000/api/v1/docs](http://localhost:8000/api/v1/docs)
* 📄 **ReDoc Documentation:** [http://localhost:8000/api/v1/redoc](http://localhost:8000/api/v1/redoc)
* 🩺 **System Health Check:** [http://localhost:8000/health](http://localhost:8000/health)

#### Option B: Streamlit Multi-Page Dashboard (Optional)
If you prefer running the multi-page Streamlit dashboard:
```bash
streamlit run frontend/app.py
```
* 🖥️ **Streamlit Web UI:** [http://localhost:8501](http://localhost:8501)


---

## 🐳 Docker Compose Quickstart

To run the complete production stack (**FastAPI Backend**, **Streamlit Frontend**, **PostgreSQL 16**, and **Qdrant Vector DB**) with a single command:

```bash
docker compose up --build
```

### Container Endpoints:
* 🖥️ **Streamlit UI:** [http://localhost:8501](http://localhost:8501)
* ⚡ **FastAPI API & Swagger Docs:** [http://localhost:8000/api/v1/docs](http://localhost:8000/api/v1/docs)
* 🎯 **Qdrant Vector Web Dashboard:** [http://localhost:6333/dashboard](http://localhost:6333/dashboard)

To stop the containers:
```bash
docker compose down
```

---

## 🔑 Environment Variables Reference

| Variable | Default Value | Description |
|---|---|---|
| `APP_NAME` | `Enterprise AI Knowledge Assistant` | Name of the application displayed in UI/Docs |
| `APP_ENV` | `development` | Environment mode (`development`, `production`, `test`) |
| `DEBUG` | `true` | Enable verbose error responses and debug logging |
| `API_V1_PREFIX` | `/api/v1` | URL prefix for all REST API endpoints |
| `SECRET_KEY` | `enterprise-super-secret-key...` | Cryptographic secret for signing sessions |
| `DATABASE_URL` | `postgresql+psycopg2://...` | PostgreSQL or SQLite connection URI |
| `JWT_SECRET_KEY` | `enterprise-super-secret-jwt...` | Secret key for signing JWT tokens |
| `JWT_ALGORITHM` | `HS256` | JWT signing algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `1440` | Token expiration duration in minutes (24h) |
| `GROQ_API_KEY` | `gsk_...` | Primary Groq API Key for LPU inference |
| `GROQ_API_KEYS` | `["gsk_...","gsk_..."]` | JSON array of fallback Groq keys for multi-key pool |
| `GROQ_MODEL` | `llama-3.3-70b-versatile` | LLM model for final grounded answer generation |
| `GROQ_FAST_MODEL` | `llama-3.1-8b-instant` | Lightweight LLM for fast query rewriting and HyDE |
| `EMBEDDING_MODEL` | `BAAI/bge-small-en-v1.5` | FastEmbed dense embedding model name |
| `EMBEDDING_DIMENSION` | `384` | Dimensionality of dense embedding vectors |
| `QDRANT_HOST` | `localhost` | Qdrant host URL (`localhost`, cloud URL, or `memory`) |
| `QDRANT_PORT` | `6333` | Qdrant HTTP REST port |
| `QDRANT_COLLECTION_NAME` | `enterprise_knowledge_base`| Name of vector collection in Qdrant |
| `CHUNK_SIZE` | `800` | Target characters per chunk during recursive splitting |
| `CHUNK_OVERLAP` | `150` | Overlap character count between consecutive chunks |
| `DENSE_TOP_K` | `20` | Candidate chunk count retrieved from dense vector search |
| `SPARSE_TOP_K` | `20` | Candidate chunk count retrieved from BM25 sparse search |
| `RERANK_TOP_K` | `8` | Chunk count retained after cross-encoder scoring |
| `RERANKER_MODEL` | `cross-encoder/ms-marco-MiniLM-L-6-v2` | Cross-Encoder model name |
| `RELEVANCE_THRESHOLD` | `0.6` | CRAG relevance cutoff score before query retry |
| `MAX_RETRIEVAL_ATTEMPTS` | `2` | Maximum retry attempts for corrective query expansion |

---

## 📡 REST API Reference

The FastAPI server provides standard OpenAPI 3.1 documentation at `/api/v1/docs`.

### 1. Authentication & Users
| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `POST` | `/api/v1/auth/register` | Register a new user account | ❌ No |
| `POST` | `/api/v1/auth/login` | Authenticate with username/password, get JWT token | ❌ No |
| `GET` | `/api/v1/users/me` | Retrieve profile of the currently logged-in user | 🔒 Yes |

### 2. Knowledge Bases
| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `POST` | `/api/v1/knowledge-bases/` | Create a new isolated knowledge base | 🔒 Yes |
| `GET` | `/api/v1/knowledge-bases/` | List all knowledge bases owned by current user | 🔒 Yes |
| `GET` | `/api/v1/knowledge-bases/{kb_id}` | Retrieve specific knowledge base details & stats | 🔒 Yes |
| `PUT` | `/api/v1/knowledge-bases/{kb_id}` | Update knowledge base title or description | 🔒 Yes |
| `DELETE` | `/api/v1/knowledge-bases/{kb_id}` | Delete knowledge base and cascade-delete all docs & vectors | 🔒 Yes |

### 3. Documents
| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `POST` | `/api/v1/documents/upload` | Upload `.pdf`, `.docx`, `.txt`, `.md` files to a KB | 🔒 Yes |
| `GET` | `/api/v1/documents/kb/{kb_id}` | List all documents and ingestion statuses in a KB | 🔒 Yes |
| `GET` | `/api/v1/documents/{doc_id}` | Get status and chunk count of a specific document | 🔒 Yes |
| `DELETE` | `/api/v1/documents/{doc_id}` | Delete document file, DB record, and Qdrant points | 🔒 Yes |

### 4. Conversations & RAG Chat
| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `POST` | `/api/v1/chat/conversations` | Create a new conversation thread scoped to a KB | 🔒 Yes |
| `GET` | `/api/v1/chat/conversations?kb_id={id}` | List all conversation threads in a knowledge base | 🔒 Yes |
| `GET` | `/api/v1/chat/conversations/{id}/messages`| Retrieve all messages and citations in a conversation | 🔒 Yes |
| `POST` | `/api/v1/chat/message` | Execute Advanced RAG pipeline and return answer + citations | 🔒 Yes |
| `DELETE` | `/api/v1/chat/conversations/{id}` | Delete conversation thread and its message history | 🔒 Yes |

---

## 🌐 Cloud Deployment Guide

| Service Component | Recommended Host | Free / Low-Cost Tier Notes |
|---|---|---|
| **Frontend UI** | [Streamlit Community Cloud](https://streamlit.io/cloud) | 100% Free. Connects to the public FastAPI backend URL via `API_BASE_URL`. |
| **Backend Server** | [Render](https://render.com) / [Railway](https://railway.app) / [Koyeb](https://www.koyeb.com) | Free/hobby web service tiers. Set environment variables in the cloud dashboard. |
| **Relational Database** | [Neon Postgres](https://neon.tech) / [Supabase](https://supabase.com) | Serverless PostgreSQL with generous free storage (0.5GB - 1GB) and instant branching. |
| **Vector Database** | [Qdrant Cloud](https://cloud.qdrant.io) | Permanent Free 1GB managed cluster (no credit card required). |
| **LLM Inference** | [Groq Cloud Console](https://console.groq.com) | Free Developer Tier with generous rate limits and ultra-fast inference. |

---

## ❓ Troubleshooting & FAQs

<details>
<summary><b>1. What happens if Qdrant or PostgreSQL is not installed locally?</b></summary>
The system is built with resilience fallbacks:
- If Qdrant is not reachable at the specified host/port, the `VectorService` automatically initializes a local **In-Memory Qdrant instance** (`location=":memory:"`).
- If you don't have PostgreSQL installed, change `DATABASE_URL` in `.env` to `sqlite:///./rag_app.db` for instant single-file relational storage.
</details>

<details>
<summary><b>2. How does the system prevent LLM hallucinations?</b></summary>
The system enforces hallucination resistance through 3 layers:
1. **Cross-Encoder Reranking** eliminates irrelevant chunks that could lead the LLM astray.
2. **Corrective RAG (CRAG)** evaluates context relevance before answer generation. If no retrieved chunks exceed the relevance threshold, the system provides a clear "insufficient context" notice instead of fabricating facts.
3. **Strict Grounding System Prompt** instructs the LLM to only answer based on provided context and format explicit bracketed citations `[Doc: filename, Page: X]`.
</details>

<details>
<summary><b>3. Why use Hybrid Search (Dense + Sparse) instead of Dense-only?</b></summary>
Dense vector embeddings excel at capturing conceptual meaning and synonyms, but often fail on exact alphanumeric queries like error codes (`ERR_404_AUTH`), version numbers (`v1.12.0`), model numbers, or domain-specific acronyms. BM25 sparse search ensures exact keyword matches are never missed, and Reciprocal Rank Fusion (RRF) blends them harmoniously.
</details>

---

## 📄 License & Contributing

Distributed under the **MIT License**. Contributions, bug reports, and feature requests are welcome via GitHub Issues and Pull Requests.

<div align="center">
  <sub>Built with ❤️ • Star ⭐ the repository if you found this helpful!</sub>
</div>
