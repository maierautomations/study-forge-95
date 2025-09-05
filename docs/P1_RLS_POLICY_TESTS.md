# P1.2 - RLS Policy Tests

## Overview
Manual RLS policy validation for chunks and embeddings tables to ensure user data isolation.

## Current RLS Policies

### Chunks Table
- `chunk_select_by_owner`: Users can only SELECT chunks from their own documents
- `chunk_insert_by_owner`: Users can only INSERT chunks for their own documents

### Embeddings Table  
- `emb_select_by_owner`: Users can only SELECT embeddings from their own chunks
- `emb_insert_by_owner`: Users can only INSERT embeddings for their own chunks

## Test Scripts

### Setup Test Data
```sql
-- Run in Supabase SQL Editor to create test users and documents
-- Note: These INSERT statements will work because we're bypassing RLS as superuser

-- Insert test documents for different users
INSERT INTO documents (id, user_id, filename, title, content_type) VALUES
  ('550e8400-e29b-41d4-a716-446655440000', '11111111-1111-1111-1111-111111111111', 'test1.pdf', 'User A Document', 'application/pdf'),
  ('550e8400-e29b-41d4-a716-446655440001', '22222222-2222-2222-2222-222222222222', 'test2.pdf', 'User B Document', 'application/pdf');

-- Insert test chunks
INSERT INTO chunks (id, document_id, ordinal, content, tokens) VALUES
  ('660e8400-e29b-41d4-a716-446655440000', '550e8400-e29b-41d4-a716-446655440000', 1, 'User A chunk content', 100),
  ('660e8400-e29b-41d4-a716-446655440001', '550e8400-e29b-41d4-a716-446655440001', 1, 'User B chunk content', 100);

-- Insert test embeddings
INSERT INTO embeddings (id, chunk_id, embedding, model, created_at) VALUES
  ('770e8400-e29b-41d4-a716-446655440000', '660e8400-e29b-41d4-a716-446655440000', '[0.1,0.2,0.3]'::vector, 'text-embedding-3-small', now()),
  ('770e8400-e29b-41d4-a716-446655440001', '660e8400-e29b-41d4-a716-446655440001', '[0.4,0.5,0.6]'::vector, 'text-embedding-3-small', now());
```

### Test Case 1: User A - Positive Cases (Should SUCCEED)

```sql
-- Simulate User A (11111111-1111-1111-1111-111111111111)
-- Set the session user context
SELECT set_config('request.jwt.claims', 
  '{"sub":"11111111-1111-1111-1111-111111111111"}', true);

-- Should work: User A selects their own chunks
SELECT c.id, c.content, d.user_id 
FROM chunks c 
JOIN documents d ON d.id = c.document_id
WHERE c.document_id = '550e8400-e29b-41d4-a716-446655440000';
-- Expected: 1 row returned (User A's chunk)

-- Should work: User A selects their own embeddings  
SELECT e.id, e.model, d.user_id
FROM embeddings e
JOIN chunks c ON c.id = e.chunk_id
JOIN documents d ON d.id = c.document_id
WHERE c.document_id = '550e8400-e29b-41d4-a716-446655440000';
-- Expected: 1 row returned (User A's embedding)

-- Should work: User A inserts chunk for their own document
INSERT INTO chunks (document_id, ordinal, content, tokens)
VALUES ('550e8400-e29b-41d4-a716-446655440000', 2, 'New chunk by User A', 50);
-- Expected: INSERT successful

-- Should work: User A inserts embedding for their own chunk
INSERT INTO embeddings (chunk_id, embedding, model)
SELECT c.id, '[0.7,0.8,0.9]'::vector, 'text-embedding-3-small'
FROM chunks c 
WHERE c.document_id = '550e8400-e29b-41d4-a716-446655440000' 
AND c.ordinal = 2;
-- Expected: INSERT successful
```

### Test Case 2: User A - Negative Cases (Should FAIL)

