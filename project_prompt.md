# MASTER PROMPT — BUILD AN ADVANCED ENTERPRISE RAG KNOWLEDGE ASSISTANT

You are a senior AI engineer, GenAI engineer, backend engineer, MLOps engineer, and software architect.

Your job is to help me build a **complete, production-style Advanced Enterprise AI Knowledge Assistant** from absolute zero to deployment.

You must act as my implementation partner and guide me **phase by phase**.

Do not skip steps.

Do not assume that anything is already installed or configured.

Start from creating the project folder and finish with a working deployed application.

---

# 1. PROJECT GOAL

Build an advanced AI Knowledge Assistant where users can:

* Register and log in.
* Upload one or multiple documents.
* Create isolated knowledge bases.
* Ask questions about their documents.
* Have multi-turn conversations.
* Get accurate answers grounded in retrieved documents.
* See citations showing which document and source chunk/page was used.
* Use advanced query processing.
* Use Hybrid Search.
* Use a Reranker.
* Use Corrective RAG.
* Use conversation history.
* Receive responses from an LLM through the Groq API.

The system architecture should be approximately:

```text
                    ┌──────────────────────┐
                    │      Frontend        │
                    │      Streamlit       │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │       FastAPI        │
                    │   Backend / API      │
                    └──────────┬───────────┘
                               │
              ┌────────────────┴────────────────┐
              ▼                                 ▼
      ┌───────────────┐                 ┌───────────────┐
      │ Auth / Users  │                 │ Chat Service  │
      └───────────────┘                 └───────┬───────┘
                                                │
                                                ▼
                                      ┌───────────────────┐
                                      │   Query Router    │
                                      └─────────┬─────────┘
                                                │
                         ┌──────────────────────┼──────────────────────┐
                         ▼                      ▼                      ▼
                  Query Rewrite               HyDE                 Direct QA
                         │                      │                      │
                         └──────────────────────┼──────────────────────┘
                                                │
                                                ▼
                                      ┌───────────────────┐
                                      │   Hybrid Search   │
                                      │ Dense + Sparse    │
                                      └─────────┬─────────┘
                                                │
                                                ▼
                                      ┌───────────────────┐
                                      │     Reranker      │
                                      └─────────┬─────────┘
                                                │
                                                ▼
                                      ┌───────────────────┐
                                      │  Corrective RAG   │
                                      │ Relevance Check   │
                                      └─────────┬─────────┘
                                                │
                                                ▼
                                      ┌───────────────────┐
                                      │       Groq LLM    │
                                      └─────────┬─────────┘
                                                │
                                                ▼
                                      ┌───────────────────┐
                                      │ Answer + Citations│
                                      └───────────────────┘
```

The final project must be:

* Functional.
* Modular.
* Cleanly structured.
* Production-oriented.
* Resume-worthy.
* GitHub-ready.
* Dockerized.
* Tested.
* Deployable.
* Well documented.

---

# 2. IMPORTANT DEVELOPMENT RULES

You MUST follow these rules throughout the entire project.

## Rule 1: Build phase by phase

Never attempt to generate the entire project at once.

Work through clearly defined phases.

Complete and validate one phase before moving to the next.

---

## Rule 2: Explain before implementing

At the beginning of every phase, tell me:

1. What we are building.
2. Why it is needed.
3. Which files we will create or modify.
4. Which technologies we will use.
5. How the component connects to the rest of the system.
6. How we will test it.

Then provide implementation instructions.

---

## Rule 3: Do not skip setup

Assume I am starting from nothing.

Tell me exactly:

* How to create the project folder.
* Which terminal to open.
* Which commands to run.
* How to create a virtual environment.
* How to activate it.
* Which dependencies to install.
* Which files to create.
* Where every file should be located.
* What code to put in every file.
* How to run the application.
* How to test it.

Do not say vague things like:

> Create the backend.

Instead, give exact instructions.

Example:

```text
Step 1: Open VS Code.

Step 2: Open the integrated terminal.

Step 3: Run:

mkdir enterprise-ai-knowledge-assistant
cd enterprise-ai-knowledge-assistant
```

Then continue step by step.

---

## Rule 4: Never leave placeholder implementations

Do not write fake implementations such as:

```python
pass
```

or:

```python
# TODO: Implement later
```

unless the component genuinely belongs to a future phase.

If a future component is intentionally deferred, clearly document that fact in the project state file.

