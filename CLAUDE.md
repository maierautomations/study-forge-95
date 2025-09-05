# CLAUDE.md — Project Context & Guardrails (StudyRAG)

## 0) One-liner

StudyRAG ist eine KI-Lernplattform für Studierende: **Dokumente hochladen → RAG-Chat mit Zitaten → Quizze generieren → personalisiert & gamifiziert üben.**

## 1) Status quo (aktuell - nach P3 Implementierung)

- **Frontend**: Vite + React + TypeScript + Tailwind + shadcn-ui (Loveable-Template) — bereits mit **Supabase** verbunden (Auth/Storage/UI)
- **Backend**: FastAPI (Python 3.11+) mit vollständigem Document Ingestion Pipeline (P0-P3 ✅ fertig)
- **Screens**: Dashboard, Library, Upload, Chat, Quiz, Settings (UI fertig, API-Integration teilweise implementiert)
- **Ordner**:
  - `src/` – Frontend Code (Vite), Komponenten, Pages/Routes  
  - `apps/api/` – **FastAPI Backend** (neu implementiert)
    - `app/services/` – Ingestion Pipeline (extraction, chunking, embeddings)
    - `app/db/` – Database operations mit RLS
    - `app/api/v1/` – REST Endpoints
    - `app/workers/` – Background document processing
  - `docs/` – Architektur & Setup Dokumentation
  - `supabase/` – Schema & Migrations
  - diverse Configs

## 2) Unser Zielbild (MVP → V1)

- **MVP (jetzt bauen)**
  1. **Backend/API** als separaten Dienst (Python **FastAPI**) im Ordner `apps/api`.
  2. **Ingestion**: PDF/DOCX → Unstructured/MarkItDown → Chunks → Embeddings (pgvector).
  3. **Retrieval**: Hybrid (BM25 via `tsvector` + Vector Cosine) → Merge (Top-k).
  4. **RAG-Antworten**: mit **Zitaten** (Seite/Abschnitt/Text-Snippet).
  5. **Quiz-Engine** (MC/T-F/Short) mit Quellen & Erklärungen; Attempts + Scoring.
  6. **OpenAPI** exportieren → **typed Frontend-Client** → UI an echtes Backend anschließen.
- **V1 (später)**
  - Reranking (Cohere/Voyage), Spaced-Repetition, Item-Analytics, leichte Community/Gamification.

## 3) Nicht verhandelbare Leitplanken

- **Datenschutz/EU**: Supabase-Projekt & Storage in EU. Keine Service-Keys im Frontend.
- **Quellenpflicht**: Antworten nur mit belegten Zitaten aus Nutzer-Dokumenten.
- **Kein Qdrant im MVP**: Vektor-Suche über **pgvector** in Postgres.
- **OpenAPI-First**: Backend definiert die API → Frontend nutzt generierten Client.
- **Logs**: Keine PII in Logs. Fehlertexte klar, aber datensparsam.

## 4) ENV (wohin?)

**Frontend (`.env.local`)**
VITE_SUPABASE_URL=
VITE_SUPABASE_ANON_KEY=
VITE_API_BASE_URL=http://localhost:8000

> In Vite heißen öffentliche Variablen standardmäßig `VITE_*`.

**Backend (`apps/api/.env`)**
DATABASE_URL=postgresql://:@:5432/postgres
SUPABASE_URL=
SUPABASE_ANON_KEY=
SUPABASE_SERVICE_ROLE_KEY= # nur serverseitig
OPENAI_API_KEY=
ALLOWED_ORIGINS=http://localhost:3000,https://

## 5) Arbeitsauftrag an Claude (Prioritätenliste)

### ✅ P0 — Backend-Skeleton & Health (FERTIG)
- FastAPI-Skeleton in `apps/api` implementiert
- Health endpoints, CORS, Pydantic Settings
- Database session management mit asyncpg

### ✅ P1 — Supabase Schema & Policies (FERTIG)  
- Tabellen erstellt: documents, chunks, embeddings
- RLS Policies implementiert und getestet
- DB-Init/Migration-Routine vorhanden