```sql
-- Still as User A (11111111-1111-1111-1111-111111111111)
SELECT set_config('request.jwt.claims', 
  '{"sub":"11111111-1111-1111-1111-111111111111"}', true);

-- Should fail: User A tries to select User B's chunks
SELECT c.id, c.content, d.user_id 
FROM chunks c 
JOIN documents d ON d.id = c.document_id
WHERE c.document_id = '550e8400-e29b-41d4-a716-446655440001';
-- Expected: 0 rows returned (RLS blocks access)

-- Should fail: User A tries to select User B's embeddings
SELECT e.id, e.model, d.user_id
FROM embeddings e
JOIN chunks c ON c.id = e.chunk_id
JOIN documents d ON d.id = c.document_id
WHERE c.document_id = '550e8400-e29b-41d4-a716-446655440001';
-- Expected: 0 rows returned (RLS blocks access)

-- Should fail: User A tries to insert chunk for User B's document
INSERT INTO chunks (document_id, ordinal, content, tokens)
VALUES ('550e8400-e29b-41d4-a716-446655440001', 3, 'Malicious chunk by User A', 50);
-- Expected: INSERT fails with RLS violation

-- Should fail: User A tries to insert embedding for User B's chunk
INSERT INTO embeddings (chunk_id, embedding, model)
VALUES ('660e8400-e29b-41d4-a716-446655440001', '[0.1,0.2,0.3]'::vector, 'text-embedding-3-small');
-- Expected: INSERT fails with RLS violation
```

### Test Case 3: User B - Positive Cases (Should SUCCEED)

```sql
-- Simulate User B (22222222-2222-2222-2222-222222222222)
SELECT set_config('request.jwt.claims', 
  '{"sub":"22222222-2222-2222-2222-222222222222"}', true);

-- Should work: User B selects their own chunks
SELECT c.id, c.content, d.user_id 
FROM chunks c 
JOIN documents d ON d.id = c.document_id
WHERE c.document_id = '550e8400-e29b-41d4-a716-446655440001';
-- Expected: 1 row returned (User B's chunk)

-- Should work: User B selects their own embeddings
SELECT e.id, e.model, d.user_id
FROM embeddings e
JOIN chunks c ON c.id = e.chunk_id
JOIN documents d ON d.id = c.document_id
WHERE c.document_id = '550e8400-e29b-41d4-a716-446655440001';
-- Expected: 1 row returned (User B's embedding)
```

### Test Case 4: User B - Negative Cases (Should FAIL)

```sql
-- Still as User B (22222222-2222-2222-2222-222222222222)
SELECT set_config('request.jwt.claims', 
  '{"sub":"22222222-2222-2222-2222-222222222222"}', true);

-- Should fail: User B tries to select User A's chunks
SELECT c.id, c.content, d.user_id 
FROM chunks c 
JOIN documents d ON d.id = c.document_id
WHERE c.document_id = '550e8400-e29b-41d4-a716-446655440000';
-- Expected: 0 rows returned (RLS blocks access)

-- Should fail: User B tries to insert chunk for User A's document
INSERT INTO chunks (document_id, ordinal, content, tokens)
VALUES ('550e8400-e29b-41d4-a716-446655440000', 4, 'Malicious chunk by User B', 50);
-- Expected: INSERT fails with RLS violation
```

## How to Execute Tests

1. **Setup**: Run the setup script to create test data (as superuser)
2. **Execute**: Run each test case in Supabase SQL Editor
3. **Verify**: Check that positive cases succeed and negative cases fail as expected
4. **Cleanup**: Remove test data after validation

## Expected Results Summary

✅ **Positive Cases**: All legitimate operations should succeed
❌ **Negative Cases**: All cross-user access attempts should fail
🔒 **RLS Protection**: Users should only access their own data

## Cleanup Script

```sql
-- Clean up test data after testing
DELETE FROM embeddings WHERE id IN (
  '770e8400-e29b-41d4-a716-446655440000',
  '770e8400-e29b-41d4-a716-446655440001'
);

DELETE FROM chunks WHERE id IN (
  '660e8400-e29b-41d4-a716-446655440000', 
  '660e8400-e29b-41d4-a716-446655440001'
);

DELETE FROM documents WHERE id IN (
  '550e8400-e29b-41d4-a716-446655440000',
  '550e8400-e29b-41d4-a716-446655440001'
);
```

## Status: ✅ READY FOR MANUAL TESTING
RLS policies are configured and test scripts are prepared. Execute manually in Supabase SQL Editor to validate user data isolation.