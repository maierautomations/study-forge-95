0. TL;DR (Executive Summary)

StudyRAG ist eine Lern-SaaS für Studierende: Dokumente hochladen → RAG-Chat mit Zitaten → Quizze generieren → personalisiert & gamifiziert üben.
Frontend steht (Vite + Supabase + UI). Dieses PRD definiert Backend/API, Ingestion/Retrieval, Quiz-Engine, Datenmodell, KPIs, Akzeptanzkriterien und die konkrete Implementierungsreihenfolge.

⸻

1. Vision & Produktziele
   • Verlässliches Lernen: Antworten immer mit Zitaten aus den eigenen Dokumenten.
   • Schnelles Üben: One-click-Quizze in mehreren Formaten.
   • Personalisierung: Fokus auf Schwachstellen, Streaks/XP als Motivation.
   • EU-Konform: Datenverarbeitung und Speicherung ausschließlich in EU-Regionen.

Erfolgskriterien (KPIs, MVP)
• Antwort-Nützlichkeit: ≥ 80 % „hilfreich“ Feedback in der App.
• Zitierquote: ≥ 95 % der Antworten enthalten ≥ 1 verwertbares Zitat.
• Lernaktivität: D7-Retention ≥ 30 %, Ø 90 min/Woche aktive Lernzeit.
• Quiz-Engagement: ≥ 60 % der Sitzungen schließen ein Quiz ab.

⸻

2. Zielnutzer & Personas (kurz)
   • Laura (BWL, 22): Viele PDFs/Slides; will Zusammenfassungen, MC-Übungen.
   • Markus (Informatik, 25): Verständnisfragen, kurze Codeschnipsel-Erklärungen.
   • Später: Tutor:innen/Dozent:innen (Kursräume, Kuratierung, Analytics).

⸻

3. Scope

In Scope (MVP)
• UI (bestehend): Dashboard, Library, Upload, Chat, Quiz, Settings.
• Supabase (EU): Auth, Storage-Bucket documents, Postgres 16 + pgvector.
• Ingestion: PDF/DOCX/MD → Unstructured/MarkItDown → Chunks + Embeddings.
• Retrieval (Hybrid): BM25 (tsvector) + Vector (cosine, pgvector) → Merge.
• RAG-Chat: Antwort mit Zitaten (Seite/Abschnitt/Text-Snippet), Streaming.
• Quiz-MVP: MC/True-False/Short, Erklärungen + Quellen. Attempts + Score.
• OpenAPI-First: FastAPI exportiert OpenAPI → typed Client im Frontend.
• RLS/Policies: Nur Owner sieht/bearbeitet eigene Daten.
• Basic Gamification: Streak, XP, wenige Badges (UI vorhanden).

Out of Scope (MVP)
• Reranking (kommt in V1), Spaced Repetition, Kurs-Communities, Dozenten-Dashboards, native Apps.

⸻

4. Systemübersicht (Repo-Stand)

Frontend
• Stack: Vite + React + TS + Tailwind + shadcn.
• Auth/Storage: Supabase.
• ENV: VITE_SUPABASE_URL, VITE_SUPABASE_ANON_KEY, VITE_API_BASE_URL.
• Seiten (bereits vorhanden):
• /dashboard, /library, /upload, /chat, /quiz, /settings
• API-Client: erst Mocks, später aus OpenAPI generiert.

Backend (neu)
• FastAPI (Python 3.11/3.12) als separater Dienst: apps/api/…
• Services: ingestion, retrieval, generation, quiz.
• OpenAPI Export: apps/api/openapi/openapi.json.

Daten
• Supabase: Postgres + pgvector, RLS aktiv.
• Tabellen: profiles, documents, chunks, embeddings, quizzes, questions, quiz_attempts, answers.
• Storage: Bucket documents (signierte Downloads).

⸻

5. Funktionale Anforderungen

5.1 Upload & Ingestion
• Nutzer lädt Datei in Supabase Storage hoch (UI vorhanden).
• App triggert /docs/ingest mit {documentId, storagePath, mime}.
• Ingestion extrahiert Text (Unstructured/MarkItDown), erzeugt header-aware Chunks (300–800 Tokens, 10–15 % Overlap), erstellt Embeddings, schreibt in DB.
• /docs/status liefert Fortschritt bis „ready“.

