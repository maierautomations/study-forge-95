# Schema Diff - StudyRAG IST vs. SOLL

## Zusammenfassung

**Status**: ❌ Kritische Lücken vorhanden  
**Aktion**: Schema-Anpassungen erforderlich vor Backend-Implementierung  
**Risiko**: RAG/Retrieval funktioniert ohne `chunks` und `embeddings` nicht  

---

## Extensions

| Extension | IST | SOLL | Status |
|-----------|-----|------|--------|
| vector | ✅ | ✅ | OK |
| pg_trgm | ✅ | ✅ | OK |
| pgcrypto | ✅ | ✅ | OK |
| pg_graphql | ✅ | - | zusätzlich |
| pg_stat_statements | ✅ | - | zusätzlich |
| plpgsql | ✅ | - | zusätzlich |
| supabase_vault | ✅ | - | zusätzlich |
| uuid-ossp | ✅ | - | zusätzlich |

**Bewertung**: ✅ Alle benötigten Extensions vorhanden

---

## Tabellen - Überblick

| Tabelle | IST | SOLL | Status | Aktion |
|---------|-----|------|--------|--------|
| profiles | ✅ (abweichend) | ✅ | ⚠️ | ALTER |
| documents | ✅ (abweichend) | ✅ | ⚠️ | ALTER |
| chunks | ❌ | ✅ | ❌ | CREATE |
| embeddings | ❌ | ✅ | ❌ | CREATE |
| quizzes | ❌ (als quiz_configs) | ✅ | ⚠️ | ALTER/MIGRATE |
| questions | ❌ (als quiz_questions) | ✅ | ⚠️ | ALTER/MIGRATE |
| quiz_attempts | ✅ (abweichend) | ✅ | ⚠️ | ALTER |
| answers | ❌ (als quiz_answers) | ✅ | ⚠️ | ALTER/MIGRATE |
| chat_sessions | ✅ | - | ➕ | bleibt |
| chat_messages | ✅ | - | ➕ | bleibt |

**Bewertung**: ❌ Kritische Tabellen `chunks`, `embeddings` fehlen

---

## Detaillierte Tabellenanalyse

### 1. profiles

**IST-Struktur:**
```sql
id (uuid, PK)
user_id (uuid, NOT NULL) -- ABWEICHUNG!
display_name (text, nullable)
created_at (timestamptz, NOT NULL)
updated_at (timestamptz, NOT NULL) -- ZUSÄTZLICH
```

**SOLL-Struktur:**
```sql
id (uuid, PK -> auth.users.id)  -- DIREKTE REFERENZ!
display_name (text, nullable)
created_at (timestamptz, default now())
```

**Problem**: IST hat `user_id` als Fremdschlüssel, SOLL hat `id` als direkte Referenz zu `auth.users.id`

### 2. documents

**IST-Struktur:**
```sql
id (uuid, PK)
user_id (uuid, NOT NULL)
title (text, NOT NULL)
filename (text, NOT NULL) -- ABWEICHUNG
file_size (bigint, NOT NULL) -- ABWEICHUNG
file_path (text, NOT NULL) -- ABWEICHUNG  
upload_date (timestamptz, NOT NULL) -- ZUSÄTZLICH
status (text, NOT NULL) -- ZUSÄTZLICH
created_at (timestamptz, NOT NULL)
updated_at (timestamptz, NOT NULL) -- ZUSÄTZLICH
```

**SOLL-Struktur:**
```sql
id (uuid, PK)
owner_id (uuid -> profiles.id) -- ABWEICHUNG: user_id vs owner_id
title (text, NOT NULL)
storage_path (text, NOT NULL) -- vs file_path
mime_type (text, nullable) -- FEHLT
page_count (int, nullable) -- FEHLT
size_bytes (bigint, nullable) -- vs file_size (NOT NULL)
created_at (timestamptz, default now())
```

### 3. chunks ❌ FEHLT KOMPLETT