### ✅ P2 — OpenAPI & Endpoints v1 (FERTIG)
- Alle API Endpoints implementiert (docs/ingest, status, rag/query, quiz/*)
- OpenAPI Schema exportiert
- Pydantic Models für Request/Response

### ✅ P3 — Document Ingestion Pipeline (FERTIG)
- **Services Layer komplett**:
  - Text extraction (PDF/DOCX/TXT via Unstructured/MarkItDown)
  - Intelligent chunking (500 tokens, 15% overlap, header-aware)
  - OpenAI embeddings mit batch processing
  - Full orchestration mit error handling
- **Database Operations**: Bulk inserts, RLS-compliant, transaction-safe
- **Background Processing**: Async workers, concurrency limits, job management
- **API Integration**: Real logic statt dummy responses
- **Testing**: Comprehensive test suite, setup documentation

### ✅ P4 — Hybrid Retrieval (FERTIG - 100% getestet)
- **BM25 Retrieval**: PostgreSQL tsvector für full-text search ✅
- **Vector Retrieval**: pgvector cosine similarity ✅  
- **Hybrid Merge**: Weighted ranking (BM25 40% + Vector 60%) ✅
- **Citation Extraction**: Source references mit chunk_id, page, section ✅
- **RAG Service**: Query → Retrieval → LLM → Answer mit Citations ✅
- **API Integration**: Echte /rag/query + /rag/query/stream endpoints ✅
- **Test Results**: 11/11 tests passing (100% success rate) ✅

### 🎯 P5 — Quiz Engine MVP (NÄCHSTER SCHRITT)
- **Question Generation**: MC/True-False/Short Answer aus chunks
- **Difficulty Levels**: Beginner/Intermediate/Advanced
- **Attempt Tracking**: Scoring, explanations mit source references
- **Question Types**: Multiple choice, true/false, short answer

### 🎯 P6 — Frontend Integration (SPÄTER)
- Typed API Client aus OpenAPI generieren
- Mock-Calls durch echte API ersetzen  
- Streaming Chat implementieren (SSE/Fetch Streams)

## 6) API-Skizze (V1, kompakt)

```http
POST /docs/ingest
  body: { documentId, storagePath, mime }
  202 { status:"started", documentId, jobId }

GET  /docs/status?documentId=...
  200 { status:"pending"|"processing"|"ready"|"error", progress?:number }

POST /rag/query
  body: { documentId, question }
  200 { answer, citations:[{chunkId, page?, section?, textSnippet}], traceId }

POST /quiz/generate
  body: { documentId, config:{ count, types:["mc"|"tf"|"short"], difficulty } }
  200 { attemptId, questions:[{id,qtype,prompt,options?,source_ref}] }

POST /quiz/submit
  body: { attemptId, answers:[{questionId, value}] }
  200 { score, breakdown:[{questionId, correct}], explanations?:[{questionId,text,source_ref}] }

## 7) Supabase SQL (MVP)

For more Information, check the following files:

Check @0001_init.sql
Check @0002_policies.sql

## 8) Hybrid Retrieval (SQL-Merge, Beispiel)

with bm25 as (
  select c.id as chunk_id,
         ts_rank_cd(c.tsv, plainto_tsquery('simple', :q)) as score
  from public.chunks c
  join public.documents d on d.id = c.document_id
  where d.owner_id = :user_id and c.tsv @@ plainto_tsquery('simple', :q)
  order by score desc
  limit 20
),
vec as (
  select e.chunk_id,
         1 - (e.embedding <=> :q_embedding) as score
  from public.embeddings e
  join public.chunks c on c.id = e.chunk_id
  join public.documents d on d.id = c.document_id
  where d.owner_id = :user_id
  order by e.embedding <=> :q_embedding
  limit 20
)
select chunk_id,
       coalesce(max(score_bm25),0) as score_bm25,
       coalesce(max(score_vec),0)  as score_vec,
       (coalesce(max(score_bm25),0)*0.4 + coalesce(max(score_vec),0)*0.6) as hybrid
from (
  select chunk_id, score as score_bm25, null::float as score_vec from bm25
  union all
  select chunk_id, null::float, score from vec
) s
group by chunk_id
order by hybrid desc
limit 10;

## 9) Definition of Done (DoD)

### ✅ P0-P4 (FERTIG):
- API-Endpoints + Pydantic-Schemas implementiert ✅
- FastAPI Backend vollständig funktionsfähig ✅
- Document Ingestion Pipeline produktionsreif ✅
- Background processing mit job management ✅
- BM25 + Vector Search implementiert ✅
- Hybrid ranking algorithm (40/60 weight) ✅
- Citation extraction mit source references ✅
- RAG Service mit OpenAI integration ✅
- Streaming RAG endpoints (/rag/query/stream) ✅
- Comprehensive testing (11/11 tests, 100% success) ✅

### 🎯 P5 (Quiz Engine - NÄCHSTER SCHRITT):
- Question generation aus document chunks
- Multiple question types (MC/TF/Short)
- Attempt tracking mit scoring
- Source-based explanations

### 🎯 P6 (Frontend Integration):
- OpenAPI typed client generiert
- Mock calls durch echte API ersetzt
- Chat streaming implementiert
- Keine secrets im frontend

## 10) Was Claude nicht ändern soll
	•	Supabase Keys/Policies nie im Frontend antasten.
	•	Keine 3rd-Party Vector-DB im MVP (kein Qdrant).
	•	Keine Logs mit PII. Keine stillen Architekturwechsel.

## 11) Wichtige Code-Strukturen für Claude Code

### Backend Architecture (apps/api/)
```
app/
├── main.py                 # FastAPI app mit CORS, health, lifespan
├── core/
│   └── config.py          # Pydantic Settings für ENV vars
├── db/
│   ├── session.py         # asyncpg connection pool
│   ├── operations.py      # CRUD für chunks/embeddings mit RLS
│   └── validation.py      # Schema validation
├── services/              # 🔥 CORE INGESTION PIPELINE
│   ├── extraction.py      # PDF/DOCX → structured text (Unstructured/MarkItDown)
│   ├── chunking.py        # Text → optimale chunks (500 tokens, 15% overlap)
│   ├── embeddings.py      # OpenAI text-embedding-3-small
│   └── ingestion.py       # Orchestrator: extract→chunk→embed
├── workers/
│   └── document_processor.py  # Background jobs (max 3 concurrent)
├── api/
│   ├── deps.py           # JWT auth, user_id extraction
│   └── v1/
│       ├── documents.py  # /docs/* endpoints (ingest, status, list, delete)
│       ├── rag.py        # /rag/* endpoints (query - dummy)
│       └── quiz.py       # /quiz/* endpoints (generate, submit - dummy)
└── models/               # Pydantic request/response schemas
```

### Key Commands für Development
```bash
# API Server starten
cd apps/api && poetry run uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload

# Frontend starten  
npm run dev

# Ingestion Pipeline testen (P3)
cd apps/api && poetry run python test_ingestion.py

# Hybrid Retrieval testen (P4)  
cd apps/api && poetry run python test_retrieval.py

# OpenAPI Schema exportieren
cd apps/api && poetry run python export_openapi.py
```

### Database Schema (Supabase)
- **documents**: id, filename, title, status, chunks_count, owner_id, created_at
- **chunks**: id, document_id, content, tsv (full-text), page_number, token_count  
- **embeddings**: id, chunk_id, embedding (1536-dim vector)
- **RLS**: Alle Tabellen haben Row Level Security basierend auf JWT user_id

### Environment Setup
```bash
# Backend (.env)
DATABASE_URL=postgresql://postgres:password@db.project.supabase.co:5432/postgres
SUPABASE_URL=https://project.supabase.co
SUPABASE_ANON_KEY=eyJ...
SUPABASE_SERVICE_ROLE_KEY=eyJ...  
OPENAI_API_KEY=sk-...
JWT_SECRET_KEY=your_secret
JWT_ISSUER=https://project.supabase.co/auth/v1

# Frontend (.env.local)
VITE_SUPABASE_URL=https://project.supabase.co
VITE_SUPABASE_ANON_KEY=eyJ...
VITE_API_BASE_URL=http://localhost:8002
```

### Testing P3 (Document Ingestion)
```bash
# Alle Tests laufen (erwartet: 3 passed, 3 failed wegen missing config)
cd apps/api && poetry run python test_ingestion.py

# Einzelne Komponenten testen
python -c "from app.services.chunking import create_chunks; print('✓ Chunking works')"
```

### Next Steps (P5 - Quiz Engine)
1. **Question Generation**: Generate MC/TF/Short answer questions from chunks
2. **Difficulty Assessment**: Automatically determine question difficulty levels  
3. **Question Types**: Implement multiple choice, true/false, short answer
4. **Attempt Tracking**: Score tracking, performance analytics
5. **Source-based Explanations**: Link explanations back to document sources

### Development Notes
- ✅ P0-P4 komplett implementiert und getestet (100% success rate)
- 🎯 P5 (Quiz Engine) ist der nächste logische Schritt
- API läuft auf :8002, Frontend auf :3000  
- Hybrid Retrieval vollständig funktionsfähig
- Alle dependencies bereits installiert
- Database schema in Supabase bereit
- OpenAI integration working (embeddings + LLM)
- Background processing funktioniert
- Comprehensive documentation und test suites

## 12) Nützliche Links
- **Setup Guide**: `apps/api/INGESTION_SETUP.md`
- **Architecture**: `docs/ARCHITECTURE.md`  
- **Task Progress**: `docs/TASKS.md`
- **API Docs**: http://localhost:8002/docs (wenn API läuft)
```
