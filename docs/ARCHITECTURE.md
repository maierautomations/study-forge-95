# Architektur — StudyRAG (Vite + React + TS)

## Kurzüberblick

- **Frontend**: Vite + React + TypeScript + Tailwind + shadcn-ui. Auth/Storage via Supabase. API-Calls über `VITE_API_BASE_URL`.
- **Backend**: FastAPI (separater Dienst), OpenAPI-First, Streaming (SSE/Fetch-Streams).
- **Daten**: Supabase Postgres 16 + pgvector (Embeddings), Storage-Bucket `documents`, RLS.
- **RAG**: Ingestion (Unstructured/MarkItDown) → Chunks → Embeddings → Hybrid Retrieval (BM25 + Vector) → Antwort mit Zitaten.
- **Region/DSGVO**: Alles in EU-Regionen (Supabase EU, Hosting EU).

## Verzeichnisstruktur (relevant)

- `src/` – Vite-Frontend (UI, Routing, Supabase-Client, API-Client)
- `src/pages|routes` – Seiten/Views (Dashboard, Library, Upload, Chat, Quiz, Settings)
- `src/lib/` – Hilfen (Supabase, API-Client, Stream-Utils)
- `apps/api/` – (wird erstellt) FastAPI Backend
- `supabase/migrations/` – SQL (Schema, Policies)
- `docs/` – PRD, Architecture, OpenAPI Sketch, Tech Notes

## 1) High-Level Architecture

┌───────────────────────────────┐ HTTPS ┌───────────────────────────────┐
│ Frontend (Vite + React TS) │ <----------------> │ Backend (FastAPI) │
│ - Supabase Auth (client) │ │ - OpenAPI (v1) │
│ - UI: Dashboard/Library/... │ │ - Auth: Supabase JWT verify │
│ - API-Base: VITE_API_BASE │ │ - Services: │
└───────────────┬───────────────┘ │ • ingestion │
│ │ • retrieval │
│ Supabase JS (Auth/Storage) │ • generation │
│ │ • quiz │
▼ └───────┬───────────┬───────────┘
┌──────────────────────┐ DB │ │ LLM APIs
│ Supabase (EU-Region)│ (SQL) │ │ (Embeddings/Chat)
│ - Postgres + pgvector│ <───────────┐ │ │
│ - RLS Policies │ │ │ │
│ - Storage: documents │ INSERT/ │ SELECT/MERGE │ │
└───────────┬───────────┘ UPDATE │ │ │
│ │ │ │
└──────────────► Ingestion ◄──────────────┘ │
(Worker/Task) │

## 2) Ingestion-Pipeline (Upload → Index)

[User]
│ (drag&drop / Upload)
▼
Frontend (Vite) ──► Supabase Storage (Bucket: documents)
│
│ trigger / API call (/docs/ingest)
▼
FastAPI / ingestion service
│
│ read file (signed URL)
▼
┌──────────────────────────────┐
│ Unstructured / MarkItDown │
│ - parse PDF/DOCX/PPTX │
│ - section/title aware │
└─────────────┬────────────────┘
│ chunks (300–800 tokens, overlap 10–15%)
▼
Embeddings (LLM API)
│ vectors (dim=1536 z.B.)
▼
┌───────────────────────────────────────────────────────┐
│ Postgres (Supabase) │
│ - INSERT chunks(content, section_ref, ordinal, tsv) │
│ - INSERT embeddings(chunk_id, embedding) │
│ - UPDATE documents(status='ready') │
└───────────────────────────────────────────────────────┘

Status abrufen: GET /docs/status?documentId=...

## 3) RAG-Anfrage (Frage → Antwort mit Zitaten)

User Frage
│
▼
Frontend (Chat UI, Streaming)
│ POST /rag/query { documentId, question }
▼
FastAPI RAG Orchestrator
│
├─► Retrieve (Hybrid)
│ a) BM25: SELECT ... WHERE tsv @@ tsquery ORDER BY ts_rank LIMIT k
│ b) Vector: SELECT ... ORDER BY embedding <=> q_embedding LIMIT k
│ c) Merge: gewichtete Scores → Top-N
│
├─► (optional) Rerank (später)
│
├─► Prompt-Augment (Top-N Chunks + Zitier-Metadaten)
│
└─► Generate (LLM API)
│
└─► Antwort + citations[{chunkId, page?, section?, textSnippet}]