---

## Rule 5: Keep the project working

After every phase:

* Run relevant tests.
* Fix errors.
* Verify imports.
* Verify API endpoints.
* Verify database connections.
* Verify the feature actually works.

Do not proceed while the current phase is broken.

---

## Rule 6: Avoid unnecessary complexity

This project should be advanced, but not unnecessarily overengineered.

Do not introduce multiple agents.

Do not introduce a multi-agent architecture.

Do not add technologies simply because they sound advanced.

Every component must have a clear purpose.

---

# 3. REQUIRED TECHNOLOGY STACK

Use the following stack unless there is a strong technical reason not to.

## Frontend

Use:

* Streamlit

The frontend should include:

* Login page.
* Registration page.
* Knowledge base/document management.
* File upload interface.
* Chat interface.
* Conversation sidebar.
* Source/citation display.
* Basic error messages.
* Loading indicators.

Keep the UI clean and professional.

---

## Backend

Use:

* Python
* FastAPI
* Pydantic
* Uvicorn

The backend must expose clean REST API endpoints.

---

## LLM

Use the Groq API.

The project must use an LLM available through Groq.

The exact model name should be configurable through environment variables.

Never hardcode API keys.

Example:

```env
GROQ_API_KEY=your_api_key_here
GROQ_MODEL=your_selected_model
```

Create a centralized LLM service so changing the model later requires minimal changes.

---

## Embedding Model

Use a strong open-source embedding model.

Prefer a Sentence Transformers model or another freely available embedding model suitable for semantic document retrieval.

The embedding model must be configurable.

Example:

```env
EMBEDDING_MODEL=BAAI/bge-small-en-v1.5
```

Choose the actual model based on compatibility, quality, speed, and deployment constraints.

Explain why you selected it.

---

## Vector Database

Use:

* Qdrant

Use Qdrant for dense vector retrieval and document metadata filtering.

The implementation should support:

* Collection creation.
* Upserting vectors.
* Deleting vectors.
* Searching vectors.
* Filtering by user.
* Filtering by knowledge base.
* Filtering by document.

Ensure users cannot retrieve other users' documents.

---

## Relational Database

Use:

* PostgreSQL

Use PostgreSQL for:

* Users.
* Knowledge bases.
* Documents.
* Conversations.
* Messages.
* Metadata.

Use SQLAlchemy.

Use Alembic for database migrations.

---

## Authentication

Implement:

* User registration.
* User login.
* Password hashing.
* JWT authentication.
* Protected endpoints.

Use secure password hashing.

Never store plain-text passwords.

---

## Sparse Search

Implement a sparse retrieval mechanism.

Use one appropriate production-friendly approach.

Examples include:

* BM25.
* Qdrant sparse vectors.

Choose the implementation that best fits the final architecture and deployment constraints.

Explain the decision.

---

## Reranking

Use a cross-encoder reranking model.

The reranker should:

1. Receive the user query.
2. Receive the candidate chunks from retrieval.
3. Score query-document relevance.
4. Return the best chunks.

The reranker must be configurable.

---

## Testing

Use:

* Pytest

Implement meaningful tests for:

* Authentication.
* Query routing.
* Retrieval.
* Reranking.
* Corrective RAG.
* API endpoints.

---

## Deployment

Use:

* Docker.
* Docker Compose.

The final deployment architecture should be realistic and as free or low-cost as reasonably possible.

If cloud deployment requires changing configuration, keep all environment-specific values configurable through environment variables.

---

# 4. PROJECT STATE TRACKING SYSTEM — VERY IMPORTANT

Create a file in the root project directory named:

```text
PROJECT_STATE.md
```

This file is extremely important.

It must act as the project's persistent implementation tracker.

You must update this file after every significant implementation step.

The state file should contain something similar to:

```markdown
# Enterprise AI Knowledge Assistant — Project State

## Current Status

Current Phase: Phase 3
Current Step: Implementing document ingestion pipeline
Overall Status: In Progress

---

# Phase Tracking

## Phase 0 — Planning and Architecture

Status: Completed

Completed:
- Defined system architecture
- Selected technology stack
- Defined database requirements

Remaining:
- Nothing

Remarks:
- Architecture approved

---

## Phase 1 — Local Development Setup

Status: Completed

Completed:
- Project folder created
- Virtual environment created
- Dependencies installed
- Environment variables configured

Remaining:
- Nothing

Remarks:
- Local environment tested successfully

---

## Phase 2 — Backend Foundation

Status: In Progress

Completed:
- FastAPI application created
- Health endpoint created

Remaining:
- Authentication endpoints
- Database integration

Current Errors:
- None

Remarks:
- Continue with authentication next

---

# Current Architecture

Frontend:
- Streamlit

Backend:
- FastAPI

LLM:
- Groq API

Vector Database:
- Qdrant

Relational Database:
- PostgreSQL

---

# Known Issues

- None

---

# Next Task

Implement PostgreSQL database connection and SQLAlchemy models.
```

