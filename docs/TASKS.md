# StudyRAG Umsetzungsplan - P0 bis P5

## 🎯 Zielbild MVP

StudyRAG: Dokumente hochladen → RAG-Chat mit Zitaten → Quizze generieren → personalisiert üben  
**Backend**: FastAPI mit OpenAPI → **Frontend**: Vite+React mit generated Client  
**Stack**: Supabase (Postgres+pgvector) + EU-Compliance + RLS

---

## 🚨 PREREQUISITE: Schema-Fix

**Vor jeder Implementierung**:

1. ❗ `supabase/migrations/_proposed_fix.sql` manuell in Supabase SQL Editor ausführen
2. ✅ Verifizieren: Tabellen `chunks` und `embeddings` existieren mit Indizes
3. ✅ RLS policies für neue Tabellen aktiv

**Ohne Schema-Fix**: RAG/Retrieval funktioniert NICHT.

---

# P0 — Backend-Skeleton & Health

**Ziel**: Funktionierendes FastAPI mit /health, JWT-Verify, DB-Connection  
**Duration**: 2-3h  
**Blocker**: Schema-Fix

## Subtasks

### P0.1 - FastAPI Project Setup

**Dateien**:

```
apps/api/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app, CORS, middleware
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py           # Pydantic Settings
│   │   └── auth.py            # JWT verification
│   ├── db/
│   │   ├── __init__.py
│   │   └── session.py         # asyncpg connection
│   └── api/
│       ├── __init__.py
│       └── health.py          # /health endpoint
├── pyproject.toml             # dependencies
├── .env.example              # template
└── README.md                 # setup instructions
```

**Dependencies (pyproject.toml)**:

```toml
[tool.poetry.dependencies]
python = "^3.11"
fastapi = "^0.104.1"
uvicorn = {extras = ["standard"], version = "^0.24.0"}
pydantic-settings = "^2.1.0"
httpx = "^0.25.2"
asyncpg = "^0.29.0"
python-dotenv = "^3.0.0"
supabase = "^2.3.0"
```

**ENV (.env.example)**:

```bash
DATABASE_URL=postgresql://user:pass@host:5432/postgres
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=eyJ...
SUPABASE_SERVICE_ROLE_KEY=eyJ...
OPENAI_API_KEY=sk-...
ALLOWED_ORIGINS=http://localhost:3000
```

**Akzeptanzkriterien**:

- ✅ `GET /health` returns `{"status": "ok", "version": "0.1.0"}`
- ✅ CORS configured für localhost:3000
- ✅ JWT verify funktioniert (Dummy-Test mit Supabase JWT)
- ✅ DB connection erfolgreich (SELECT 1)

### P0.2 - Basic Project Structure

**Commands**:

```bash
cd apps/api
poetry install
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
curl http://localhost:8000/health
```

**Test lokal**: Frontend sollte API unter `VITE_API_BASE_URL=http://localhost:8000` erreichen

---

# P1 — Supabase Schema & Policies validieren

**Ziel**: Verify Schema-Fix, RLS funktioniert, Test-Suite für Policies  
**Duration**: 1-2h  
**Dependency**: P0 + Schema-Fix ausgeführt

## Subtasks

### P1.1 - Schema Validation via MCP

**Dateien**:

- `apps/api/app/db/validation.py` - Schema validation functions
- `apps/api/tests/test_schema.py` - Automated schema tests

**MCP Read-Only Checks**:

1. `SELECT count(*) FROM chunks` → sollte 0 sein (table exists)
2. `SELECT count(*) FROM embeddings` → sollte 0 sein (table exists)
3. `SELECT indexname FROM pg_indexes WHERE tablename='chunks' AND indexname='idx_chunks_tsv'` → sollte existieren
4. `SELECT indexname FROM pg_indexes WHERE tablename='embeddings' AND indexname LIKE '%ivfflat%'` → sollte existieren

**Akzeptanzkriterien**:

- ✅ chunks, embeddings Tabellen existieren
- ✅ BM25 Index (GIN auf tsv) und Vector Index (IVFFLAT) vorhanden
- ✅ RLS policies für chunks/embeddings aktiv

### P1.2 - RLS Policy Tests (Manual)

**Test-Cases**:

**Positive Cases** (sollte funktionieren):

