# OpenAPI Sketch (v1) — StudyRAG

## Auth

- Supabase JWT im `Authorization: Bearer <token>` Header.
- Jede Anfrage wird serverseitig verifiziert.

## Endpoints

### POST /docs/ingest

Startet die Ingestion für ein bereits in Supabase Storage hochgeladenes Dokument.

- Req: `{ documentId: string, storagePath: string, mime: string }`
- Res: `202 { status: "started", documentId, jobId }`

### GET /docs/status

Liefert den Ingestion-Fortschritt.

- Query: `?documentId=...`
- Res: `200 { status: "pending"|"processing"|"ready"|"error", progress?: number }`

### POST /rag/query

Stellt eine Frage zu einem Dokument.

- Req: `{ documentId: string, question: string }`
- Res: `200 { answer: string, citations: [{ chunkId: string, page?: number, section?: string, textSnippet: string }], traceId: string }`
- Streaming (optional): `text/event-stream`/Fetch-Streams

### POST /quiz/generate

Erzeugt ein Quiz aus Dokumentinhalten.

- Req: `{ documentId: string, config: { count: number, types: ("mc"|"tf"|"short")[], difficulty: "easy"|"medium"|"hard" } }`
- Res: `200 { attemptId: string, questions: [{ id, qtype, prompt, options?, source_ref }] }`

### POST /quiz/submit

Bewertet einen Versuch.

- Req: `{ attemptId: string, answers: [{ questionId: string, value: any }] }`
- Res: `200 { score: number, breakdown: [{ questionId: string, correct: boolean }], explanations?: [{ questionId, text, source_ref }] }`

### GET /health

- Res: `{ status: "ok", version: string }`

## Modelle (Pydantic)

- Shared: `DocId`, `IngestRequest`, `IngestStatus`, `RagQuery`, `RagAnswer`, `QuizConfig`, `QuizGenerateResp`, `QuizSubmitReq`, `QuizSubmitResp`.
- Fehler: RFC7807-ähnliche Struktur `{ type, title, status, detail, traceId }`.

## Codegen im Frontend

- `openapi-typescript` erzeugt Typen/Client in `src/lib/api/generated`.
- API-Base stammt aus `VITE_API_BASE_URL`.