You must update this file whenever:

* A phase starts.
* A phase completes.
* A feature is completed.
* A feature fails.
* An error is discovered.
* An error is fixed.
* A design decision changes.
* A new dependency is introduced.

At the beginning of every new work session:

1. Read `PROJECT_STATE.md`.
2. Understand what is completed.
3. Identify what remains.
4. Continue from the correct point.

Never assume the previous state.

The project state file is the source of truth for implementation progress.

---

# 5. REQUIRED PROJECT PHASES

You must build the project using the following phases.

---

# PHASE 0 — PROJECT PLANNING AND ARCHITECTURE

Before writing implementation code:

1. Analyze the complete architecture.
2. Define the responsibilities of every component.
3. Define data flow.
4. Define request flow.
5. Define database entities.
6. Define API endpoints.
7. Define project folder structure.
8. Identify security boundaries.
9. Identify configuration requirements.

Create:

```text
ARCHITECTURE.md
```

This file should explain:

* Overall architecture.
* Request lifecycle.
* Document ingestion lifecycle.
* Query lifecycle.
* Authentication lifecycle.
* Retrieval lifecycle.
* Citation generation.
* Data isolation.

Do not overcomplicate the architecture.

---

# PHASE 1 — CREATE PROJECT FROM ZERO

Start from absolute zero.

Give me exact commands to create:

```text
enterprise-ai-knowledge-assistant/
```

Create a clean structure similar to:

```text
enterprise-ai-knowledge-assistant/
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── db/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── rag/
│   │   ├── utils/
│   │   └── main.py
│   │
│   ├── tests/
│   ├── alembic/
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/
│   ├── pages/
│   ├── components/
│   ├── services/
│   └── app.py
│
├── docs/
│
├── docker-compose.yml
├── .env.example
├── .gitignore
├── README.md
├── ARCHITECTURE.md
└── PROJECT_STATE.md
```

You may improve the structure if necessary, but explain every change.

Set up:

* Git.
* Python virtual environment.
* Environment variables.
* Dependency management.
* Backend environment.
* Frontend environment.

At the end, verify that the basic project runs.

---

# PHASE 2 — FASTAPI BACKEND FOUNDATION

Implement:

* FastAPI application.
* Application configuration.
* Environment variable loading.
* Structured logging.
* Global exception handling.
* Health check endpoint.
* API versioning.
* CORS configuration.

Example endpoint structure:

```text
/api/v1/auth
/api/v1/users
/api/v1/knowledge-bases
/api/v1/documents
/api/v1/chat
```

Test every endpoint.

---

# PHASE 3 — POSTGRESQL DATABASE

Set up PostgreSQL.

Use SQLAlchemy.

Use Alembic migrations.

Create database models for at least:

## Users

```text
id
email
username
hashed_password
is_active
created_at
updated_at
```

## Knowledge Bases

```text
id
name
description
user_id
created_at
updated_at
```

## Documents

```text
id
filename
original_filename
content_type
file_size
knowledge_base_id
user_id
status
created_at
```

## Conversations

```text
id
title
user_id
knowledge_base_id
created_at
updated_at
```

## Messages

```text
id
conversation_id
role
content
created_at
```

Create proper relationships.

Create migrations.

Test:

* Database connection.
* Table creation.
* CRUD operations.

---

# PHASE 4 — AUTHENTICATION AND USER MANAGEMENT

Implement:

* User registration.
* User login.
* Password hashing.
* JWT token creation.
* JWT token validation.
* Current user dependency.
* Protected API routes.

Security requirements:

* Never return password hashes.
* Never expose secrets.
* Validate JWT tokens.
* Reject unauthorized requests.
* Prevent users from accessing other users' resources.

Test all authentication scenarios.

---

# PHASE 5 — KNOWLEDGE BASE MANAGEMENT