Akzeptanzkriterien
• Unterstützte Typen: PDF, DOCX, MD, TXT (PPTX optional).
• Nach Ingestion: documents.page_count befüllt (falls extrahierbar), chunks/embeddings vorhanden.
• Fehlerfälle (beschädigte Datei) werden als status: "error" protokolliert.

5.2 RAG-Chat
• /rag/query nimmt {documentId, question}.
• Retrieval: Hybrid (BM25+Vector) → Merge (gewichtete Scores).
• Antwort enthält citations[] mit chunkId, optional page, section, textSnippet.
• Streaming-Antwort in der Chat-UI.

Akzeptanzkriterien
• Keine Antwort ohne Zitate (mind. 1 Quelle).
• „Keine Quelle“ → freundlicher Fallback („konnte keine beweisbaren Passagen finden“).
• P95 Latenz ≤ 2,5 s (nach warm-up, typische Dokumentgröße 30–80 Seiten).

5.3 Quiz
• /quiz/generate erzeugt auf Basis der Chunks Fragen (MC/T-F/Short) inkl. kurzer Erklärung & Quellenhinweis.
• /quiz/submit bewertet Antworten und speichert Attempt-Ergebnis.

Akzeptanzkriterien
• Default-Quiz: 10–15 Fragen, gemischte Typen.
• Jede Frage hat source_ref (Chunk/Seite).
• Ergebnisansicht zeigt Score + pro Frage richtig/falsch + Erklärung.

5.4 Sicherheit/Compliance
• Alle API-Calls mit Supabase JWT (Bearer).
• RLS in Postgres sorgt dafür, dass nur Owner Daten sieht/bearbeitet.
• Keine Service-Keys im Client.
• Logs ohne PII, mit Trace-ID.

⸻

6. Nicht-funktionale Anforderungen
   • EU-Regionen: Supabase-Projekt EU; Hosting Backend in EU; Frontend-Hosting EU.
   • Reliability: 99.5 % (MVP-Ziel), Recoverable Deploys.
   • Observability: strukturierte Logs, eindeutige Trace-ID pro Request.
   • Build/CI: Lint/Typecheck/Tests für Web & API; OpenAPI-Export + Codegen als Job.

⸻

7. Informationsarchitektur (UI ↔ API)
   • Dashboard
   Zeigt Streak/XP, Recent Docs, Recent Quizzes.
   API: (später) /me/summary (optional) oder zusammengesetzt aus vorhandenen Endpoints.
   • Library
   Listet eigene documents (title, size, created_at).
   API: GET /documents (optional), oder Frontend liest aus Supabase-View; für MVP reicht ein minimaler GET.
   • Upload
   Upload in Storage → POST /docs/ingest → Status-Polling GET /docs/status.
   • Chat
   Dokument wählen → POST /rag/query (Streaming). Anzeige von citations.
   • Quiz
   Builder (count/types/difficulty) → POST /quiz/generate → Attempt-Page → POST /quiz/submit.
   • Settings
   Profile (display_name), Privacy toggles (UI ok). API minimal (optional), Großteil via Supabase.

⸻

8. API-Definition (v1, kurz)

Auth: Authorization: Bearer <supabase_jwt>.
• POST /docs/ingest
Req: { documentId, storagePath, mime }
Res: 202 { status:"started", documentId, jobId }
• GET /docs/status?documentId=...
Res: 200 { status: "pending"|"processing"|"ready"|"error", progress?: number }
• POST /rag/query
Req: { documentId, question }
Res: 200 { answer, citations:[{chunkId, page?, section?, textSnippet}], traceId }
Optional Streaming (SSE/Fetch Streams)
• POST /quiz/generate
Req: { documentId, config:{ count, types, difficulty } }
Res: 200 { attemptId, questions:[{id,qtype,prompt,options?,source_ref}] }
• POST /quiz/submit
Req: { attemptId, answers:[{questionId, value}] }
Res: 200 { score, breakdown:[{questionId, correct}], explanations?:[{questionId,text,source_ref}] }
• GET /health
Res: { status:"ok", version }

Fehlerformat (empfohlen):
{ type, title, status, detail, traceId }

⸻

9. Datenmodell (MVP)

profiles
• id (uuid, PK → auth.users.id), display_name, created_at

documents
• id (uuid, PK), owner_id (uuid → profiles), title, storage_path, mime_type, page_count, size_bytes, created_at

chunks
• id (uuid, PK), document_id (uuid → documents), ordinal (int), content (text), tokens (int), section_ref (text), tsv (tsvector, generated)

embeddings
• chunk_id (uuid, PK → chunks), embedding (vector(1536))

