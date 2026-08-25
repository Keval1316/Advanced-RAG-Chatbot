# 🧠 Enterprise AI Knowledge Assistant

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg?style=flat&logo=FastAPI&logoColor=white)](https://fastapi.tiangolo.com)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.38+-FF4B4B.svg?style=flat&logo=Streamlit&logoColor=white)](https://streamlit.io)
[![Qdrant](https://img.shields.io/badge/Qdrant-Vector%20DB-DC2626.svg?style=flat&logo=qdrant&logoColor=white)](https://qdrant.tech)
[![Groq](https://img.shields.io/badge/Groq-Llama%203.3%2070B-F97316.svg?style=flat)](https://groq.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1.svg?style=flat&logo=postgresql&logoColor=white)](https://www.postgresql.org)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED.svg?style=flat&logo=docker&logoColor=white)](https://www.docker.com)
[![Pytest](https://img.shields.io/badge/Tests-32%2F32%20Passed-22C55E.svg?style=flat&logo=pytest&logoColor=white)](https://pytest.org)

> A production-grade, multi-tenant **Advanced Retrieval-Augmented Generation (RAG)** platform featuring **Intelligent Query Routing**, **Context-Aware Query Rewriting**, **HyDE**, **Dense + Sparse Hybrid Search (BM25 + BGE)**, **Reciprocal Rank Fusion (RRF)**, **Cross-Encoder Reranking**, **Corrective RAG (CRAG)**, and **Source-Grounded Citations** powered by the **Groq LPU LLM Engine**.

---

## 🏗️ System Architecture

```text
                    ┌────────────────────────────────────────────────────────┐
                    │                   Streamlit Frontend                   │
                    │      (Auth, KB Management, Doc Upload, Chat & Citations)│
                    └───────────────────────────┬────────────────────────────┘
                                                │ REST API (JSON / Multipart)
                                                ▼
                    ┌────────────────────────────────────────────────────────┐
                    │                   FastAPI Backend                      │
                    │   (JWT Auth, Dependency Injection, Validation, Router) │
                    └───────┬───────────────────┬────────────────────┬───────┘
                            │                   │                    │
           ┌────────────────▼────────┐ ┌────────▼─────────┐ ┌────────▼────────┐
           │   PostgreSQL Metadata   │ │   Qdrant Vector  │ │  Groq LLM Engine│
           │  (Users, KBs, Docs,     │ │ (Dense Embeddings│ │(Llama 3.3 70B   │
           │   Conversations, Msgs)  │ │ + Sparse Vectors)│ │ Query Rewrite,  │
           └─────────────────────────┘ └──────────────────┘ │ HyDE, Answers) │
                                                            └─────────────────┘
```

---

## ⚡ Advanced RAG Pipeline Lifecycle

```text
                         USER QUESTION + CONVERSATION HISTORY
                                          │
                                          ▼
                                    QUERY ROUTER
                                          │
                   ┌──────────────────────┼──────────────────────┐
                   ▼                      ▼                      ▼
             QUERY REWRITE              HYDE                 DIRECT QA
         (Resolve coreferences)  (Hypothetical passage) (Self-contained query)
                   │                      │                      │
                   └──────────────────────┼──────────────────────┘
                                          │
                                          ▼
                                    HYBRID SEARCH
                                          │
                            ┌─────────────┴─────────────┐
                            ▼                           ▼
                       DENSE SEARCH               SPARSE SEARCH
                   (BAAI/bge-small-en-v1.5)        (BM25 Lexical)
                            │                           │
                            └─────────────┬─────────────┘
                                          ▼
                            RECIPROCAL RANK FUSION (RRF)
                                          ▼
                          CANDIDATE CHUNKS (TOP 20)
                                          │
                                          ▼
                              CROSS-ENCODER RERANKER
                       (ms-marco-MiniLM-L-6-v2, TOP 8)
                                          │
                                          ▼
                            CORRECTIVE RAG (CRAG)
                           (Relevance Assessment)
                                          │
                   ┌──────────────────────┴──────────────────────┐
                   ▼ (Context Relevant)                          ▼ (Context Poor)
           GENERATE ANSWER                                RETRY / FALLBACK
                   │                                             │ (if max retries reached)
                   │                                             ▼
                   │                                GROUNDED INSUFFICIENT NOTICE
                   └──────────────────────┬──────────────────────┘
                                          ▼
                               GROQ LLM GENERATION
                             (Strict Grounding Prompt)
                                          ▼
                             ANSWER + REAL CITATIONS
```

---

## 🚀 Key Features

* **Multi-Tenant Isolation:** Complete isolation at DB (PostgreSQL tenant IDs), Vector DB (Qdrant payload filters), and physical storage.
* **Hybrid Search with RRF:** Merges dense semantic embeddings (`bge-small-en-v1.5`) and sparse lexical matching (`BM25`) using Reciprocal Rank Fusion ($k=60$).
* **Cross-Encoder Precision:** Re-scores retrieved candidate chunks with cross-attention (`ms-marco-MiniLM-L-6-v2`) to eliminate false-positive chunks.
* **Self-Correcting RAG (CRAG):** Evaluates context relevance before answering, executing targeted query expansion if relevance is insufficient.
* **Grounded Citations:** Structured citations mapping claims back to document filenames, page numbers, and exact chunk snippets.
* **Modern Streamlit UI:** Multi-turn chat interface, conversation switcher, live RAG telemetry inspection, document manager, and knowledge base manager.
* **Production Stack:** Pydantic v2 schemas, Alembic migrations, JWT authentication, and Docker Compose orchestration.

---

## 🛠️ Technology Stack

| Layer | Component | Choice |
|---|---|---|
| **Frontend** | Interactive Web UI | Streamlit 1.38+ (Custom Glassmorphism Dark Theme) |
| **Backend** | REST API Server | FastAPI, Pydantic v2, Uvicorn |
| **LLM Provider** | Inference Engine | Groq API (`llama-3.3-70b-versatile` / `llama-3.1-8b-instant`) |
| **Embeddings** | Dense Vector Model | `BAAI/bge-small-en-v1.5` (384 dim via FastEmbed) |
| **Sparse Retrieval** | Lexical Index | BM25Okapi Engine with custom alphanumeric tokenization |
| **Reranker** | Cross-Encoder Model | `cross-encoder/ms-marco-MiniLM-L-6-v2` |
| **Vector DB** | Vector & Payload Index | Qdrant (Persistent + In-Memory Fallback) |
| **Relational DB** | Metadata & Conversation Store | PostgreSQL 16 with SQLAlchemy 2.0 & Alembic |
| **Security** | Authentication | OAuth2 Password Bearer, JWT (HS256), bcrypt |
| **Testing** | Automated Test Suite | Pytest, Pytest-Asyncio, HTTPX (32 Unit & Integration Tests) |
| **Container** | Containerization | Docker & Docker Compose |

---

## 📦 Quickstart & Local Setup

### 1. Prerequisites
- Python 3.12+ installed
- Git installed
- Docker & Docker Compose (optional, for full containerized stack)

### 2. Clone and Setup Environment
```bash
git clone https://github.com/Keval1316/Advanced-RAG-Chatbot.git
cd "Advanced RAG Chatbot"

# Create and activate virtual environment
python -m venv .venv
# On Windows (PowerShell):
.venv\Scripts\Activate.ps1
# On Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt -r frontend/requirements.txt
```

### 3. Configure Environment Variables
Copy `.env.example` to `.env` and provide your Groq API key:
```bash
cp .env.example .env
```
Edit `.env`:
```ini
GROQ_API_KEY=gsk_your_actual_groq_api_key_here
```

### 4. Run the Full Test Suite
```bash
pytest backend/tests -v
```
*(All 32 tests will run and pass).*

### 5. Launch Locally
Start the FastAPI Backend:
```bash
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

In a second terminal, launch the Streamlit Frontend:
```bash
streamlit run frontend/app.py
```
Open **http://localhost:8501** in your browser.

---

## 🐳 Running with Docker Compose

To start the complete multi-service stack (FastAPI, Streamlit, PostgreSQL, Qdrant) with a single command:
```bash
docker compose up --build
```
Access points:
- **Streamlit Web UI:** [http://localhost:8501](http://localhost:8501)
- **FastAPI OpenAPI Docs:** [http://localhost:8000/api/v1/docs](http://localhost:8000/api/v1/docs)
- **Qdrant Dashboard:** [http://localhost:6333/dashboard](http://localhost:6333/dashboard)

---

## 🌐 Low-Cost / Free Cloud Deployment

| Service | Recommended Host | Free / Low-Cost Tier Notes |
|---|---|---|
| **Frontend** | [Streamlit Community Cloud](https://streamlit.io/cloud) | 100% Free; Connects directly to backend API URL |
| **Backend** | [Render](https://render.com) / [Railway](https://railway.app) / [Koyeb](https://www.koyeb.com) | Free web service tier; Set `.env` platform secrets |
| **Vector DB** | [Qdrant Cloud](https://cloud.qdrant.io) | Permanent Free 1GB Managed Cluster |
| **Database** | [Neon Postgres](https://neon.tech) / [Supabase](https://supabase.com) | Free Serverless PostgreSQL (0.5GB storage, autoscaling) |
| **LLM** | [Groq Cloud Console](https://console.groq.com) | Free Developer Tier with generous rate limits |

---

## 🛡️ License & Contributing
MIT License. Built for enterprise AI engineering architectures.