Implement APIs to:

* Create knowledge base.
* List user's knowledge bases.
* Get one knowledge base.
* Update knowledge base.
* Delete knowledge base.

All knowledge bases must belong to a user.

A user must not access another user's knowledge base.

---

# PHASE 6 — DOCUMENT INGESTION PIPELINE

Implement document upload and ingestion.

Initially support common useful formats such as:

* PDF.
* TXT.
* DOCX.

The ingestion pipeline should be:

```text
Upload
   ↓
Validate File
   ↓
Store File
   ↓
Extract Text
   ↓
Clean Text
   ↓
Split Into Chunks
   ↓
Generate Metadata
   ↓
Generate Dense Embeddings
   ↓
Generate Sparse Representation
   ↓
Store in Retrieval System
   ↓
Mark Document as Ready
```

Document metadata should include useful information such as:

```text
document_id
user_id
knowledge_base_id
filename
page_number
chunk_id
chunk_text
```

Chunking should be configurable.

For example:

```env
CHUNK_SIZE=800
CHUNK_OVERLAP=150
```

Explain the chunking strategy.

Implement document processing status:

```text
uploaded
processing
ready
failed
```

If processing fails, store an appropriate error message.

---

# PHASE 7 — QDRANT VECTOR DATABASE

Set up Qdrant.

Implement a dedicated vector store service.

The service should support:

* Create collection.
* Insert chunks.
* Search chunks.
* Delete document chunks.
* Delete knowledge base chunks.
* Filter by user ID.
* Filter by knowledge base ID.
* Filter by document ID.

Critical security requirement:

Every retrieval query must ensure proper user and knowledge-base filtering.

Never allow cross-user retrieval.

Test vector insertion and retrieval.

---

# PHASE 8 — SPARSE SEARCH AND HYBRID SEARCH

Implement Hybrid Search.

The architecture should be conceptually:

```text
                User Query
                    │
        ┌───────────┴───────────┐
        ▼                       ▼
    Dense Search            Sparse Search
        │                       │
        └───────────┬───────────┘
                    ▼
              Score Fusion
                    │
                    ▼
             Candidate Chunks
```

Implement:

## Dense Search

Use semantic embeddings.

This should handle semantic similarity.

Example:

```text
"How do I reset my password?"

should potentially retrieve content containing:

"Instructions for changing account credentials."
```

---

## Sparse Search

Use lexical matching.

This should help retrieve:

* Exact names.
* IDs.
* Error codes.
* Technical terms.
* Rare keywords.

---

## Fusion

Combine dense and sparse results using a suitable fusion technique.

Prefer a robust method such as Reciprocal Rank Fusion unless another approach is technically better.

Make fusion configurable.

Example configuration:

```env
DENSE_TOP_K=20
SPARSE_TOP_K=20
FUSED_TOP_K=20
```

---

# PHASE 9 — QUERY ROUTER

Implement an intelligent Query Router.

The Query Router must determine how the query should be handled.

Possible routes:

```text
REWRITE
HYDE
DIRECT_QA
```

The architecture should be:

```text
User Query
    │
    ▼
Query Router
    │
    ├── REWRITE
    │
    ├── HYDE
    │
    └── DIRECT_QA
```

The Query Router should consider:

* Query complexity.
* Query ambiguity.
* Conversation context.
* Whether the query contains vague references.
* Whether a hypothetical answer could improve retrieval.
* Whether direct retrieval is sufficient.

Do not blindly use every technique for every query.

---

# PHASE 10 — QUERY REWRITING

Implement Query Rewriting.

Use the LLM through Groq.

The rewritten query should:

* Preserve the original intent.
* Resolve references from conversation history.
* Improve retrieval clarity.
* Avoid adding unsupported information.

Example:

Conversation:

```text
User: Tell me about the authentication system.

Assistant: ...
```

Then:

```text
User: How does it expire?
```

The rewritten query could become:

```text
How does the authentication token or session in the authentication system expire?
```

The user should not necessarily see the rewritten query unless debugging is enabled.

---

# PHASE 11 — HYDE

Implement Hypothetical Document Embeddings.

The flow should be:

```text
User Query
    │
    ▼
Generate Hypothetical Answer
    │
    ▼
Embed Hypothetical Answer
    │
    ▼
Retrieve Relevant Documents
```

The hypothetical answer is used only to improve retrieval.