quizzes
• id, owner_id, document_id, config (jsonb), created_at

questions
• id, quiz_id, qtype, prompt, options (jsonb), answer (jsonb), explanation, source_ref

quiz_attempts
• id, quiz_id, user_id, score (numeric), duration_secs, started_at, completed_at

answers
• id, attempt_id, question_id, chosen (jsonb), correct (bool)

Indizes
• gin(tsv) auf chunks.tsv, ivfflat auf embeddings.embedding.

RLS/Policies
• Owner-Only für alle relevanten Tabellen (liegt als SQL vor).

⸻

10. Ingestion & Retrieval (Logik)

Ingestion 1. Signierte URL von Supabase Storage beziehen. 2. Datei → Unstructured/MarkItDown → Klartext + Struktur (Überschriften/Seiten). 3. Chunking: 300–800 Tokens, Overlap 10–15 %, section_ref setzen. 4. Embeddings berechnen (z. B. OpenAI 1536-dim), Insert in chunks + embeddings. 5. documents.status auf „ready“ setzen; page_count befüllen (wenn bekannt).

Retrieval 1. BM25: tsvector/tsquery → top-k (z. B. 20). 2. Vector: cosine-ähnlichkeit (embedding <=> query_embedding) → top-k (z. B. 20). 3. Merge: gewichteter Score (z. B. 0.4BM25 + 0.6Vector) → top-N (z. B. 10). 4. (V1) optional Reranking.

⸻

11. Analytics/Events (MVP)
    • doc_ingested (docId, pages, chunks, duration_ms)
    • query_submitted (docId, q_len, topk)
    • query_answered (docId, tokens_out, citations, latency_ms)
    • quiz_generated (docId, count, types)
    • quiz_submitted (attemptId, score, duration)

Keine PII im Event-Payload.

⸻

12. Risiken & Gegenmaßnahmen
    • Parsing-Fehler → Fallback auf reines Text-Extraction; Logs mit docId/traceId.
    • Halluzinationen → „No-source-no-claim“, Zitate Pflicht, Top-k/Chunk-Tuning.
    • Kosten/Latenz → Caching Embeddings, Batching, sinnvolle topk, Chunk-Größen testen.
    • RLS-Fehlkonfig → Test-Suite für Policies (positive/negative Cases).

⸻

13. Rollout-Plan (Reihenfolge für Claude Code)
    1.  Backend-Skeleton (FastAPI, /health, Settings, DB-Session, JWT-Verify).
    2.  /docs/ingest, /docs/status (Dummy → echt).
    3.  /rag/query (Dummy → Retrieval-Merge → Generation).
    4.  OpenAPI Export + typed Client im Frontend, Mocks ersetzen.
    5.  /quiz/generate, /quiz/submit (Dummy → echt).
    6.  Streaming für Chat, Basis-Observability.
    7.  E2E-Probe: Upload → Ingest → Query → Quiz.

⸻

14. Acceptance (MVP „done“)
    • Upload/Ingestion: 5+ realistische PDFs funktionieren, Status „ready“, Chunks/Embeddings vorhanden.
    • Chat: 10 Beispiel-Fragen liefern Antworten mit Zitaten, keine PII-Logs, P95 ≤ 2,5 s.
    • Quiz: 10–15 Fragen generierbar, Submit liefert Score/Breakdown, Kommentare + Quellen vorhanden.
    • OpenAPI erzeugt, Frontend nutzt generierten Client.
    • RLS verifiziert (Owner kann sehen, Fremde nicht).

⸻

15. ENV & Secrets

Frontend (.env.local)

VITE_SUPABASE_URL=
VITE_SUPABASE_ANON_KEY=
VITE_API_BASE_URL=http://localhost:8000

Backend (apps/api/.env)

DATABASE_URL=postgresql://<user>:<pass>@<host>:5432/postgres
SUPABASE_URL=
SUPABASE_ANON_KEY=
SUPABASE_SERVICE_ROLE_KEY=
OPENAI_API_KEY=
ALLOWED_ORIGINS=http://localhost:3000,https://<dein-vercel-host>

Secrets nie im Client bundlen.

⸻

16. Anhang
    • SQL (Schema/Policies): siehe supabase/migrations/0001_init.sql, 0002_policies.sql (liegt vor).
    • ASCII-Architektur: siehe docs/ARCHITECTURE.md.
    • OpenAPI-Skizze: siehe docs/OPENAPI_SKETCH.md.
