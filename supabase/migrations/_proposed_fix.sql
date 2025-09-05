-- PROPOSED SCHEMA FIX FOR STUDYRAG
-- ⚠️  NICHT automatisch ausführen! Diese SQL-Statements manuell in Supabase SQL Editor ausführen.
-- ✅ Alle Statements sind NICHT-destruktiv (keine DROP/DELETE)

-- ==================================================
-- PHASE 1: KRITISCHE LÜCKEN SCHLIEßEN
-- ==================================================

-- 1. CREATE chunks table (KRITISCH für RAG/BM25-Suche)
create table if not exists public.chunks (
  id uuid primary key default gen_random_uuid(),
  document_id uuid not null references public.documents(id) on delete cascade,
  ordinal int not null,
  content text not null,
  tokens int,
  section_ref text,
  created_at timestamptz default now(),
  tsv tsvector generated always as (to_tsvector('simple', coalesce(content,''))) stored
);

-- 2. CREATE embeddings table (KRITISCH für Vector-Suche)
create table if not exists public.embeddings (
  chunk_id uuid primary key references public.chunks(id) on delete cascade,
  embedding vector(1536) not null
);

-- 3. CREATE critical indexes für Performance
create index if not exists idx_chunks_tsv on public.chunks using gin(tsv);
create index if not exists idx_embeddings_ivfflat
  on public.embeddings using ivfflat (embedding vector_cosine_ops) with (lists = 100);
  
-- 4. Additional useful indexes
create index if not exists idx_chunks_document_id on public.chunks(document_id);
create index if not exists idx_chunks_ordinal on public.chunks(document_id, ordinal);

-- ==================================================
-- PHASE 2: RLS & POLICIES FÜR NEUE TABELLEN
-- ==================================================

-- Enable RLS on new tables
alter table public.chunks enable row level security;
alter table public.embeddings enable row level security;

-- Policies for chunks table
create policy "chunk_select_by_owner" on public.chunks
  for select using (exists (
    select 1 from public.documents d where d.id = document_id and d.user_id = auth.uid()
  ));

create policy "chunk_insert_by_owner" on public.chunks
  for insert with check (exists (
    select 1 from public.documents d where d.id = document_id and d.user_id = auth.uid()
  ));

-- Policies for embeddings table  
create policy "emb_select_by_owner" on public.embeddings
  for select using (exists (
    select 1 from public.chunks c join public.documents d on d.id = c.document_id
    where c.id = chunk_id and d.user_id = auth.uid()
  ));

create policy "emb_insert_by_owner" on public.embeddings
  for insert with check (exists (
    select 1 from public.chunks c join public.documents d on d.id = c.document_id
    where c.id = chunk_id and d.user_id = auth.uid()
  ));

-- ==================================================
-- PHASE 3: SCHEMA-HARMONISIERUNG (OPTIONAL)
-- ==================================================

-- 3a. Extend documents table with missing SOLL columns
alter table public.documents add column if not exists mime_type text;
alter table public.documents add column if not exists page_count int;

-- Rename existing columns to match SOLL (if desired)
-- ACHTUNG: Diese statements können Frontend-Code brechen!
-- Nur ausführen wenn Frontend entsprechend angepasst wird.

-- alter table public.documents rename column user_id to owner_id;
-- alter table public.documents rename column file_path to storage_path;  
-- alter table public.documents rename column file_size to size_bytes;

-- 3b. New tables to match SOLL schema
-- Ersetzt quiz_configs/quiz_questions/quiz_answers durch SOLL-Schema
-- ACHTUNG: Erfordert Datenmigration!

create table if not exists public.quizzes (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid not null references public.profiles(user_id) on delete cascade, -- Using current profiles structure
  document_id uuid not null references public.documents(id) on delete cascade,
  config jsonb not null default '{}'::jsonb,
  created_at timestamptz default now()
);

create table if not exists public.questions (
  id uuid primary key default gen_random_uuid(),
  quiz_id uuid not null references public.quizzes(id) on delete cascade,
  qtype text not null,
  prompt text not null,
  options jsonb,
  answer jsonb,
  explanation text,
  source_ref text
);

create table if not exists public.answers (
  id uuid primary key default gen_random_uuid(),
  attempt_id uuid not null references public.quiz_attempts(id) on delete cascade,
  question_id uuid not null references public.questions(id) on delete cascade,
  chosen jsonb,
  correct boolean
);

-- RLS für neue Quiz-Tabellen
alter table public.quizzes enable row level security;
alter table public.questions enable row level security;
alter table public.answers enable row level security;

-- Quiz policies (matching SOLL from 0002_policies.sql)
create policy "quiz_select_own" on public.quizzes
  for select using (auth.uid() = owner_id);
create policy "quiz_modify_own" on public.quizzes
  for all using (auth.uid() = owner_id) with check (auth.uid() = owner_id);

create policy "question_select_by_quiz_owner" on public.questions
  for select using (exists (
    select 1 from public.quizzes q where q.id = quiz_id and q.owner_id = auth.uid()
  ));

create policy "answer_select_owner_or_user" on public.answers
  for select using (exists (
    select 1 from public.quiz_attempts a
    join public.quizzes q on q.id = a.quiz_config_id  -- Using current quiz_attempts structure
    where a.id = answers.attempt_id
      and (a.user_id = auth.uid() or q.owner_id = auth.uid())
  ));

-- ==================================================
-- VERIFICATION QUERIES
-- ==================================================

-- Nach Ausführung: Diese Queries testen um zu prüfen ob alles funktioniert

-- 1. Teste ob chunks table erstellt wurde
-- select count(*) from public.chunks;

-- 2. Teste ob embeddings table erstellt wurde  
-- select count(*) from public.embeddings;

-- 3. Teste ob Indizes erstellt wurden
-- select indexname, indexdef from pg_indexes where tablename in ('chunks', 'embeddings') and schemaname='public';

-- 4. Teste ob RLS policies aktiv sind
-- select tablename, policyname, cmd from pg_policies where schemaname='public' and tablename in ('chunks', 'embeddings');

-- ==================================================
-- MIGRATION NOTES
-- ==================================================

/*
KRITISCHE DEPENDENCIES:
1. chunks & embeddings Tabellen MÜSSEN existieren bevor Backend startet
2. Backend Services erwarten diese Tabellen für Ingestion/Retrieval
3. Indizes sind performance-kritisch für BM25/Vector-Suche

MIGRATION REIHENFOLGE:
1. Erst Phase 1 ausführen (chunks, embeddings, indexes)
2. Backend implementieren und testen mit neuen Tabellen
3. Später Phase 3 für komplette Schema-Harmonisierung

COMPATIBILITY NOTES:  
- Bestehende Tabellen werden nicht verändert
- chat_messages/chat_sessions bleiben unberührt (für Chat-Feature)
- quiz_* Tabellen werden parallel erstellt (alte können später migriert werden)
- profiles/documents: nur neue Spalten hinzugefügt, keine Änderung bestehender Daten
*/