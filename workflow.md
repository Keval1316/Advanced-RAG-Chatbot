# Advanced RAG Chatbot - Complete Code-Execution Workflow

> This document was created by inspecting every source file in this project.  
> Every file path, function name, class name, and execution step described below  
> is verified against the actual code. Nothing has been assumed.

---

## Table of Contents

1. [Project Structure](#1-project-structure)
2. [Technology Stack (Discovered from Code)](#2-technology-stack-discovered-from-code)
3. [Two Application Entry Points](#3-two-application-entry-points)
4. [Application Startup - FastAPI Path](#4-application-startup-fastapi-path)
5. [Frontend UI - Two Separate UIs](#5-frontend-ui--two-separate-uis)
6. [Authentication Flow](#6-authentication-flow)
7. [Knowledge Base and Document Ingestion Flow](#7-knowledge-base-and-document-ingestion-flow)
8. [Complete Chat Message Flow](#8-complete-chat-message-flow)
9. [Advanced RAG Pipeline - Step by Step](#9-advanced-rag-pipeline--step-by-step)
10. [LLM Service - How the Model Is Called](#10-llm-service--how-the-model-is-called)
11. [Prompt Construction](#11-prompt-construction)
12. [Conversation Memory Behavior](#12-conversation-memory-behavior)
13. [Response Flow Back to the User](#13-response-flow-back-to-the-user)
14. [Error Handling](#14-error-handling)
15. [Data Objects - What Flows Through the System](#15-data-objects--what-flows-through-the-system)
16. [Database Layer](#16-database-layer)
17. [Vector Database (Qdrant) Layer](#17-vector-database-qdrant-layer)
18. [Complete End-to-End Example](#18-complete-end-to-end-example)
19. [Master Execution Diagram](#19-master-execution-diagram)
20. [File-Level Workflow Map](#20-file-level-workflow-map)
21. [Interview Explanation](#21-interview-explanation)

---

## 1. Project Structure

```
Advanced RAG Chatbot/
|
|-- run.py                         <- PRIMARY entry point (FastAPI + Uvicorn)
|-- app.py                         <- ALTERNATIVE entry point (Gradio UI, no auth)
|
|-- backend/
|   +-- app/
|       |-- main.py                <- FastAPI app factory + static file server
|       |-- api/
|       |   |-- deps.py            <- JWT auth dependency injection
|       |   +-- v1/
|       |       |-- router.py      <- Registers all endpoint routers under /api/v1
|       |       +-- endpoints/
|       |           |-- auth.py    <- POST /auth/register, /auth/login
|       |           |-- chat.py    <- POST /chat/message (core chat endpoint)
|       |           |-- documents.py   <- POST /documents/upload
|       |           |-- knowledge_bases.py <- CRUD for knowledge bases
|       |           |-- users.py   <- GET /users/me
|       |           +-- health.py  <- GET /health
|       |-- core/
|       |   |-- config.py          <- Pydantic Settings, reads from .env
|       |   |-- exceptions.py      <- Custom exception classes + FastAPI handlers
|       |   |-- guardrails.py      <- Input safety filter (regex blacklist)
|       |   |-- logging.py         <- Structlog setup
|       |   +-- security.py        <- JWT create/decode, bcrypt hashing
|       |-- db/
|       |   |-- base.py            <- SQLAlchemy DeclarativeBase, GUID type
|       |   +-- session.py         <- Engine, SessionLocal, get_db()
|       |-- models/
|       |   |-- user.py            <- User ORM model
|       |   |-- knowledge_base.py  <- KnowledgeBase ORM model
|       |   |-- document.py        <- Document ORM model
|       |   |-- conversation.py    <- Conversation ORM model
|       |   +-- message.py         <- Message ORM model (stores chat history)
|       |-- schemas/
|       |   |-- chat.py            <- SendMessageRequest, SendMessageResponse, etc.
|       |   |-- rag.py             <- ScoredChunk, Citation, ChatResponse
|       |   |-- document.py        <- ChunkMetadata, DocumentResponse
|       |   +-- common.py          <- APIResponse[T] wrapper
|       |-- services/
|       |   |-- auth_service.py    <- register/authenticate user
|       |   |-- chat_service.py    <- conversation + message CRUD + RAG trigger
|       |   |-- document_service.py <- file save, parse, chunk, index pipeline
|       |   |-- kb_service.py      <- knowledge base CRUD
|       |   |-- llm_service.py     <- Groq API client pool, generate/generate_chat
|       |   +-- vector_service.py  <- Qdrant client, upsert, dense_search
|       +-- rag/
|           |-- pipeline.py        <- AdvancedRAGPipeline.execute() — orchestrator
|           |-- router.py          <- QueryRouter — DIRECT_QA / REWRITE / HYDE
|           |-- rewriter.py        <- QueryRewriter — reformulates follow-up queries
|           |-- hyde.py            <- HyDEGenerator — generates hypothetical passages
|           |-- hybrid_search.py   <- HybridSearchService — dense + sparse + RRF
|           |-- sparse.py          <- BM25Index — pure-Python BM25 implementation
|           |-- embeddings.py      <- EmbeddingService — FastEmbed bge-small-en-v1.5
|           |-- reranker.py        <- CrossEncoderReranker — ms-marco-MiniLM-L-6-v2
|           |-- corrective.py      <- CorrectiveRAG — LLM relevance evaluator
|           |-- generator.py       <- AnswerGenerator — grounded answer + citations
|           |-- chunker.py         <- RecursiveChunker — splits pages into chunks
|           +-- parser.py          <- DocumentParser — PDF/DOCX/TXT extraction
|
|-- frontend/                      <- Streamlit UI (optional, port 8501)
|   |-- app.py                     <- Main Streamlit app, navigation router
|   |-- services/api_client.py     <- HTTP client wrapper for backend REST API
|   +-- components/
|       |-- auth.py                <- Login/Register forms
|       |-- sidebar.py             <- KB selector, conversation list, navigation
|       +-- citations.py           <- Source citations + RAG telemetry display
|
|-- index.html                     <- Pure HTML/JS frontend (served at /)
|-- script.js                      <- Full chat logic for HTML frontend
|-- style.css                      <- Styles for HTML frontend
|-- .env / .env.example            <- All configuration values
+-- requirements.txt               <- All Python dependencies
```

---

## 2. Technology Stack (Discovered from Code)

| Component | Technology | Source File |
|---|---|---|
| Web Framework | FastAPI | `backend/app/main.py` |
| ASGI Server | Uvicorn | `run.py` |
| LLM Provider | Groq API (groq Python SDK) | `backend/app/services/llm_service.py` |
| LLM Models | `openai/gpt-oss-20b`, `openai/gpt-oss-120b`, `groq/compound-mini`, `groq/compound`, `qwen/qwen3.6-27b` | `backend/app/services/llm_service.py` |
| Dense Embeddings | `BAAI/bge-small-en-v1.5` via `fastembed.TextEmbedding` (384 dims) | `backend/app/rag/embeddings.py` |
| Vector Database | Qdrant (remote or in-memory fallback) | `backend/app/services/vector_service.py` |
| Sparse Search | Pure-Python BM25 (no external library) | `backend/app/rag/sparse.py` |
| Cross-Encoder Reranker | `Xenova/ms-marco-MiniLM-L-6-v2` via FastEmbed; fallback: sentence-transformers | `backend/app/rag/reranker.py` |
| Relational Database | SQLite (default) or PostgreSQL via SQLAlchemy | `backend/app/db/session.py` |
| ORM | SQLAlchemy 2.x | `backend/app/db/base.py` |
| Auth | JWT (python-jose) + bcrypt | `backend/app/core/security.py` |
| Streamlit UI | Streamlit (optional, port 8501) | `frontend/app.py` |
| Gradio UI | Gradio (HuggingFace Spaces, no auth) | `app.py` |
| HTML/JS UI | Pure HTML + Vanilla JS | `index.html`, `script.js` |
| PDF Parser | `pypdf.PdfReader` | `backend/app/rag/parser.py` |
| DOCX Parser | `python-docx` | `backend/app/rag/parser.py` |
| Config | `pydantic-settings` reading from `.env` | `backend/app/core/config.py` |

---

## 3. Two Application Entry Points

### Entry Point A: `run.py` — FastAPI Full-Stack Server

```
python run.py
```

**File:** `run.py`  **Function:** `main()`

1. Reads `settings.BACKEND_PORT` from config (default `8000`).
2. Detects if `APP_ENV=production` or `PORT` env var is set to disable hot-reload.
3. Calls `uvicorn.run("backend.app.main:app", host="0.0.0.0", port=port, reload=flag)`.
4. Uvicorn imports `backend.app.main` and locates the module-level `app` object.

### Entry Point B: `app.py` — Gradio UI (No Auth, Hugging Face Spaces)

```
python app.py
```

**File:** `app.py`  **Function:** `demo.launch()`

1. Initializes SQLite schema: `Base.metadata.create_all(bind=engine)`.
2. Warms up embedding model, reranker, Qdrant client.
3. Launches Gradio on port `7860`.
4. No user authentication — session isolated by random UUID in `gr.State`.
5. Uses the **same `rag_pipeline.execute()`** as the FastAPI version.

> **The FastAPI path is the primary focus for the rest of this document** — it includes authentication, multi-tenancy, persistent DB, and Streamlit/HTML frontends.

---

## 4. Application Startup (FastAPI Path)

**File:** `backend/app/main.py`  
**Functions:** `create_application()` and `lifespan(app)`

**Step 1: Module load — `app = create_application()` is called at import time**

Inside `create_application()`:
- Creates `FastAPI` instance with title, API prefix `/api/v1`, docs URL.
- Registers `CORSMiddleware` with origins from `settings.BACKEND_CORS_ORIGINS`.
- Registers 3 global exception handlers: `AppException`, `RequestValidationError`, `Exception`.
- Registers `add_process_time_header` middleware (`X-Process-Time-Seconds` on every response).
- Calls `application.include_router(api_router, prefix="/api/v1")` — mounts all endpoints.
- Registers GET `/`, `/style.css`, `/script.js` routes that serve static HTML/JS/CSS files.
- Mounts `/uploads` directory as static files.

**Step 2: Server starts — `lifespan(app)` context manager runs**

- Calls `setup_logging()` (structlog).
- Creates all ORM tables:
  ```python
  Base.metadata.create_all(bind=engine)
  # Creates: users, knowledge_bases, documents, conversations, messages
  ```

**Step 3: API Router Registration** — `backend/app/api/v1/router.py`

```python
api_router.include_router(health.router)           # /api/v1/health
api_router.include_router(auth.router)             # /api/v1/auth/...
api_router.include_router(users.router)            # /api/v1/users/...
api_router.include_router(knowledge_bases.router)  # /api/v1/knowledge-bases/...
api_router.include_router(documents.router)        # /api/v1/documents/...
api_router.include_router(chat.router)             # /api/v1/chat/...
```

**Step 4: Database session** — `backend/app/db/session.py`

- Reads `DATABASE_URL` from settings (SQLite by default, PostgreSQL if configured).
- If SQLite: `check_same_thread=False` + `PRAGMA foreign_keys=ON`.
- Engine created with `pool_pre_ping=True`.
- `get_db()` is a generator: yields `Session`, rolls back on exception, always closes.

---

## 5. Frontend UI - Two Separate UIs

### Option 1: Pure HTML/JS Frontend (FastAPI serves at `/`)

**Files:** `index.html`, `script.js`, `style.css`

FastAPI serves `index.html` at `GET /`:
```python
# backend/app/main.py -> serve_index()
return FileResponse(INDEX_HTML_PATH, media_type="text/html")
```

`script.js` makes `fetch()` calls to FastAPI REST API at `/api/v1/...`.  
JWT token stored in browser, sent as `Authorization: Bearer <token>`.

### Option 2: Streamlit Frontend (Port 8501)

```
streamlit run frontend/app.py
```

**File:** `frontend/app.py`  **Function:** `main()`

Checks `st.session_state["token"]`:
- No token -> `render_auth_screen()` (`frontend/components/auth.py`)
- Token exists -> `render_sidebar()` then routes by `st.session_state["nav"]`:
  - `"chat"` -> `render_chat_view()`
  - `"kbs"` -> `render_knowledge_bases_view()`
  - `"docs"` -> `render_documents_view()`

**Session state keys:** `token`, `user`, `active_kb_id`, `active_conv_id`, `nav`

**File:** `frontend/services/api_client.py` **Class:** `APIClient`

All HTTP calls use the `requests` library. Base URL: `http://localhost:8000/api/v1`.  
Every authenticated call: `Authorization: Bearer {token}` via `_headers(token)`.

---

## 6. Authentication Flow

### 6A. Registration

```
User fills register form (frontend/components/auth.py -> render_auth_screen())
    |
api_client.register(email, username, password)
  -> POST /api/v1/auth/register
    |
backend/app/api/v1/endpoints/auth.py -> register()
    |
auth_service.register_user(db, user_in)
  (backend/app/services/auth_service.py -> AuthService.register_user())
  -> Check email unique, username unique (HTTP 400 if duplicate)
  -> get_password_hash(password) -> bcrypt.hashpw()
  -> User ORM object, db.add(), db.commit()
    |
Returns: APIResponse[UserResponse]
```

### 6B. Login

```
api_client.login(username_or_email, password)
  -> POST /api/v1/auth/login
    |
auth_service.authenticate_user(db, username_or_email, password)
  -> Queries User by email OR username (SQLAlchemy OR condition)
  -> verify_password(plain, hashed) -> bcrypt.checkpw()
    |
create_access_token(subject=user.id)
  -> jose.jwt.encode({"sub": user_id, "exp": utcnow+1440min, "iat": utcnow}, HS256)
    |
Returns: {"access_token": "eyJ...", "token_type": "bearer", "user": {...}}
    |
Streamlit: st.session_state["token"] = access_token -> st.rerun()
```

### 6C. Per-Request Auth (FastAPI Dependency Injection)

Every protected endpoint: `current_user: User = Depends(get_current_active_user)`

File: `backend/app/api/deps.py`  

1. `OAuth2PasswordBearer` extracts Bearer token from `Authorization` header.
2. `decode_token(token)` -> `jose.jwt.decode()` — validates signature + expiry.
3. Extracts `"sub"` (user UUID) from payload.
4. `auth_service.get_by_id(db, user_id)` — queries `users` table.
5. Checks `user.is_active == True`.
6. Returns `User` ORM object to endpoint.

Any failure -> raises `UnauthorizedException` (HTTP 401).

---

## 7. Knowledge Base and Document Ingestion Flow

### 7A. Creating a Knowledge Base

```
api_client.create_knowledge_base(token, name, description)
  -> POST /api/v1/knowledge-bases/
    |
kb_service.create(db, kb_in, user_id)
  -> backend/app/services/kb_service.py
  -> Creates KnowledgeBase ORM record, db.add(), db.commit()
    |
Returns: APIResponse[KnowledgeBaseResponse]
```

### 7B. Document Upload and Ingestion Pipeline

This is the **offline indexing pipeline** — runs when user uploads a file, NOT during chat.

```
User picks file -> clicks "Process & Ingest Document"
    |
api_client.upload_document(token, kb_id, file_bytes, filename, content_type)
  -> POST /api/v1/documents/upload (multipart: file + knowledge_base_id)
    |
document_service.upload_and_process(db, file, kb_id, user_id)
  -> backend/app/services/document_service.py -> DocumentService.upload_and_process()
```

**Step 1: File validation**
```
DocumentService.validate_file(file)
-> Checks extension in {.pdf, .docx, .doc, .txt, .md, .csv}
-> AppException if unsupported
```

**Step 2: Ownership check**
```
Queries KnowledgeBase by kb_id
-> Verifies kb.user_id == current user's id
-> NotFoundException / ForbiddenException if failed
```

**Step 3: Save file to disk**
```
DocumentService.save_file(file, user_id, kb_id, doc_id)
-> Creates: uploads/{user_id}/{kb_id}/
-> Saves as: {doc_id}_{original_filename}
-> Validates size <= 25 MB
```

**Step 4: Create Document DB record**
```
Document ORM with status="uploaded", db.add(), db.commit()
```

**Step 5a: Parse** — `backend/app/rag/parser.py` -> `DocumentParser.parse_file()`
```
.pdf  -> parse_pdf()  -> pypdf.PdfReader, text page by page
.docx -> parse_docx() -> python-docx, joins all paragraphs
.txt/.md/.csv -> parse_txt() -> tries utf-8, utf-8-sig, latin-1, cp1252
clean_text(): normalizes whitespace and control characters
Returns: List[PageContent] (each has page_number, text)
```

**Step 5b: Chunk** — `backend/app/rag/chunker.py` -> `RecursiveChunker.chunk_pages()`
```
For each page: calls _split_text(text, separators)
Separators tried in order: ["\n\n", "\n", ". ", "? ", "! ", " ", ""]
chunk_size=800 chars, chunk_overlap=150 chars
Each chunk ID: "{doc_id}_p{page_number}_c{chunk_index}"
Returns: List[ChunkMetadata]
```

**Step 5c: Embed and Index into Qdrant** — `backend/app/services/vector_service.py` -> `VectorService.upsert_chunks()`
```
embedding_service.embed_documents([chunk.text for chunk in chunks])
  -> fastembed.TextEmbedding("BAAI/bge-small-en-v1.5")
  -> Batch size 64
  -> Returns: List[List[float]] (384-dim vectors)

For each chunk: PointStruct with:
  id: uuid5(chunk_id) — deterministic UUID
  vector: 384-dim float list
  payload: {chunk_id, document_id, user_id, knowledge_base_id,
            filename, page_number, chunk_index, text}

client.upsert(collection_name, points, wait=True)
Creates payload indexes for user_id, knowledge_base_id, document_id
```

**Step 5d: Invalidate BM25 cache**
```
hybrid_search_service.invalidate_cache(kb_id)
-> Removes cached BM25Index -> forces rebuild on next search
```

**Step 5e: Update document status**
```
doc.status = "ready", doc.chunk_count = len(chunks), db.commit()
```

---

## 8. Complete Chat Message Flow

### From Streamlit:

**File:** `frontend/app.py` -> `render_chat_view()`
```python
if prompt := st.chat_input("Ask a question..."):
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        with st.spinner("Retrieving sources and synthesizing grounded answer..."):
            res = api_client.send_message(token, kb_id, prompt, conv_id)
```

**File:** `frontend/services/api_client.py` -> `APIClient.send_message()`
```python
r = requests.post(
    f"{self.base_url}/chat/message",
    json={"knowledge_base_id": kb_id, "message": message, "conversation_id": conv_id},
    headers=self._headers(token), timeout=60
)
return r.json()
```

### At the FastAPI Backend:

**Endpoint:** `POST /api/v1/chat/message`  
**File:** `backend/app/api/v1/endpoints/chat.py` -> `send_chat_message()`

```python
conv, user_msg, assistant_msg, rag_response = chat_service.send_message(
    db=db, user_id=current_user.id,
    kb_id=payload.knowledge_base_id,
    message_text=payload.message,
    conv_id=payload.conversation_id
)
```

### Inside `ChatService.send_message()`:

**File:** `backend/app/services/chat_service.py`

**Step 1: Conversation resolution**
```python
if conv_id:
    conv = cls.get_conversation(db, conv_id, user_id)  # verify ownership
else:
    title = message_text[:40] + ("..." if len(message_text) > 40 else "")
    conv = cls.create_conversation(db, user_id, kb_id, title=title)
```

**Step 2: Persist user message**
```python
user_msg = Message(conversation_id=conv.id, role="user", content=message_text.strip())
db.add(user_msg); db.commit()
```

**Step 3: Load conversation history (sliding window)**
```python
past_messages = db.query(Message).filter(
    Message.conversation_id == conv.id,
    Message.id != user_msg.id
).order_by(Message.created_at.asc()).all()

history_payload = [{"role": m.role, "content": m.content}
                   for m in past_messages[-settings.MAX_HISTORY_MESSAGES:]]  # last 10
```

**Step 4: Execute RAG Pipeline**
```python
rag_response = rag_pipeline.execute(
    query=message_text.strip(), user_id=user_id, kb_id=kb_id,
    conversation_id=conv.id, conversation_history=history_payload
)
```

**Step 5: Persist assistant response**
```python
assistant_msg = Message(
    conversation_id=conv.id, role="assistant",
    content=rag_response.answer,
    citations=[c.model_dump(mode="json") for c in rag_response.citations],
    msg_metadata=rag_response.metadata
)
db.add(assistant_msg); db.commit()
```

---

## 9. Advanced RAG Pipeline - Step by Step

**File:** `backend/app/rag/pipeline.py`  
**Class:** `AdvancedRAGPipeline`  
**Method:** `execute(query, user_id, kb_id, conversation_id, conversation_history)`

### Step 0: Input Guardrails

**File:** `backend/app/core/guardrails.py` -> `InputGuardrails.evaluate(user_input)`

Checks against compiled regex patterns:
- English profanity (fuck, shit, bitch, bastard, asshole, cunt...)
- Hindi/Hinglish profanity (chutiya, madarchod, bhenchod, gandu...)
- Prompt injections ("ignore all previous instructions", "reveal system prompt", "jailbreak", "DAN mode")

Any match -> immediately returns blocked response (no LLM or vector DB called).

### Step 0.5: Fast-path for Greetings

```python
greetings_set = {"hi", "hello", "hey", "good morning", ..., "thanks", "thank you"}
if clean_lower in greetings_set and len(clean_lower.split()) <= 4:
    answer, _ = answer_generator.generate_answer(query=query, chunks=[], ...)
    return ChatResponse(answer=answer, citations=[], metadata={"route": "DIRECT_GREETING"})
```
Short greetings skip the entire retrieval pipeline.

### Step 1: Query Routing

**File:** `backend/app/rag/router.py` -> `QueryRouter.route(query, conversation_history)`

Returns `QueryRoute.DIRECT_QA`, `QueryRoute.REWRITE`, or `QueryRoute.HYDE`

Decision logic (in order):
1. Query in greetings set -> DIRECT_QA (no LLM call)
2. No conversation history -> DIRECT_QA (no LLM call)
3. History exists AND query <= 7 words AND contains pronouns {it, its, they, them, that, this, these, those, why, how} -> REWRITE (no LLM call)
4. Otherwise -> LLM call (groq/compound-mini, temp=0.0, max_tokens=25) returns exactly: "DIRECT_QA", "REWRITE", or "HYDE"
5. Any exception -> default DIRECT_QA

### Step 2: Query Transformation

**Route = REWRITE:**  
File: `backend/app/rag/rewriter.py` -> `QueryRewriter.rewrite(query, conversation_history)`
- Uses last 6 history messages
- LLM: resolve pronouns, standalone query only (don't answer)
- Calls `llm_service.generate(model=GROQ_ROUTER_MODEL, temp=0.1, max_tokens=100)`
- Example: "What does it support?" + auth history -> "What authentication methods does the authentication module support?"

**Route = HYDE:**  
File: `backend/app/rag/hyde.py` -> `HyDEGenerator.generate_hypothetical_document(query)`
- LLM generates a realistic 1-2 paragraph technical document passage that would answer the question
- Calls `llm_service.generate(model=GROQ_MODEL, temp=0.3, max_tokens=300)`
- The generated PASSAGE (not the query) is used as the embedding input

**Route = DIRECT_QA:**  
`search_query = query` (raw query used as-is)

### Step 3: Hybrid Search (Dense + Sparse + RRF)

**File:** `backend/app/rag/hybrid_search.py` -> `HybridSearchService.search(query, user_id, kb_id, ...)`

**3A: Dense Retrieval** — `backend/app/services/vector_service.py` -> `VectorService.dense_search()`
```
embed_query(query)
  -> If "bge" in model name: prepends "Represent this sentence for searching relevant passages: "
  -> fastembed model.embed([query_text])
  -> Returns 384-dim List[float]

qdrant_client.query_points(
    collection_name="enterprise_knowledge_base",
    query=query_vector,
    query_filter=Filter(must=[user_id==X, knowledge_base_id==Y]),
    limit=10
)
Returns: List[ScoredChunk] with retrieval_type="dense"
```

**3B: Sparse Retrieval (BM25)** — `backend/app/rag/sparse.py` -> `BM25Index`
```
Index cached in self._bm25_cache["{user_id}:{kb_id}"]
On cache miss:
  _get_kb_chunks() -> scrolls ALL Qdrant points for this user+KB (paginated)
  BM25Index.index(chunks):
    tokenize(): lowercase, alphanumeric, remove stopwords
    Compute: term frequencies, document frequencies, avg doc length
    k1=1.5, b=0.75

BM25Index.search(query, top_k=10):
  For each query token:
    IDF = log(1 + (N - n_q + 0.5) / (n_q + 0.5))
  For each document:
    score += IDF * (tf*(k1+1)) / (tf + k1*(1-b + b*(dl/avgdl)))
  Returns: List[ScoredChunk] with retrieval_type="sparse"
```

**3C: Reciprocal Rank Fusion (RRF)** — `ReciprocalRankFusion.fuse(ranked_lists, k=60, top_k=10)`
```
For each chunk across all lists:
  rrf_score(chunk) = sum(1 / (60 + rank_in_list))
Sort by rrf_score descending, take top 10
Each fused chunk gets retrieval_type="hybrid"
```

### Step 4: Cross-Encoder Reranking

**File:** `backend/app/rag/reranker.py` -> `CrossEncoderReranker.rerank(query, chunks, top_k=5)`
```
1. candidate_pool = chunks[:8]  (top 8 from RRF)

2. Lazy-load model:
   Primary:  fastembed.rerank.cross_encoder.TextCrossEncoder("Xenova/ms-marco-MiniLM-L-6-v2")
   Fallback: sentence_transformers.CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
   If both fail: return chunks[:top_k] as-is

3. Score each (query, chunk_text) pair:
   FastEmbed: model.rerank(query, texts) -> scores
   ST path:   model.predict([[query, text] for text in texts], batch_size=8)

4. Sort by score descending, return top 5 ScoredChunk with retrieval_type="reranked"
```

### Step 5: Corrective RAG (CRAG) Evaluation

**File:** `backend/app/rag/corrective.py` -> `CorrectiveRAG.evaluate_context(query, chunks, attempt)`

Returns: `(status: "RELEVANT" | "INSUFFICIENT", should_retry: bool)`

```
1. No chunks:
   -> "INSUFFICIENT", retry if attempt < MAX_RETRIEVAL_ATTEMPTS (default 2)

2. highest_score >= -1.5 (cross-encoder logit threshold):
   -> FAST-PATH: "RELEVANT", no retry, no LLM call
   (This fires for most queries)

3. Score too low -> call LLM:
   System: rate RELEVANT or INSUFFICIENT
   User: "User Question: {query}\nRetrieved Context: {3 snippets}\nRelevance Assessment:"
   Model: GROQ_ROUTER_MODEL, temp=0.0, max_tokens=30
   -> "RELEVANT" -> accept
   -> "INSUFFICIENT" and attempt < 2 -> should_retry = True
```

**CRAG retry in pipeline.py:**
```python
if should_retry:
    retry_query = f"{query} {transformed_query}"  # broadened
    retry_retrieval = hybrid_search_service.search(retry_query, ...)
    top_chunks = reranker.rerank(query, retry_retrieval.chunks, top_k=5)
    crag_status, _ = corrective_rag.evaluate_context(query, top_chunks, attempt=2)
```

### Step 6: Answer Generation with Citations

**File:** `backend/app/rag/generator.py` -> `AnswerGenerator.generate_answer(query, chunks, history, insufficient_context)`

**6A: Build context string** — `build_context(chunks, max_total_chars=4500)`
```
For each of top 5 chunks (4500 char total limit):
  "[Source 1] File: 'report.pdf' (Page 3, Chunk: uuid_p3_c7)\n<chunk text>"
Simultaneously creates Citation objects (document_id, name, page_number, chunk_id, snippet[:200])
```

**6B: Assemble LLM messages**
```python
history_messages = [{"role": ..., "content": content[:500]} for msg in history[-4:]]
if chunks and not insufficient_context:
    user_content = f"=== DOCUMENT CONTEXT ===\n{context_text}\n=== END CONTEXT ===\n\nQuestion: {query}"
else:
    user_content = query  # LLM answers from general knowledge

history_messages.append({"role": "user", "content": user_content})
```

**6C: Call LLM**
```python
answer = llm_service.generate_chat(
    messages=history_messages, system_prompt=GENERATOR_SYSTEM_PROMPT,
    model=settings.GROQ_MODEL, temperature=0.1, max_tokens=1024
)
```

`GENERATOR_SYSTEM_PROMPT` instructs LLM to:
- Identify as "Nexus AI, Enterprise AI Knowledge Assistant"
- Answer from documents with `[Source N]` inline citations
- Use markdown (bold, bullets, code blocks)
- When no context: answer conversationally

---

## 10. LLM Service - How the Model Is Called

**File:** `backend/app/services/llm_service.py`  
**Class:** `LLMService` (singleton via `__new__`)

### Multi-Key Round-Robin Pool + Model Fallback Chain

```python
FALLBACK_MODELS = [
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
    "groq/compound-mini",
    "groq/compound",
    "qwen/qwen3.6-27b"
]
```

**`get_clients()`:** Reads all keys from `GROQ_API_KEYS` + `GROQ_API_KEY`, creates one `Groq(api_key=key)` per key.

**`_get_rotated_clients()`:** Round-robin via `_key_index` counter.

**`generate(prompt, system_prompt, model, temp, max_tokens)`:**
1. Gets rotated client list.
2. Appends anti-CoT to system prompt: "CRITICAL: Output ONLY the direct final answer. Never expose chain of thought..."
3. For each client x model in `[primary_model] + FALLBACK_MODELS`:
   - `client.chat.completions.create(model, messages, temperature, max_tokens)`
   - `clean_thinking_process()` — strips `<think>...</think>` tags
   - Non-empty response -> return it
   - "reduce the length"/"400" error -> retry with `prompt[:3000]` and smaller `max_tokens`
   - Otherwise -> log warning, try next
4. All fail -> raises `LLMServiceException`

**`generate_chat(messages, system_prompt, model, ...)`:**
- Same but takes `[{"role": ..., "content": ...}]` message list
- Token-budget error -> retry with just `[system_msg, last_user_msg]`

**`clean_thinking_process(text)`:**
- Strips `<think>...</think>` XML blocks
- Removes "Thinking Process:", "Analysis:" sections
- Strips leading "Output:", "Response:", "Final Response:", "Answer:"

---

## 11. Prompt Construction

### A. Router Prompt (Step 1 — only when heuristics can't decide)
```
File:   backend/app/rag/router.py
System: ROUTER_SYSTEM_PROMPT — classify into DIRECT_QA, REWRITE, or HYDE
User:   "Conversation History:\n{last 3 msgs}\n\nCurrent Query: {query}\n\nSelected Route:"
```

### B. Rewriter Prompt (Step 2 — REWRITE route)
```
File:   backend/app/rag/rewriter.py
System: REWRITER_SYSTEM_PROMPT — resolve pronouns, standalone query only
User:   "Conversation History:\n{last 6 msgs}\nCurrent Follow-up Query: {query}\n\nRewritten Standalone Query:"
```

### C. HyDE Prompt (Step 2 — HYDE route)
```
File:   backend/app/rag/hyde.py
System: HYDE_SYSTEM_PROMPT — generate 1-2 paragraph technical passage
User:   "User Question: {query}\n\nHypothetical Passage:"
```

### D. CRAG Evaluation Prompt (Step 5 — only if score < -1.5)
```
File:   backend/app/rag/corrective.py
System: CRAG_EVAL_SYSTEM_PROMPT — rate RELEVANT or INSUFFICIENT
User:   "User Question: {query}\n\nRetrieved Context:\n{3 snippets}\n\nRelevance Assessment:"
```

### E. Answer Generation Prompt (Step 6 — always)
```
File:   backend/app/rag/generator.py
System: GENERATOR_SYSTEM_PROMPT — Nexus AI with grounding + citation instructions
Messages: [system, history[-4] (each 500 char), user: "=== DOCUMENT CONTEXT ===\n[Source 1]...\nQuestion: {query}"]
```

---

## 12. Conversation Memory Behavior

### Storage

Every user message and assistant response stored as a `Message` row.

`Message` model (`backend/app/models/message.py`):
- `id` (UUID PK)
- `conversation_id` (FK -> `conversations`, CASCADE delete)
- `role` ("user" or "assistant")
- `content` (Text column — full text)
- `citations` (JSON list)
- `msg_metadata` (JSON dict — route, latency, crag_status, etc.)
- `created_at` (UTC timestamp)

### Retrieval Per Request

File: `backend/app/services/chat_service.py`

```python
# All past messages in order, excluding current user message
past_messages = db.query(Message).filter(
    Message.conversation_id == conv.id,
    Message.id != user_msg.id
).order_by(Message.created_at.asc()).all()

# Window: last 10 messages (MAX_HISTORY_MESSAGES)
history_payload = [{"role": m.role, "content": m.content}
                   for m in past_messages[-10:]]
```

In generator (backend/app/rag/generator.py):
```python
recent_history = conversation_history[-4:]  # last 4 only for LLM budget
# Each truncated to 500 chars
```

### Persistence Summary

| Scenario | Result |
|---|---|
| Within same session | Yes — stored in DB |
| Across browser restarts | Yes — stored in DB |
| Across app restarts | Yes — SQLite/PostgreSQL |
| Across different conversations | No — isolated by `conversation_id` |
| Across different users | No — isolated by `user_id` ownership |

---

## 13. Response Flow Back to the User

**In endpoint** (`backend/app/api/v1/endpoints/chat.py`):
```python
return APIResponse(
    success=True,
    data=SendMessageResponse(
        conversation_id=conv.id,
        message_id=assistant_msg.id,
        answer=rag_response.answer,
        citations=rag_response.citations,
        metadata=rag_response.metadata
    )
)
```

**JSON response to client:**
```json
{
  "success": true,
  "data": {
    "conversation_id": "uuid...",
    "message_id": "uuid...",
    "answer": "The authentication module supports OAuth 2.0 [Source 1]...",
    "citations": [
      {"document_id": "...", "document_name": "auth_manual.pdf",
       "page_number": 4, "chunk_id": "...", "snippet": "OAuth 2.0..."}
    ],
    "metadata": {
      "route": "REWRITE",
      "transformed_query": "What authentication methods does the module support?",
      "retrieval_attempts": 1,
      "candidates_retrieved": 10,
      "top_chunks_used": 5,
      "crag_status": "RELEVANT",
      "latency_seconds": 2.341
    }
  }
}
```

**Back in Streamlit** (`frontend/app.py` -> `render_chat_view()`):
```python
st.markdown(data["answer"])
render_citations(data["citations"], data["metadata"])
st.session_state["active_conv_id"] = data["conversation_id"]
st.rerun()
```

**Citation rendering** (`frontend/components/citations.py` -> `render_citations()`):
- `st.expander("Sources & Citations (N)")` — styled cards with [Source N], filename, page, snippet
- `st.expander("RAG Telemetry")` — route, latency, candidates, top-K, CRAG status, rewritten query

**Response is NOT streamed.** No SSE, no WebSocket. Full synchronous JSON response.

---

## 14. Error Handling

### Global FastAPI Exception Handlers (backend/app/core/exceptions.py)

| Handler | Catches | HTTP Status |
|---|---|---|
| `app_exception_handler` | `AppException` subclasses | 400-503 |
| `validation_exception_handler` | `RequestValidationError` | 422 |
| `generic_exception_handler` | `Exception` (catch-all) | 500 |

All return: `{"success": false, "error": {"message": "...", "status_code": N, "details": null}}`

### Custom Exception Classes
- `NotFoundException` -> 404
- `UnauthorizedException` -> 401
- `ForbiddenException` -> 403
- `LLMServiceException` -> 502 (all Groq keys + models exhausted)
- `VectorStoreException` -> 503 (Qdrant failure)

### LLM Failures (llm_service.py)
- Tries every API key x every fallback model
- Token-budget error: retries with truncated prompt
- All fail: raises `LLMServiceException`

### Vector Store Failures (vector_service.py)
- Remote Qdrant fails at startup -> in-memory fallback
- Search errors -> `VectorStoreException`
- Delete errors -> returns `False`, logs (non-fatal)

### RAG Pipeline Graceful Degradation (pipeline.py)
- Router failure -> defaults to DIRECT_QA
- Rewriter failure -> uses original query
- HyDE failure -> uses original query
- CRAG evaluation failure -> assumes RELEVANT
- Reranker failure -> returns `chunks[:top_k]` in original order
- Generator failure -> returns `f"Error generating answer: {str(e)}"`

### Document Processing Failure (document_service.py)
```python
except Exception as e:
    db.rollback()
    doc.status = "failed"; doc.error_message = str(e); db.commit()
    raise AppException(message=f"Document processing failed: {str(e)}")
```

---

## 15. Data Objects - What Flows Through the System

### `ChunkMetadata` (Pydantic — backend/app/schemas/document.py)

Created by: `RecursiveChunker.chunk_pages()`  
Consumed by: `VectorService.upsert_chunks()`, `BM25Index.index()`
```python
{chunk_id: str, document_id: UUID, user_id: UUID, knowledge_base_id: UUID,
 filename: str, page_number: int, chunk_index: int, text: str}
```

### `ScoredChunk` (Pydantic — backend/app/schemas/rag.py)

Created by: `dense_search()`, `BM25Index.search()`, `RRF.fuse()`, `Reranker.rerank()`  
Consumed by: `AnswerGenerator.build_context()`, `CorrectiveRAG.evaluate_context()`
```python
{chunk_id: str, document_id: UUID, user_id: UUID, knowledge_base_id: UUID,
 filename: str, page_number: int, chunk_index: int, text: str,
 score: float, retrieval_type: str}  # "dense"|"sparse"|"hybrid"|"reranked"
```

### `Citation` (Pydantic — backend/app/schemas/rag.py)

Created by: `AnswerGenerator.build_context()`  
Stored in DB as JSON; sent to frontend
```python
{document_id: UUID, document_name: str, page_number: int,
 chunk_id: str, snippet: str}  # snippet = first 200 chars of chunk
```

### `ChatResponse` (Pydantic — backend/app/schemas/rag.py)

Created by: `AdvancedRAGPipeline.execute()`
```python
{conversation_id: UUID, answer: str, citations: List[Citation],
 metadata: {"route": ..., "transformed_query": ..., "retrieval_attempts": ...,
            "candidates_retrieved": ..., "top_chunks_used": ...,
            "crag_status": ..., "latency_seconds": ...}}
```

### `Message` (SQLAlchemy ORM — backend/app/models/message.py)

Table: `messages` — persists user and assistant turns with full content, citations, metadata.

---

## 16. Database Layer

**File:** `backend/app/db/session.py`

Default: SQLite (`sqlite:///./rag_knowledge_db.sqlite3`)  
Optional: PostgreSQL (set `DATABASE_URL=postgresql+psycopg2://...` in `.env`)

### ORM Models and Tables

| Model | Table | Key Columns |
|---|---|---|
| `User` | `users` | id UUID PK, email, username, hashed_password, is_active |
| `KnowledgeBase` | `knowledge_bases` | id UUID PK, name, description, user_id FK |
| `Document` | `documents` | id UUID PK, filename, original_filename, file_path, status, chunk_count, knowledge_base_id FK, user_id FK |
| `Conversation` | `conversations` | id UUID PK, title, user_id FK, knowledge_base_id FK |
| `Message` | `messages` | id UUID PK, conversation_id FK, role, content Text, citations JSON, msg_metadata JSON, created_at |

The `GUID` custom type (`backend/app/db/base.py`):
- PostgreSQL: native `UUID`
- SQLite: `CHAR(36)` string

---

## 17. Vector Database (Qdrant) Layer

**File:** `backend/app/services/vector_service.py`  
**Class:** `VectorService` (singleton via `__new__`)

**Collection:** `"enterprise_knowledge_base"`, 384-dim, Cosine similarity

### Multi-Tenant Isolation

All chunks tagged with `user_id` + `knowledge_base_id` in Qdrant payload.  
Every search: `Filter(must=[user_id==X, knowledge_base_id==Y])`.  
Users cannot see each other's data.

### Connection Strategy

```python
try:
    client = QdrantClient(host=QDRANT_HOST, port=6333, timeout=10.0)
    client.get_collections()  # connectivity test
except Exception:
    client = QdrantClient(location=":memory:")  # in-memory fallback
```

**Payload indexes** created on `user_id`, `knowledge_base_id`, `document_id` for fast filtering.

---

## 18. Complete End-to-End Example

**Scenario:** User asks "What are the authentication methods?" against a KB with "auth_manual.pdf".

1. **User types** in Streamlit chat input, presses Enter.
   - File: `frontend/app.py` -> `render_chat_view()`

2. **Streamlit calls** `api_client.send_message(token, kb_id, "What are the authentication methods?", conv_id=None)`
   - File: `frontend/services/api_client.py` -> `APIClient.send_message()`
   - Sends: `POST http://localhost:8000/api/v1/chat/message`

3. **FastAPI** authenticates JWT, calls `send_chat_message()`.
   - File: `backend/app/api/v1/endpoints/chat.py`

4. **Conversation created** (new, conv_id=None), user message persisted to DB.
   - File: `backend/app/services/chat_service.py`

5. **`rag_pipeline.execute()`** called with empty history.
   - File: `backend/app/rag/pipeline.py`

6. **Guardrails:** Input safe, passes.

7. **Router:** No history -> `QueryRoute.DIRECT_QA` (0ms, no LLM call).

8. **Hybrid Search:**
   - Dense: BGE embeds query -> Qdrant returns 10 chunks from auth_manual.pdf
   - Sparse: BM25 searches {authentication, methods} -> 10 chunks
   - RRF: fuses -> 10 unique hybrid chunks

9. **Reranker:** Cross-encoder scores top 8 -> returns top 5 in relevance order.

10. **CRAG:** Top chunk score = 2.34 (>= -1.5) -> fast-path "RELEVANT", no LLM call.

11. **Answer Generation:**
    - `build_context()` creates "[Source 1]...[Source 3]" (4500 char max)
    - Assembles: `[system, user: "=== DOCUMENT CONTEXT ===\n...\nQuestion: ..."]`
    - `llm_service.generate_chat(...)` -> Groq API (openai/gpt-oss-20b)
    - Returns: "The authentication manual describes: **OAuth 2.0** [Source 1]..."

12. **Assistant message** persisted to DB (answer + citations + metadata).

13. **HTTP 200 JSON** response sent to Streamlit.

14. **Streamlit renders:** `st.markdown(answer)`, `render_citations()`, `st.rerun()`.

**Total latency: ~2.1 seconds** (embedding + Qdrant + BM25 + cross-encoder + Groq API)

---

## 19. Master Execution Diagram

```
APPLICATION START
       |
run.py -> main() -> uvicorn.run("backend.app.main:app", :8000)
       |
backend/app/main.py -> create_application()
  [FastAPI + CORS + Exception handlers + Routers + Static files]
       |
backend/app/main.py -> lifespan()
  setup_logging()
  Base.metadata.create_all(bind=engine)  [5 tables created]
  [Server ready on :8000]

===========================================================
USER: opens / -> index.html served (HTML/JS frontend)
  OR
USER: streamlit run frontend/app.py -> Streamlit on :8501

===========================================================
USER: logs in -> POST /api/v1/auth/login
  auth_service.authenticate_user() [bcrypt.checkpw()]
  create_access_token() [jose.jwt.encode()]
  JWT token returned

===========================================================
USER: uploads document -> POST /api/v1/documents/upload
  document_service.upload_and_process()
    |-- DocumentParser.parse_file() [pypdf/python-docx/open]
    |-- RecursiveChunker.chunk_pages() [800 chars, 150 overlap]
    |-- EmbeddingService.embed_documents() [fastembed bge-small-en-v1.5]
    |-- VectorService.upsert_chunks() [Qdrant upsert]
    +-- invalidate_cache(kb_id) [BM25 cache cleared]

===========================================================
USER: sends message -> POST /api/v1/chat/message
  JWT decoded -> user verified
       |
chat_service.send_message()
  Get/create Conversation [SQL]
  Persist user Message [SQL]
  Load history: last 10 [SQL]
       |
rag_pipeline.execute()

  [GUARDRAILS] guardrails.py -> regex check -> PASS or BLOCK

  [STEP 1: ROUTER] router.py -> QueryRouter.route()
    heuristics -> optional LLM call -> DIRECT_QA | REWRITE | HYDE

  [STEP 2: QUERY TRANSFORM]
    REWRITE -> rewriter.py -> LLM: resolve pronouns
    HYDE    -> hyde.py -> LLM: generate technical passage
    DIRECT  -> raw query unchanged

  [STEP 3: HYBRID SEARCH] hybrid_search.py -> HybridSearchService.search()
    Dense:  vector_service.dense_search()
            embeddings.embed_query() [fastembed 384-dim]
            qdrant_client.query_points() [tenant-filtered]
            -> 10 ScoredChunk (dense)
    Sparse: sparse.py -> BM25Index.search()
            Pure-Python BM25 over all KB chunks
            -> 10 ScoredChunk (sparse)
    Fuse:   ReciprocalRankFusion.fuse() [RRF k=60]
            -> 10 ScoredChunk (hybrid)

  [STEP 4: RERANKER] reranker.py -> CrossEncoderReranker.rerank()
    Xenova/ms-marco-MiniLM-L-6-v2 [ONNX/FastEmbed]
    Scores top-8 -> returns top-5 (reranked)

  [STEP 5: CRAG] corrective.py -> CorrectiveRAG.evaluate_context()
    Score-based fast-path (>= -1.5 threshold) OR LLM evaluation
    -> RELEVANT (proceed) | INSUFFICIENT (retry once with broadened query)

  [STEP 6: ANSWER GENERATION] generator.py -> AnswerGenerator.generate_answer()
    build_context(top_5) -> "[Source 1]..." string + List[Citation]
    Assemble messages: history[-4] + context + query
    llm_service.generate_chat() -> Groq API [openai/gpt-oss-20b + fallbacks]
    clean_thinking_process() -> clean answer text

       |
  Returns: ChatResponse(answer, citations, metadata)

chat_service.send_message()
  Persist assistant Message [SQL: answer + citations JSON + metadata]
  Return (conv, user_msg, assistant_msg, rag_response)
       |
send_chat_message() endpoint
  Build SendMessageResponse -> APIResponse -> HTTP 200 JSON
       |
FRONTEND
  st.markdown(answer) [in assistant chat bubble]
  render_citations(citations, metadata) [source cards + telemetry]
  st.rerun()
       |
USER sees grounded answer with verifiable citations
```

---

## 20. File-Level Workflow Map

### Startup Chain
```
run.py
  +-- backend/app/main.py (create_application, lifespan)
        |-- backend/app/core/config.py
        |-- backend/app/core/logging.py
        |-- backend/app/core/exceptions.py
        |-- backend/app/db/session.py
        |-- backend/app/models/__init__.py -> all 5 ORM models
        +-- backend/app/api/v1/router.py -> all endpoint routers
```

### Request Auth Chain
```
Any protected endpoint
  +-- backend/app/api/deps.py (get_current_active_user)
        |-- backend/app/core/security.py (decode_token -> jose.jwt.decode)
        +-- backend/app/services/auth_service.py (get_by_id -> DB query)
```

### Chat Message Chain
```
POST /api/v1/chat/message
  +-- backend/app/api/v1/endpoints/chat.py (send_chat_message)
        +-- backend/app/services/chat_service.py (send_message)
              |-- backend/app/models/conversation.py
              |-- backend/app/models/message.py
              +-- backend/app/rag/pipeline.py (execute)
                    |-- backend/app/core/guardrails.py
                    |-- backend/app/rag/router.py
                    |-- backend/app/rag/rewriter.py      [REWRITE]
                    |-- backend/app/rag/hyde.py           [HYDE]
                    |-- backend/app/rag/hybrid_search.py
                    |       |-- backend/app/services/vector_service.py
                    |       |       +-- backend/app/rag/embeddings.py
                    |       +-- backend/app/rag/sparse.py
                    |-- backend/app/rag/reranker.py
                    |-- backend/app/rag/corrective.py
                    +-- backend/app/rag/generator.py
                              +-- backend/app/services/llm_service.py
                                    +-- groq.Groq client -> Groq API
```

### Document Ingestion Chain
```
POST /api/v1/documents/upload
  +-- backend/app/api/v1/endpoints/documents.py (upload_document)
        +-- backend/app/services/document_service.py (upload_and_process)
              |-- backend/app/rag/parser.py  [pypdf / python-docx / open()]
              |-- backend/app/rag/chunker.py  (RecursiveChunker)
              +-- backend/app/services/vector_service.py  (upsert_chunks)
                    +-- backend/app/rag/embeddings.py  (embed_documents)
                          +-- fastembed.TextEmbedding -> Qdrant upsert
```

---

## 21. Interview Explanation

### What this project is

This is a **production-grade, multi-tenant Enterprise RAG (Retrieval-Augmented Generation) Chatbot** that allows authenticated users to upload documents into named **Knowledge Bases** and have grounded, multi-turn conversations about those documents. The chatbot retrieves relevant passages from the uploaded documents and grounds the LLM's answer in those passages, providing verifiable source citations with the exact document name and page number.

### How the application starts

Launched with `python run.py`, which starts a **Uvicorn ASGI server** on port 8000 running a **FastAPI** application defined in `backend/app/main.py`. During startup, the lifespan context manager initializes structured logging and creates all database tables (SQLite by default, PostgreSQL in production). All REST API routes register under `/api/v1`. The server simultaneously serves a pure HTML/JS frontend at the root URL `/`.

There is also an optional **Streamlit** frontend (port 8501) and an alternative **Gradio** entry point (`app.py`) for Hugging Face Spaces — both use the same backend RAG pipeline.

### How the user interacts

The user first registers and logs in. The backend issues a **JWT access token** (HS256, valid 24 hours) that must be sent as `Authorization: Bearer` with every request. The user then creates a Knowledge Base, uploads documents (PDF, DOCX, TXT) into it, and starts chatting.

### What happens when a message is submitted

1. Frontend sends `POST /api/v1/chat/message` with message text, knowledge base ID, and optional conversation ID.
2. Backend authenticates the JWT, verifies the user.
3. `ChatService.send_message()` saves the user message to the database, loads the last 10 messages as conversation history, and calls `AdvancedRAGPipeline.execute()`.
4. The RAG pipeline runs a **6-stage process:**
   - **Guardrails:** Blocks profanity and prompt injection via compiled regex patterns.
   - **Query Router:** Decides whether to use the original query (DIRECT_QA), rewrite it to resolve pronouns (REWRITE), or generate a HyDE passage (HYDE). Decision by heuristics first; LLM only called when heuristics can't decide.
   - **Query Transformation:** If REWRITE, LLM reformulates the query. If HYDE, LLM generates a hypothetical answer passage used as the vector search input.
   - **Hybrid Search:** Query embedded with `BAAI/bge-small-en-v1.5` (384-dim FastEmbed/ONNX), used to search Qdrant for dense matches. Simultaneously, pure-Python BM25 searched for lexical matches. Both lists fused via Reciprocal Rank Fusion (RRF, k=60).
   - **Cross-Encoder Reranking:** Top 8 RRF candidates re-scored with `ms-marco-MiniLM-L-6-v2` (ONNX via FastEmbed) to pick the most relevant 5.
   - **CRAG:** Reranked chunks evaluated for relevance by score threshold (fast-path) or LLM call. If insufficient, a second retrieval attempt with broadened query.
5. Final answer generated by Groq API with a structured prompt: document context (`[Source 1]`, `[Source 2]`, etc.) + last 4 conversation turns. Uses multi-key round-robin pool with model fallback chain.
6. Response (answer + citations + metadata) saved to DB, returned to client.

### How context and memory work

Conversation history stored persistently in the `messages` table. Per request: last 10 messages loaded and passed to pipeline; generator trims to last 4 for LLM budget. History persists across restarts.

### How the response reaches the user

Complete synchronous JSON (not streamed). Frontend receives answer text, citations (document name, page, snippet), and telemetry (route, latency, CRAG status). Streamlit renders answer in markdown with expandable "Sources & Citations" and "RAG Telemetry" panels.

### Key engineering choices (from code)

- **Groq API multi-key round-robin pool** with 5-model fallback chain — maximizes availability
- **Qdrant payload filtering** for multi-tenant isolation — users never see each other's data
- **Pure-Python BM25** (no external library) cached in memory per knowledge base
- **RRF fusion** with k=60 — combines dense + sparse without score normalization
- **CRAG score-based fast-path** (threshold >= -1.5) — avoids extra LLM calls on most queries
- **Anti-CoT cleaning** — strips `<think>...</think>` automatically from thinking models
- **Three frontend options** — HTML/JS (FastAPI), Streamlit (REST client), Gradio (HF Spaces)