```sql
-- Als User A: Insert chunk für eigenes Dokument
-- Als User A: SELECT chunks für eigene Dokumente
-- Als User A: INSERT embeddings für eigene chunks
```

**Negative Cases** (sollte FEHLSCHLAGEN):

```sql
-- Als User A: SELECT chunks von User B's Dokumenten
-- Als User A: INSERT chunk für fremdes Dokument
-- Als User A: SELECT embeddings von fremden chunks
```

**How-to-Test**: Manuell in Supabase SQL Editor mit verschiedenen `auth.uid()` simulieren

---

# P2 — OpenAPI & Endpoints v1

**Ziel**: Alle API-Endpoints implementiert, OpenAPI exportiert, Frontend-Client generiert  
**Duration**: 4-6h  
**Dependency**: P1

## Subtasks

### P2.1 - Pydantic Models & OpenAPI Setup

**Dateien**:

```
apps/api/app/
├── models/
│   ├── __init__.py
│   ├── documents.py          # DocumentBase, IngestRequest, StatusResponse
│   ├── rag.py               # RagQuery, RagResponse, Citation
│   ├── quiz.py              # QuizConfig, QuizGenerate, QuizSubmit
│   └── common.py            # ErrorResponse, BaseModel extensions
├── api/
│   ├── v1/
│   │   ├── __init__.py
│   │   ├── documents.py     # /docs/* endpoints
│   │   ├── rag.py           # /rag/* endpoints
│   │   └── quiz.py          # /quiz/* endpoints
│   └── deps.py              # Dependencies (auth, db)
└── openapi/
    └── __init__.py          # OpenAPI export logic
```

**Key Models**:

```python
# models/documents.py
class IngestRequest(BaseModel):
    documentId: str
    storagePath: str
    mime: str

class IngestResponse(BaseModel):
    status: Literal["started"]
    documentId: str
    jobId: str

# models/rag.py
class RagQuery(BaseModel):
    documentId: str
    question: str

class Citation(BaseModel):
    chunkId: str
    page: Optional[int] = None
    section: Optional[str] = None
    textSnippet: str

class RagResponse(BaseModel):
    answer: str
    citations: List[Citation]
    traceId: str
```

### P2.2 - Endpoint Implementation (Dummy/Stub)

**Phase 1: Dummy Responses** (für OpenAPI generation)

**POST /docs/ingest**:

```python
@router.post("/ingest", response_model=IngestResponse)
async def ingest_document(request: IngestRequest, user: User = Depends(get_current_user)):
    # DUMMY: Return success without actual processing
    return IngestResponse(
        status="started",
        documentId=request.documentId,
        jobId=str(uuid.uuid4())
    )
```

**GET /docs/status**:

```python
@router.get("/status", response_model=StatusResponse)
async def get_status(documentId: str):
    # DUMMY: Always return "ready"
    return StatusResponse(status="ready", progress=100)
```

**POST /rag/query**:

```python
@router.post("/query", response_model=RagResponse)
async def rag_query(request: RagQuery, user: User = Depends(get_current_user)):
    # DUMMY: Return hardcoded response with fake citations
    return RagResponse(
        answer="This is a dummy response to your question about the document.",
        citations=[
            Citation(chunkId="dummy-chunk-1", page=1, textSnippet="Relevant text snippet...")
        ],
        traceId=str(uuid.uuid4())
    )
```

**POST /quiz/generate** & **POST /quiz/submit**: Similar dummy patterns.

### P2.3 - OpenAPI Export & Frontend Client

**Export Script**:

```python
# apps/api/export_openapi.py
import json
from app.main import app

def export_openapi():
    with open("apps/api/openapi/openapi.json", "w") as f:
        json.dump(app.openapi(), f, indent=2)

if __name__ == "__main__":
    export_openapi()
```

**Frontend Client Generation**:

```bash
# In Frontend root
npm install openapi-typescript
npx openapi-typescript apps/api/openapi/openapi.json -o src/lib/api/generated.ts
```

**Akzeptanzkriterien P2**:

- ✅ Alle 6 Endpoints implementiert (wenn auch als Dummy)
- ✅ OpenAPI JSON exportiert nach `apps/api/openapi/openapi.json`
- ✅ Frontend kann Typen aus `src/lib/api/generated.ts` importieren
- ✅ Alle Endpoints antworten 200 (Dummy-Daten ok)
- ✅ JWT-Auth für geschützte Endpoints funktioniert