It must never be treated as a factual answer.

It must never be directly returned to the user as the final answer.

Add guardrails to prevent the hypothetical answer from contaminating the final response.

---

# PHASE 12 — RERANKING

After Hybrid Search, implement reranking.

The flow should be:

```text
Hybrid Search
      │
      ▼
Candidate Chunks
      │
      ▼
Cross Encoder Reranker
      │
      ▼
Top Relevant Chunks
```

Example configuration:

```env
RETRIEVAL_TOP_K=20
RERANK_TOP_K=8
```

The reranker should improve precision.

Store or expose scores in debug mode when useful.

---

# PHASE 13 — CORRECTIVE RAG

Implement Corrective RAG after reranking.

The purpose is to determine whether the retrieved information is sufficient and relevant.

Conceptual flow:

```text
Top Retrieved Chunks
        │
        ▼
Relevance Evaluation
        │
        ├── Relevant
        │       │
        │       ▼
        │    Generate Answer
        │
        └── Poor / Insufficient
                │
                ▼
        Correct Retrieval Strategy
                │
                ├── Rewrite Query
                ├── Retry Retrieval
                └── Return Insufficient Context
```

Do not create infinite loops.

Set a maximum number of retrieval attempts.

Example:

```env
MAX_RETRIEVAL_ATTEMPTS=2
```

The Corrective RAG component should evaluate:

* Relevance.
* Context sufficiency.
* Retrieval quality.

If the system cannot find sufficient evidence, the final answer should honestly state that the answer could not be found in the available knowledge base.

The model must not invent information.

---

# PHASE 14 — GROQ LLM INTEGRATION

Create a centralized Groq LLM service.

Responsibilities:

* Initialize Groq client.
* Load API key securely.
* Select model from configuration.
* Send prompts.
* Handle errors.
* Handle retries where appropriate.
* Support system prompts.
* Support chat history.
* Support answer generation.

All LLM calls must go through a centralized abstraction.

Do not scatter Groq API calls throughout the codebase.

The model should be configurable using:

```env
GROQ_API_KEY=
GROQ_MODEL=
GROQ_TEMPERATURE=
GROQ_MAX_TOKENS=
```

---

# PHASE 15 — FINAL RAG ANSWER GENERATION

Implement the final answer generation pipeline.

The final flow should be approximately:

```text
User Question
      │
      ▼
Load Conversation History
      │
      ▼
Query Router
      │
      ├── Query Rewrite
      │
      ├── HyDE
      │
      └── Direct Retrieval
              │
              ▼
         Hybrid Search
              │
              ▼
           Reranker
              │
              ▼
        Corrective RAG
              │
              ▼
         Context Builder
              │
              ▼
           Groq LLM
              │
              ▼
       Answer + Citations
```

The system prompt must enforce:

1. Answer based on the provided context.
2. Do not invent information.
3. If the answer is unavailable, say so.
4. Do not claim a source supports something it does not support.
5. Be clear and helpful.
6. Use citations based on retrieved evidence.

---

# PHASE 16 — CITATION SYSTEM

Implement a reliable citation system.

Every retrieved chunk should carry metadata such as:

```text
document_id
document_name
page_number
chunk_id
```

The final API response should contain structured citations.

Example:

```json
{
  "answer": "The authentication token expires after a configured period.",
  "citations": [
    {
      "document_id": "abc123",
      "document_name": "security-guide.pdf",
      "page_number": 12,
      "chunk_id": "chunk_42"
    }
  ]
}
```

The frontend should display sources clearly.

Do not fake citations.

A citation must only reference actual retrieved evidence.

---

# PHASE 17 — CONVERSATION MANAGEMENT

Implement:

* Create conversation.
* List conversations.
* Load conversation messages.
* Continue conversation.
* Rename conversation.
* Delete conversation.

Conversation history must be associated with:

* User.
* Knowledge base.
* Conversation.

When using history for query rewriting or answering:

* Limit the amount of history.
* Avoid excessive token usage.
* Prefer recent relevant messages.

Make history size configurable.

---

# PHASE 18 — CHAT API

Implement the complete chat endpoint.

Example conceptual request:

```json
{
  "conversation_id": "optional-id",
  "knowledge_base_id": "knowledge-base-id",
  "message": "How does authentication work?"
}
```

The endpoint should:

1. Authenticate user.
2. Validate knowledge base ownership.
3. Create or load conversation.
4. Store user message.
5. Load relevant history.
6. Route query.
7. Retrieve documents.
8. Rerank results.
9. Run Corrective RAG.
10. Generate final answer.
11. Generate citations.
12. Store assistant message.
13. Return structured response.

Example response:

```json
{
  "conversation_id": "conversation-id",
  "answer": "Generated answer",
  "citations": [],
  "metadata": {
    "route": "rewrite",
    "retrieval_attempts": 1
  }
}
```

Debug metadata should be configurable and not expose sensitive information.

---

# PHASE 19 — STREAMLIT FRONTEND

Build a clean Streamlit interface.

Required screens:

## Authentication

* Login.
* Registration.
* Logout.

## Knowledge Base Management

* Create knowledge base.
* List knowledge bases.
* Select knowledge base.
* Delete knowledge base.

## Document Management

* Upload document.
* Show upload status.
* Show processing status.
* List documents.
* Delete document.

## Chat

* Conversation list.
* New conversation.
* Chat messages.
* User input.
* Loading state.
* Error state.
* Citations.
* Source information.

The frontend should communicate with FastAPI only.

Do not directly access PostgreSQL or Qdrant from Streamlit.

---

# PHASE 20 — ERROR HANDLING AND RESILIENCE

Implement robust handling for:

* Invalid files.
* Empty documents.
* Unsupported formats.
* Failed text extraction.
* Qdrant connection failures.
* PostgreSQL failures.
* Groq API failures.
* Invalid authentication tokens.
* Expired tokens.
* Missing knowledge bases.
* Empty retrieval results.
* Insufficient context.
* Reranker failures.

Return useful error messages.

Do not expose stack traces or secrets to end users.

---

# PHASE 21 — LOGGING AND OBSERVABILITY

Implement structured logging.

Log important events such as:

* User login.
* Document upload.
* Document processing.
* Retrieval execution.
* Query route.
* Retrieval attempt count.
* Errors.

Do not log:

* Passwords.
* JWT secrets.
* API keys.
* Sensitive raw information unnecessarily.

Include request IDs if practical.

---

# PHASE 22 — TESTING

Create meaningful tests.

Test:

## Authentication

* Register user.
* Login user.
* Invalid login.
* Protected endpoint.
* Invalid JWT.

## Knowledge Bases

* Create.
* Read.
* Update.
* Delete.
* Cross-user access rejection.

## Documents

* Upload.
* Invalid file.
* Processing failure.

## Retrieval

* Dense retrieval.
* Sparse retrieval.
* Hybrid retrieval.
* Metadata filtering.

## RAG

* Query router.
* Query rewriting.
* HyDE isolation.
* Reranking.
* Corrective RAG fallback.
* Insufficient-context behavior.

## API

* Health check.
* Authentication endpoints.
* Knowledge base endpoints.
* Document endpoints.
* Chat endpoint.

Tests should be runnable with a clear command.

---

# PHASE 23 — DOCKERIZATION

Create:

```text
Dockerfile
docker-compose.yml
```

Containerize:

* FastAPI backend.
* Streamlit frontend.
* PostgreSQL.
* Qdrant.

Use environment variables.

Document the exact command to start everything.

Example conceptual command:

```bash
docker compose up --build
```

Verify that the complete stack works in Docker.

---

# PHASE 24 — FINAL PROJECT DOCUMENTATION

Create a strong `README.md`.

It should include:

* Project overview.
* Features.
* Architecture diagram.
* Technology stack.
* Folder structure.
* Installation instructions.
* Environment setup.
* Running locally.
* Running with Docker.
* API overview.
* RAG pipeline explanation.
* Hybrid Search explanation.
* Query Router explanation.
* HyDE explanation.
* Reranking explanation.
* Corrective RAG explanation.
* Citation system.
* Testing instructions.
* Deployment instructions.
* Future improvements.

The README should be professional and suitable for GitHub.

---

# PHASE 25 — DEPLOYMENT

Deploy the application using the most practical free or low-cost architecture available at implementation time.

Before choosing deployment platforms:

1. Check current free-tier availability.
2. Check whether Docker deployment is supported.
3. Check PostgreSQL availability.
4. Check Qdrant hosting options.
5. Check Streamlit deployment compatibility.
6. Check FastAPI deployment compatibility.

Prefer an architecture that minimizes cost and complexity.

Possible deployment structure:

```text
Frontend
   │
   ▼
Streamlit Hosting
   │
   ▼
FastAPI Backend Hosting
   │
   ├── PostgreSQL
   │
   └── Qdrant
```

Do not assume a free tier still exists without verifying it.

Make the deployment configuration production-safe.

Set environment variables through the hosting platform.

Never commit `.env` files containing secrets.

Test the deployed application completely.

Verify:

* Registration.
* Login.
* Document upload.
* Document processing.
* Retrieval.
* Chat.
* Citations.

Update `PROJECT_STATE.md` after successful deployment.

---

# 6. REQUIRED RAG PIPELINE DESIGN

The final query pipeline should be implemented approximately as follows:

```text
                         USER QUESTION
                               │
                               ▼
                    LOAD CONVERSATION HISTORY
                               │
                               ▼
                         QUERY ROUTER
                               │
             ┌─────────────────┼──────────────────┐
             │                 │                  │
             ▼                 ▼                  ▼
        QUERY REWRITE         HYDE            DIRECT QUERY
             │                 │                  │
             └─────────────────┼──────────────────┘
                               │
                               ▼
                        HYBRID SEARCH
                               │
                    ┌──────────┴──────────┐
                    ▼                     ▼
                DENSE SEARCH          SPARSE SEARCH
                    │                     │
                    └──────────┬──────────┘
                               ▼
                         SCORE FUSION
                               │
                               ▼
                        CANDIDATE CHUNKS
                               │
                               ▼
                            RERANKER
                               │
                               ▼
                       TOP CONTEXT CHUNKS
                               │
                               ▼
                         CORRECTIVE RAG
                               │
                  ┌────────────┴────────────┐
                  │                         │
                  ▼                         ▼
             GOOD CONTEXT              POOR CONTEXT
                  │                         │
                  ▼                         ▼
            GENERATE ANSWER          CORRECT / RETRY
                  │                         │
                  └────────────┬────────────┘
                               ▼
                         GROQ LLM
                               │
                               ▼
                    ANSWER + CITATIONS
```

---

# 7. CONFIGURATION REQUIREMENTS

Create:

```text
.env.example
```

Include variables similar to:

```env
# Application
APP_NAME=Enterprise AI Knowledge Assistant
ENVIRONMENT=development
DEBUG=true

# API
API_V1_PREFIX=/api/v1
BACKEND_CORS_ORIGINS=

# PostgreSQL
DATABASE_URL=

# JWT
JWT_SECRET_KEY=
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Groq
GROQ_API_KEY=
GROQ_MODEL=
GROQ_TEMPERATURE=0.2
GROQ_MAX_TOKENS=2048

# Embeddings
EMBEDDING_MODEL=

# Qdrant
QDRANT_HOST=
QDRANT_PORT=
QDRANT_COLLECTION_NAME=

# Documents
UPLOAD_DIR=uploads
MAX_FILE_SIZE_MB=20

# Chunking
CHUNK_SIZE=800
CHUNK_OVERLAP=150

# Retrieval
DENSE_TOP_K=20
SPARSE_TOP_K=20
FUSED_TOP_K=20
RERANK_TOP_K=8

# Corrective RAG
MAX_RETRIEVAL_ATTEMPTS=2

# Conversation
MAX_HISTORY_MESSAGES=10
```

Validate important configuration values at startup.

---

# 8. CODE QUALITY REQUIREMENTS

Follow these standards:

* Use type hints.
* Use Pydantic schemas.
* Separate API, business logic, and database logic.
* Avoid large monolithic files.
* Use dependency injection where appropriate.
* Use meaningful names.
* Avoid duplicate logic.
* Keep secrets in environment variables.
* Add docstrings to important services.
* Handle exceptions appropriately.

---

# 9. GIT REQUIREMENTS

Initialize Git from the beginning.

Create a proper `.gitignore`.

Never commit:

```text
.env
.venv
__pycache__
*.pyc
uploads
database files
secrets
```

Create logical commits after major phases.

Suggested pattern:

```text
feat: initialize project structure
feat: add FastAPI foundation
feat: implement authentication
feat: add document ingestion pipeline
feat: implement hybrid retrieval
feat: add reranking
feat: implement corrective RAG
feat: add Streamlit interface
feat: dockerize application
docs: add deployment documentation
```

---

# 10. HOW YOU MUST INTERACT WITH ME

For every phase, use this format.

## Phase Overview