**SOLL-Struktur:**
```sql
id (uuid, PK)
document_id (uuid -> documents.id)
ordinal (int, NOT NULL)
content (text, NOT NULL)
tokens (int, nullable)
section_ref (text, nullable)
created_at (timestamptz, default now())
tsv (tsvector, generated from content) -- KRITISCH für BM25
```

### 4. embeddings ❌ FEHLT KOMPLETT

**SOLL-Struktur:**
```sql
chunk_id (uuid, PK -> chunks.id)
embedding (vector(1536), NOT NULL) -- KRITISCH für Vektor-Suche
```

### 5. quiz_configs vs. quizzes

**IST (quiz_configs):**
```sql
id (uuid, PK)
user_id (uuid, NOT NULL)
document_id (uuid, NOT NULL)
title (text, NOT NULL) -- ZUSÄTZLICH
num_questions (int, NOT NULL) -- ZUSÄTZLICH
difficulty (text, NOT NULL) -- ZUSÄTZLICH  
question_types (ARRAY, NOT NULL) -- ZUSÄTZLICH
created_at (timestamptz, NOT NULL)
updated_at (timestamptz, NOT NULL) -- ZUSÄTZLICH
```

**SOLL (quizzes):**
```sql
id (uuid, PK)
owner_id (uuid -> profiles.id)
document_id (uuid -> documents.id) 
config (jsonb, default '{}') -- vs. separate columns
created_at (timestamptz, default now())
```

---

## Indizes

### Vorhanden (IST)
```sql
-- Primary Keys und Foreign Keys automatisch indexiert
-- Zusätzlich:
idx_documents_user_id, idx_documents_status
idx_chat_sessions_user_id, idx_chat_sessions_document_id
idx_quiz_attempts_user_id, idx_quiz_attempts_status
-- ... (weitere)
```

### Benötigt (SOLL)
```sql
-- FEHLEN KOMPLETT:
idx_chunks_tsv ON chunks USING gin(tsv) -- KRITISCH für BM25
idx_embeddings_ivfflat ON embeddings USING ivfflat(embedding vector_cosine_ops) -- KRITISCH für Vector-Suche
```

---

## RLS & Policies

**IST-Status**: ✅ Alle Tabellen haben RLS aktiviert  
**Policies**: User-basierte Policies implementiert (via `auth.uid() = user_id`)

**Problem**: Policies verwenden `user_id`, SOLL verwendet `owner_id`

### Beispiel-Policy (IST):
```sql
"Users can view their own documents" 
FOR SELECT USING (auth.uid() = user_id)
```

### SOLL-Policy:
```sql
"doc_select_own" ON documents
FOR SELECT USING (auth.uid() = owner_id)
```

---

## Storage

**IST**: ✅ Bucket `documents` vorhanden (public=false)  
**SOLL**: ✅ Bucket `documents` (private)

**Bewertung**: ✅ OK

---

## Migration-Strategie

### Phase 1: Kritische Lücken schließen
1. ❗ CREATE TABLE chunks (mit tsvector)
2. ❗ CREATE TABLE embeddings (mit vector index) 
3. ❗ CREATE benötigte Indizes

### Phase 2: Schema-Harmonisierung  
4. ALTER TABLE profiles (user_id -> direkte Referenz)
5. ALTER TABLE documents (Spalten anpassen)
6. MIGRATE quiz_* Tabellen zu SOLL-Schema

### Phase 3: Policy-Updates
7. UPDATE policies (user_id -> owner_id)
8. CREATE policies für neue Tabellen

---

## Risiko-Assessment

🚨 **Kritisch**: Ohne `chunks` und `embeddings` kein RAG möglich  
⚠️ **Hoch**: Schema-Inkompatibilität zwischen Frontend und geplanter API  
⚠️ **Mittel**: Policy-Anpassungen für neue Tabellenstruktur  

**Empfehlung**: Erst Schema-Fix, dann Backend-Entwicklung