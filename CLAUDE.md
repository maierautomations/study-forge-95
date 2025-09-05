# CLAUDE.md — Project Context & Guardrails (StudyRAG)

## 0) One-liner

StudyRAG ist eine KI-Lernplattform für Studierende: **Dokumente hochladen → RAG-Chat mit Zitaten → Quizze generieren → personalisiert & gamifiziert üben.**

## 1) Status quo (aus diesem Repo)

- **Frontend**: Vite + React + TypeScript + Tailwind + shadcn-ui (Loveable-Template) — bereits mit **Supabase** verbunden (Auth/Storage/UI). [oai_citation:1‡GitHub](https://github.com/maierautomations/study-forge-95)
- **Screens**: Dashboard, Library, Upload, Chat, Quiz, Settings (ausgebaut als UI, noch ohne echtes RAG/Quiz-Backend).
- **Ordner** (kurz):
  - `src/` – App Code (Vite), Komponenten, Pages/Routes
  - `public/` – Assets
  - `supabase/` – (falls vorhanden) Setup/SQL
  - diverse Configs (`tailwind.config.ts`, `vite.config.ts`, `package.json`, etc.)

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

### P0 — Backend-Skeleton & Health

1. Erzeuge in `apps/api` ein **FastAPI**-Skeleton (Python 3.11+):
   - `app/main.py` (FastAPI, CORS, `/health`)
   - `app/core/config.py` (Pydantic Settings)
   - `app/db/session.py` (asyncpg/SQLAlchemy oder `asyncpg` + Raw SQL)
   - `pyproject.toml` (fastapi, uvicorn[standard], pydantic-settings, httpx, asyncpg, python-dotenv)

### P1 — Supabase Schema & Policies

2. Lege (falls nicht vorhanden) die Tabellen/Policies an (siehe **SQL unten** → in Supabase SQL Editor ausführen).
3. Schreibe eine kleine **DB-Init**/Migration-Routine (nur Server-seitig benutzen).

### P2 — OpenAPI & Endpoints v1

4. Implementiere **OpenAPI**-konform (siehe „API-Skizze“ unten):
   - `POST /docs/ingest` → startet Extraction/Chunk/Embed (async Job)
   - `GET  /docs/status?documentId=` → Fortschritt
   - `POST /rag/query` → liefert `answer` + `citations[]` (Dummy zuerst)
   - `POST /quiz/generate` → erzeugt Fragen (Dummy zuerst)
   - `POST /quiz/submit` → wertet Attempt aus
5. Exportiere OpenAPI nach `apps/api/openapi/openapi.json`.

### P3 — Frontend Wiring

6. Erzeuge im Frontend einen **typed API-Client** aus OpenAPI (z. B. openapi-typescript).
7. Ersetze die **Mock-Calls** in `src/…` (Chat/Quiz/Upload/Library) durch echte API-Aufrufe.
8. **Streaming** im Chat (SSE oder Fetch Streams) einschalten (Fortschritts-Rendering).

### P4 — Ingestion & Retrieval

9. **Ingestion** Service: Unstructured/MarkItDown → Chunks (header-aware, 300–800 Tokens, 10–15 % Overlap) → Embeddings → Insert in `chunks/embeddings`.
10. **Retrieval** Service: BM25 (tsvector) + Vector (cosine) → **Merge** (gewichtetes Ranking). Rückgabe inkl. `source_ref`.

### P5 — Cleanup & Tests

11. Unit-Tests (pytest) für Services + einfache E2E (Upload→Query Dummy).
12. Fehlerbehandlung, Logging (Trace-ID), kleine Readme-Erweiterung.

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
	•	API-Endpoints + Pydantic-Schemas + Tests.
	•	OpenAPI exportiert, typed Client im Frontend ersetzt Mocks.
	•	Chat-Antworten immer mit citations[].
	•	Keine Secrets im Client. Lint/Typecheck/Tests grün.

## 10) Was Claude nicht ändern soll
	•	Supabase Keys/Policies nie im Frontend antasten.
	•	Keine 3rd-Party Vector-DB im MVP (kein Qdrant).
	•	Keine Logs mit PII. Keine stillen Architekturwechsel.

## 11) Nützliche Links
	•	Repo-Landing & Tech-Summary (Vite/React/TS/Tailwind/shadcn, Loveable): siehe README im Repo.
```