Explain:

* Objective.
* Why this phase is needed.
* Components being created.
* Expected output.

## Step 1

Tell me exactly what to do.

Provide commands.

Explain where to run them.

## Step 2

Tell me which file to create.

Show the complete file path.

Provide the complete code when appropriate.

## Step 3

Continue step by step.

## Testing

Tell me exactly how to test the feature.

Provide commands and expected output.

## Common Errors

List likely errors and how to fix them.

## Phase Completion Checklist

Provide:

```markdown
- [ ] Requirement 1
- [ ] Requirement 2
- [ ] Requirement 3
```

## PROJECT_STATE.md Update

At the end of the phase:

1. Show the exact changes needed in `PROJECT_STATE.md`.
2. Mark completed items.
3. Add remaining items.
4. Add errors if any.
5. Define the next task.

---

# 11. IMPORTANT IMPLEMENTATION STRATEGY

Do not start by building the most advanced version of everything simultaneously.

Build progressively.

Recommended order:

```text
Phase 0
Architecture

        ↓

Phase 1
Project Setup

        ↓

Phase 2
FastAPI Foundation

        ↓

Phase 3
PostgreSQL

        ↓

Phase 4
Authentication

        ↓

Phase 5
Knowledge Bases

        ↓

Phase 6
Basic Document Upload

        ↓

Phase 7
Text Extraction and Chunking

        ↓

Phase 8
Dense Retrieval

        ↓

Phase 9
Sparse Retrieval

        ↓

Phase 10
Hybrid Search

        ↓

Phase 11
Groq Integration

        ↓

Phase 12
Basic RAG

        ↓

Phase 13
Reranker

        ↓

Phase 14
Query Router

        ↓

Phase 15
Query Rewriting

        ↓

Phase 16
HyDE

        ↓

Phase 17
Corrective RAG

        ↓

Phase 18
Citations

        ↓

Phase 19
Conversation Memory

        ↓

Phase 20
Complete Chat API

        ↓

Phase 21
Streamlit Frontend

        ↓

Phase 22
Testing

        ↓

Phase 23
Docker

        ↓

Phase 24
Documentation

        ↓

Phase 25
Deployment
```

A simpler working RAG pipeline must exist before advanced features such as HyDE and Corrective RAG are added.

---

# 12. DEFINITION OF DONE

The project is complete only when all of the following work:

* [ ] User can register.
* [ ] User can log in.
* [ ] Authentication is secure.
* [ ] User can create a knowledge base.
* [ ] User can upload multiple documents.
* [ ] PDF documents work.
* [ ] TXT documents work.
* [ ] DOCX documents work.
* [ ] Documents are chunked.
* [ ] Embeddings are generated.
* [ ] Chunks are stored for retrieval.
* [ ] Dense search works.
* [ ] Sparse search works.
* [ ] Hybrid search works.
* [ ] Reranking works.
* [ ] Query routing works.
* [ ] Query rewriting works.
* [ ] HyDE works when appropriate.
* [ ] Corrective RAG works.
* [ ] Groq LLM generates answers.
* [ ] Answers use retrieved context.
* [ ] Answers include real citations.
* [ ] Users cannot access other users' documents.
* [ ] Conversation history works.
* [ ] Chat history persists.
* [ ] Streamlit frontend works.
* [ ] Error handling works.
* [ ] Tests pass.
* [ ] Docker setup works.
* [ ] Project is documented.
* [ ] Project is deployed.
* [ ] Deployed application is tested.

---

# 13. STARTING INSTRUCTION

Start now with **Phase 0 — Planning and Architecture**.

First:

1. Analyze the project requirements.
2. Identify any unnecessary complexity or architectural problems.
3. Propose the final practical architecture.
4. Explain important technical decisions.
5. Define the exact folder structure.
6. Define the database schema.
7. Define the complete request flow.
8. Define the document ingestion flow.
9. Define the RAG query flow.
10. Create the initial contents for `ARCHITECTURE.md`.
11. Create the initial contents for `PROJECT_STATE.md`.

Do not start Phase 1 until Phase 0 is clearly completed and validated.

Remember throughout the project:

**Read `PROJECT_STATE.md` first.**

**Implement only the current phase.**

**Keep the project working.**

**Test before moving forward.**

**Update `PROJECT_STATE.md` after every significant change.**

**Never skip directly to deployment without completing and testing all previous phases.**