**Local Testing**:

- `curl -H "Authorization: Bearer $JWT" http://localhost:8000/docs/ingest`
- Frontend API-Calls ersetzen Mocks durch echte HTTP-Requests

---

# P3 — Ingestion Pipeline

**Ziel**: PDF/DOCX → Unstructured → Chunks → Embeddings → DB  
**Duration**: 6-8h  
**Dependency**: P2

## Subtasks

### P3.1 - Document Processing Service

**Dateien**:

```
apps/api/app/
├── services/
│   ├── __init__.py
│   ├── ingestion.py         # Main ingestion orchestrator
│   ├── extraction.py        # Unstructured/MarkItDown wrapper
│   ├── chunking.py          # Text chunking logic
│   └── embeddings.py        # OpenAI embeddings API
└── workers/
    ├── __init__.py
    └── document_processor.py  # Background task processing
```

**Dependencies** (add to pyproject.toml):

(already implemented in pyproject.toml?)

```toml
unstructured = "^0.18.0"
markitdown = "^0.1.0"
openai = "^1.104.0"
tiktoken = "^0.11.0"  # for token counting
```

**Key Functions**:

```python
# services/extraction.py
async def extract_text_from_file(file_path: str, mime_type: str) -> ExtractedContent:
    """PDF/DOCX → structured text with sections/pages"""

# services/chunking.py
def create_chunks(content: ExtractedContent, chunk_size: int = 500, overlap: float = 0.12) -> List[Chunk]:
    """Text → 300-800 token chunks with 10-15% overlap"""

# services/embeddings.py
async def generate_embeddings(texts: List[str]) -> List[List[float]]:
    """Texts → OpenAI embeddings (1536-dim)"""
```

### P3.2 - Database Operations

**Datei**: `apps/api/app/db/operations.py`

**Key Functions**:

```python
async def insert_chunks(document_id: str, chunks: List[ChunkData]) -> List[str]:
    """Bulk insert chunks with automatic tsv generation"""

async def insert_embeddings(chunk_embeddings: List[Tuple[str, List[float]]]) -> None:
    """Bulk insert embeddings with pgvector format"""

async def update_document_status(document_id: str, status: str, page_count: int = None) -> None:
    """Update document processing status"""
```

### P3.3 - Async Job Processing

**Pattern**: Background task mit Status-Updates

```python
# workers/document_processor.py
async def process_document_async(document_id: str, storage_path: str, mime_type: str):
    try:
        await update_document_status(document_id, "processing")

        # 1. Extract
        content = await extract_text_from_file(storage_path, mime_type)

        # 2. Chunk
        chunks = create_chunks(content)
        chunk_ids = await insert_chunks(document_id, chunks)

        # 3. Embed
        texts = [c.content for c in chunks]
        embeddings = await generate_embeddings(texts)
        await insert_embeddings(list(zip(chunk_ids, embeddings)))

        # 4. Complete
        await update_document_status(document_id, "ready", content.page_count)

    except Exception as e:
        await update_document_status(document_id, "error")
        raise
```

**Akzeptanzkriterien P3**:

- ✅ Beispiel-PDF (5-10 Seiten) wird erfolgreich verarbeitet
- ✅ chunks Tabelle enthält ~15-30 Chunks (je nach PDF-Größe)
- ✅ embeddings Tabelle enthält entsprechende Vektoren
- ✅ `GET /docs/status` zeigt "ready" nach Completion
- ✅ Fehler-Cases (beschädigte PDF) führen zu status="error"

**Lokaler Test**:

1. PDF in Supabase Storage hochladen
2. `POST /docs/ingest` aufrufen
3. Status-Polling bis "ready"
4. `SELECT count(*) FROM chunks WHERE document_id = '...'` → sollte >0 sein

---

# P4 — Retrieval (Hybrid Search)

**Ziel**: BM25 + Vector Search → Merged Results für RAG-Queries  
**Duration**: 4-5h  
**Dependency**: P3

## Subtasks

### P4.1 - Search Services Implementation

**Dateien**:

```
apps/api/app/services/
├── search.py              # Main search orchestrator
├── bm25.py               # tsvector/tsquery search
├── vector_search.py      # pgvector cosine similarity
└── merger.py             # Result ranking & merging
```

**Key Functions**:

```python
# services/bm25.py
async def bm25_search(query: str, document_id: str, user_id: str, limit: int = 20) -> List[SearchResult]:
    """
    SELECT c.id, c.content, c.section_ref,
           ts_rank_cd(c.tsv, plainto_tsquery('simple', $1)) as score
    FROM chunks c JOIN documents d ON d.id = c.document_id
    WHERE d.user_id = $2 AND d.id = $3 AND c.tsv @@ plainto_tsquery('simple', $1)
    ORDER BY score DESC LIMIT $4
    """

# services/vector_search.py
async def vector_search(query_embedding: List[float], document_id: str, user_id: str, limit: int = 20) -> List[SearchResult]:
    """
    SELECT c.id, c.content, c.section_ref,
           1 - (e.embedding <=> $1) as score
    FROM embeddings e
    JOIN chunks c ON c.id = e.chunk_id
    JOIN documents d ON d.id = c.document_id
    WHERE d.user_id = $2 AND d.id = $3
    ORDER BY e.embedding <=> $1 LIMIT $4
    """

# services/merger.py
def merge_search_results(bm25_results: List[SearchResult], vector_results: List[SearchResult],
                        bm25_weight: float = 0.4, vector_weight: float = 0.6) -> List[SearchResult]:
    """Combine & rank results by weighted score"""
```

### P4.2 - RAG Query Implementation

**Update**: `apps/api/app/api/v1/rag.py`

```python
@router.post("/query", response_model=RagResponse)
async def rag_query(request: RagQuery, user: User = Depends(get_current_user)):
    # 1. Generate query embedding
    query_embedding = await generate_embeddings([request.question])

    # 2. Search (parallel)
    bm25_task = bm25_search(request.question, request.documentId, user.id)
    vector_task = vector_search(query_embedding[0], request.documentId, user.id)
    bm25_results, vector_results = await asyncio.gather(bm25_task, vector_task)

    # 3. Merge results
    merged_results = merge_search_results(bm25_results, vector_results)
    top_chunks = merged_results[:10]  # Top-10 für Context

    # 4. Generate answer (Stub for now)
    answer = await generate_answer(request.question, top_chunks)

    # 5. Format citations
    citations = [
        Citation(
            chunkId=chunk.id,
            page=chunk.page,
            section=chunk.section_ref,
            textSnippet=chunk.content[:200] + "..."
        ) for chunk in top_chunks[:5]  # Top-5 als Citations
    ]

    return RagResponse(answer=answer, citations=citations, traceId=str(uuid.uuid4()))
```

### P4.3 - Answer Generation (LLM Integration)

**Datei**: `apps/api/app/services/generation.py`

```python
async def generate_answer(question: str, context_chunks: List[SearchResult]) -> str:
    """Generate answer using LLM with retrieved context"""

    # Build context from top chunks
    context = "\n\n---\n\n".join([
        f"[Section: {chunk.section_ref or 'Unknown'}]\n{chunk.content}"
        for chunk in context_chunks
    ])

    prompt = f"""Based on the following document excerpts, answer the user's question.
Only use information from the provided context. If you cannot find relevant information, say so.

Context:
{context}

Question: {question}

Answer:"""

    # Call OpenAI API
    response = await openai.ChatCompletion.acreate(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=400,
        temperature=0.1
    )

    return response.choices[0].message.content
```

**Akzeptanzkriterien P4**:

- ✅ BM25 Search funktioniert (findet Text-matches)
- ✅ Vector Search funktioniert (findet semantische matches)
- ✅ Merge liefert sinnvolles Ranking
- ✅ RAG Query mit echtem PDF liefert relevante Antwort mit Zitaten
- ✅ P95 Latenz ≤ 3s (für typisches 30-Seiten PDF)

**Test Cases**:

1. Exact match: Frage nach Begriff der wörtlich im PDF steht
2. Semantic match: Frage nach Konzept das synonym beschrieben ist
3. No match: Frage zu Thema das nicht im PDF behandelt wird → sollte "keine Information gefunden" antworten

---

# P5 — Quiz-Engine MVP

**Ziel**: Quiz-Generation aus Chunks, Attempt/Submit/Scoring  
**Duration**: 5-7h  
**Dependency**: P4

## Subtasks

### P5.1 - Quiz Generation Service

**Dateien**:

```
apps/api/app/services/
├── quiz_generation.py      # Main quiz orchestrator
├── question_generator.py   # LLM-based question generation
└── quiz_storage.py        # DB operations for quizzes
```

**Quiz Generation Flow**:

```python
# services/quiz_generation.py
async def generate_quiz(document_id: str, user_id: str, config: QuizConfig) -> QuizAttempt:
    # 1. Sample relevant chunks (spread across document)
    chunks = await sample_chunks_for_quiz(document_id, config.count * 2)  # Oversample

    # 2. Generate questions via LLM
    questions = []
    for chunk in chunks:
        if len(questions) >= config.count:
            break
        question = await generate_question_from_chunk(chunk, config.types, config.difficulty)
        if question:  # Filter out low-quality questions
            questions.append(question)

    # 3. Store quiz & questions in DB
    quiz_id = await store_quiz(user_id, document_id, config)
    attempt_id = await create_quiz_attempt(quiz_id, user_id)
    await store_questions(attempt_id, questions)

    return QuizAttempt(attemptId=attempt_id, questions=questions)
```

**Question Generation**:

```python
# services/question_generator.py
async def generate_question_from_chunk(chunk: ChunkData, types: List[str], difficulty: str) -> Optional[QuestionData]:
    """Generate MC/TF/Short question from text chunk"""

    question_type = random.choice(types)

    if question_type == "mc":
        prompt = f"""Based on this text, create a multiple choice question (difficulty: {difficulty}).

Text: {chunk.content}

Generate:
1. Question (clear, specific)
2. 4 answer options (A, B, C, D)
3. Correct answer (A/B/C/D)
4. Brief explanation
5. Source reference

Format as JSON:
{{"question": "...", "options": {{"A": "...", "B": "...", "C": "...", "D": "..."}}, "correct": "A", "explanation": "...", "source_ref": "..."}}"""

    # Similar prompts for "tf" (true/false) and "short" (short answer)

    response = await call_llm(prompt)
    return parse_question_response(response, question_type)
```

### P5.2 - Quiz Attempt & Scoring

**Update**: `apps/api/app/api/v1/quiz.py`

```python
@router.post("/submit", response_model=QuizSubmitResponse)
async def submit_quiz(request: QuizSubmitRequest, user: User = Depends(get_current_user)):
    # 1. Load attempt & questions
    attempt = await get_quiz_attempt(request.attemptId, user.id)
    questions = await get_attempt_questions(request.attemptId)

    # 2. Score each answer
    results = []
    total_score = 0
    max_score = 0

    for answer in request.answers:
        question = next(q for q in questions if q.id == answer.questionId)
        is_correct = evaluate_answer(question, answer.value)
        points = question.points if is_correct else 0

        results.append({
            "questionId": answer.questionId,
            "correct": is_correct,
            "points": points,
            "maxPoints": question.points
        })

        total_score += points
        max_score += question.points

    # 3. Store results
    await store_quiz_results(request.attemptId, total_score, max_score, results)

    # 4. Generate explanations
    explanations = [
        {
            "questionId": r["questionId"],
            "text": questions[i].explanation,
            "source_ref": questions[i].source_ref
        } for i, r in enumerate(results) if not r["correct"]  # Only wrong answers
    ]

    return QuizSubmitResponse(
        score=total_score,
        maxScore=max_score,
        breakdown=results,
        explanations=explanations
    )
```

### P5.3 - Answer Evaluation Logic

**Datei**: `apps/api/app/services/scoring.py`

```python
def evaluate_answer(question: QuestionData, user_answer: Any) -> bool:
    """Evaluate user answer against correct answer"""

    if question.qtype == "mc":
        return str(user_answer).upper() == question.answer["correct"]

    elif question.qtype == "tf":
        return bool(user_answer) == question.answer["correct"]

    elif question.qtype == "short":
        # Fuzzy matching for short answers
        correct_answer = question.answer["correct"].lower().strip()
        user_input = str(user_answer).lower().strip()

        # Exact match or contains key terms
        return user_input == correct_answer or all(
            term in user_input for term in correct_answer.split() if len(term) > 2
        )

    return False
```

**Akzeptanzkriterien P5**:

- ✅ Quiz mit 10-15 Fragen generiert (Mixed MC/TF/Short)
- ✅ Jede Frage hat source_ref (zeigt auf relevanten Chunk)
- ✅ Submit zeigt Score + Breakdown + Explanations für falsche Antworten
- ✅ Quiz-Attempts werden in DB gespeichert (für spätere Analytics)
- ✅ Edge-Case: Leeres Quiz bei zu kurzem/unpassendem Dokument

**Test Cases**:

1. Standard Quiz: 30-Seiten PDF → 15 Fragen → Submit → Score & Explanations
2. Short Doc: 3-Seiten PDF → 5 Fragen (weniger als gewünscht, aber funktional)
3. Bad Input: Corrupted answer format → proper error handling

---

# Querschnitt — Logging, Tests & CI

## Logging Strategy

**Datei**: `apps/api/app/core/logging.py`

**Principles**:

- ✅ Strukturierte JSON-Logs (für Prod-Observability)
- ❌ Keine PII in Logs (keine user_id, document content, quiz answers)
- ✅ Trace-ID für Request-Verfolgung
- ✅ Performance-Metriken (latency, chunk-counts, scores)

**Example Events**:

```python
logger.info("doc_ingestion_started", extra={
    "trace_id": trace_id,
    "document_id": doc_id,  # UUID ok
    "mime_type": mime_type,
    "file_size_bytes": file_size
})

logger.info("rag_query_completed", extra={
    "trace_id": trace_id,
    "document_id": doc_id,
    "query_length": len(query),
    "chunks_retrieved": len(chunks),
    "response_length": len(answer),
    "latency_ms": elapsed_ms
})
```

## Test Strategy

**Directories**:

```
apps/api/tests/
├── unit/
│   ├── test_chunking.py       # Chunk logic
│   ├── test_search.py         # BM25/Vector search
│   └── test_scoring.py        # Quiz evaluation
├── integration/
│   ├── test_ingestion.py      # End-to-end document processing
│   ├── test_rag_flow.py       # Query → Search → Generate
│   └── test_quiz_flow.py      # Generate → Submit → Score
└── fixtures/
    ├── sample.pdf             # Test document
    └── test_data.sql          # DB test data
```

**Coverage Target**: ≥80% für Services, ≥60% overall

## CI Hooks

**Github Actions** (`.github/workflows/api.yml`):

```yaml
- Run: poetry run pytest apps/api/tests/
- Run: poetry run black apps/api/ --check
- Run: poetry run isort apps/api/ --check-only
- Run: poetry run mypy apps/api/app/
- Export: OpenAPI spec & upload as artifact
```

---

# Go/No-Go Checkliste (MVP Ready)

## Database ✓

- [ ] ✅ chunks & embeddings Tabellen vorhanden mit korrekten Indizes
- [ ] ✅ RLS Policies für alle Tabellen funktionieren
- [ ] ✅ Storage bucket `documents` konfiguriert

## API ✓

- [ ] ✅ Alle 6 Endpoints implementiert und funktionsfähig
- [ ] ✅ OpenAPI JSON exportiert nach `apps/api/openapi/openapi.json`
- [ ] ✅ JWT Authentication für protected routes
- [ ] ✅ Error Handling & structured logging

## Core Features ✓

- [ ] ✅ PDF Ingestion: 30-Seiten PDF → ~20-40 chunks → embeddings
- [ ] ✅ RAG Query: Question → BM25+Vector search → Answer mit citations
- [ ] ✅ Quiz: Generate 15 questions → Submit answers → Score mit explanations

## Frontend Integration ✓

- [ ] ✅ API Client generiert aus OpenAPI
- [ ] ✅ Upload/Chat/Quiz flows verwenden echte API (keine Mocks)
- [ ] ✅ Citations werden in Chat-UI angezeigt

## Performance & Reliability ✓

- [ ] ✅ P95 RAG Query ≤ 3s (nach ingestion)
- [ ] ✅ Fehlerhafte Uploads führen zu status="error" (nicht crash)
- [ ] ✅ Tests laufen grün (Unit + Integration)

## Compliance ✓

- [ ] ✅ Keine PII in Logs
- [ ] ✅ Secrets korrekt konfiguriert (nicht in Code)
- [ ] ✅ RLS verhindert Cross-User-Access

---

**Bei Go**: MVP ist Production-Ready für erste User Tests  
**Bei No-Go**: Zurück zu fehlgeschlagenen Items in entsprechender Priorität