Streaming zurück an Frontend (SSE/Fetch Streams) → UI rendert Text + Zitate

## 4) Quiz-Flow (Generieren → Attempt → Scoring)

Create Quiz
│ POST /quiz/generate { documentId, config }
▼
FastAPI Quiz Service
│ - zieht relevante Chunks
│ - generiert Fragen (MC/TF/Short) + Distraktoren + source_ref
│ - legt quiz + questions + attempt an
▼
Resp: { attemptId, questions[...] }

Attempt (UI)
│ Nutzer beantwortet → POST /quiz/submit { attemptId, answers[...] }
▼
Quiz Service
│ - bewertet (correct/incorrect)
│ - speichert answers, score
▼
Resp: { score, breakdown, explanations?, sources? }
│
└─► Frontend zeigt Ergebnis, speichert Progress/XP

## 5) Datenmodell (vereinfachte Sicht)

profiles (id PK -> auth.users, display_name, created_at)
documents (id PK, owner_id -> profiles.id, title, storage_path, mime, page_count, size, created_at)
chunks (id PK, document_id -> documents.id, ordinal, content, tokens, section_ref, tsv)
embeddings(chunk_id PK -> chunks.id, embedding vector(1536))
quizzes (id PK, owner_id -> profiles.id, document_id -> documents.id, config, created_at)
questions (id PK, quiz_id -> quizzes.id, qtype, prompt, options, answer, explanation, source_ref)
quiz_attempts (id PK, quiz_id -> quizzes.id, user_id -> profiles.id, score, duration, started_at, completed_at)
answers (id PK, attempt_id -> quiz_attempts.id, question_id -> questions.id, chosen, correct)

## Frontend (Vite)

- **ENV**: `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`, `VITE_API_BASE_URL`.
- **Auth**: Supabase Session; geschützte Routen (alles außer Sign-In).
- **API-Client**: aus **OpenAPI** generiert (openapi-typescript). Keine harten URLs im Code.
- **Streaming**: Chat nutzt SSE/ReadableStream für tokenweise Ausgabe.
- **UI/UX**: shadcn-Komponenten, Loading/Empty/Error-Zustände, Zitations-Box unter Antworten.

## Backend (FastAPI)

- **Endpunkte** (v1): `/docs/ingest`, `/docs/status`, `/rag/query`, `/quiz/generate`, `/quiz/submit`, `/health`.
- **Auth**: Supabase-JWT prüfen (Server-Side; keine Service Keys im Client).
- **OpenAPI**: export nach `apps/api/openapi/openapi.json`.
- **Services**:
  - **ingestion**: Datei → Unstructured/MarkItDown → Chunks → Embeddings → Insert
  - **retrieval**: BM25 (tsvector) + Vector (cosine) → Merge → (später Rerank)
  - **generation**: Prompt-Augment (mit Zitaten)
  - **quiz**: Item-Erzeugung, Attempts, Scoring

## Datenbank (Supabase / Postgres)

- **Tabellen**: `profiles`, `documents`, `chunks(tsv)`, `embeddings(vector)`, `quizzes`, `questions`, `quiz_attempts`, `answers`.
- **Indizes**: `gin(tsv)` für BM25, `ivfflat` für `embeddings`.
- **RLS**: Nur Owner sieht/bearbeitet eigene Ressourcen.
- **Storage**: Bucket `documents`, Downloads via signierten URLs.

## Deployment

- **Frontend**: Vercel (oder Netlify) – Build: Vite, ENV `VITE_*`, EU-Region.
- **Backend**: Fly.io/AWS/GCP in **EU**, ENV/Secrets dort setzen.
- **Supabase**: EU-Projekt, Migrations/Policies eingespielt.

## Observability & Sicherheit

- **Logging**: strukturierte Logs (keine PII), Trace-ID je Request.
- **Fehler**: klare Messages, 4xx/5xx sauber unterscheiden.
- **Rate Limits/Abuse**: später auf API-Ebene (FastAPI-Middleware) ergänzen.

## Wann wäre eine Migration zu Next.js sinnvoll?

- **Server Side Rendering**/ISR für öffentliche SEO-Seiten
- **Edge-Middleware**/Region-nahe Rendering
- **Vercel-First Features** (Route Handlers als BFF)
  Solange die App primär **auth-gate**d und tool-artig ist, ist **Vite** absolut ausreichend.
