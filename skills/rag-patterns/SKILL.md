---
name: rag-patterns
description: RAG pipeline patterns — chunking, embedding, hybrid search, context engineering, evaluation, and common pitfalls for local AI knowledge bases
triggers:
  - rag
  - retrieval augmented generation
  - embedding
  - chunking
  - vector search
  - hybrid search
  - knowledge base
  - qdrant
  - ingestion pipeline
---

# Skill — RAG Patterns

Activate when building, debugging, or reviewing any component of a RAG pipeline.

---

## 1 — Chunking Strategies

**Fixed-size (default for prose):**
- Target: 400–600 tokens per chunk
- Overlap: 50 tokens (preserves context across boundaries)
- Unit: token count, not character count — use a tokenizer

**Semantic chunking (Markdown/structured docs):**
- Split on headers (`#`, `##`, `###`) first
- If a section exceeds 600 tokens, apply fixed-size splitting within it
- Never split mid-sentence or mid-code-block

**Code chunking:**
- Split by logical block (function, class) not by size
- Keep the full function/class in one chunk even if > 600 tokens
- Add language metadata to chunk payload

**Required metadata on every chunk:**
```python
{
    "id": uuid5(NAMESPACE, source_path + str(chunk_index)),  # deterministic, idempotent
    "source_path": str,
    "source_type": "markdown" | "pdf" | "url" | "code",
    "chunk_index": int,
    "total_chunks": int,
    "title": str | None,          # document title if available
    "created_at": datetime,
}
```

**Golden rule:** chunk IDs MUST be deterministic — same source + same index = same ID. This enables idempotent re-ingestion without duplicates.

---

## 2 — Embedding Pipeline

**Never embed in an API route** — always in a background worker (queue-based).

**Pattern:**
```python
# 1. API route: enqueue, return immediately
job = queue.enqueue(ingest_job, file_path)
return {"job_id": job.id, "status": "queued"}

# 2. Worker: parse → chunk → embed → store
chunks = loader.load(file_path)         # type-specific loader
chunks = chunker.split(chunks)          # fixed-size or semantic
chunks = embedder.embed_chunks(chunks)  # batch embedding
qdrant.upsert(chunks)                   # idempotent by chunk ID
postgres.save_document(metadata)        # metadata + FTS index
```

**Batch embedding:** process chunks in groups of 10-20, not one-by-one. Reduces model load/unload overhead.

**Retry pattern for local models (timeouts are common):**
```python
for attempt in range(3):
    try:
        return embed(text)
    except (httpx.TimeoutException, httpx.ConnectError):
        if attempt == 2:
            raise
        await asyncio.sleep(2 ** attempt)
```

**Current Akela endpoint (do not change):**
- POST `http://host.docker.internal:11434/api/embed`
- Body: `{"model": "mxbai-embed-large", "input": text}`
- Response: `resp.json()["embeddings"][0]` (list of floats, 1024 dims)

---

## 3 — Hybrid Search

Never use semantic-only search — it fails on exact queries (names, dates, code, quotes).

**Pattern: Semantic + FTS + RRF**

```
1. Semantic search → top-20 chunks (Qdrant cosine similarity)
2. FTS search      → top-20 chunks (Postgres tsvector/tsquery)
3. RRF merge       → combine and rerank using Reciprocal Rank Fusion
4. Return top-k    → typically k=5 for context, k=10 for comprehensive
```

**Reciprocal Rank Fusion (k=60):**
```python
def rrf(semantic_ids, fts_ids, k=60):
    scores = {}
    for rank, doc_id in enumerate(semantic_ids):
        scores[doc_id] = scores.get(doc_id, 0) + 1 / (k + rank + 1)
    for rank, doc_id in enumerate(fts_ids):
        scores[doc_id] = scores.get(doc_id, 0) + 1 / (k + rank + 1)
    return sorted(scores, key=scores.get, reverse=True)
```

**Postgres FTS setup:**
```sql
ALTER TABLE chunks ADD COLUMN fts_vector tsvector
    GENERATED ALWAYS AS (to_tsvector('english', content)) STORED;
CREATE INDEX idx_chunks_fts ON chunks USING GIN(fts_vector);
```

**Query:**
```sql
SELECT id, content, ts_rank(fts_vector, query) as rank
FROM chunks, plainto_tsquery('english', :query) query
WHERE fts_vector @@ query
ORDER BY rank DESC LIMIT 20;
```

---

## 4 — Context Engineering for RAG

**System prompt structure:**
```
[Role definition — who the assistant is]
[Rules — cite sources, don't hallucinate, admit gaps, match user language]
[Context block — numbered retrieved chunks with source labels]
```

**Context block format:**
```
CONTESTO DAI DOCUMENTI:

[1] Fonte: {title or source_path}
{chunk content}

---

[2] Fonte: {title or source_path}
{chunk content}
```

**Conversation memory (sliding window + summarization):**
- Pass last N messages (default: 4 pairs = 8 messages) as recent context
- Every M messages (default: 6), summarize the full history with the LLM
- Store summary in `conversations.summary` column
- Next turn: inject summary as a SystemMessage before the sliding window

**Token budget management:**
- System prompt + context: aim for < 2000 tokens
- Sliding window: < 800 tokens
- User query: < 200 tokens
- Leave > 1000 tokens for generation

---

## 5 — RAG Evaluation

**Retrieval quality check (manual spot-check protocol):**
1. Pick 10 queries with known answers in the knowledge base
2. Run hybrid search, record top-5 chunks returned
3. Check: does the correct source appear in top-5? → Precision@5
4. Target: 80%+ for production use

**Answer faithfulness check:**
1. For each answer, verify every factual claim maps to a cited chunk
2. If the answer contains information not in any chunk → hallucination
3. Target: 0 hallucinations on spot-check set

**Citation accuracy:**
1. Each `[N]` citation in the answer should reference the chunk that actually contains that information
2. Check: does chunk N contain the sentence it's cited for?

**Baseline metrics to track (log to DB or file):**
```python
{
    "query": str,
    "chunks_retrieved": int,
    "top_chunk_score": float,
    "answer_length_tokens": int,
    "citations_count": int,
    "latency_ms": int,
    "model": str,
    "timestamp": datetime,
}
```

---

## 6 — Common Pitfalls

| Trap | Effect | Fix |
|------|--------|-----|
| Chunks > 1000 tokens | LLM can't extract relevant part; citations imprecise | Target 400-600 tokens |
| Non-idempotent chunk IDs | Duplicate vectors on re-ingestion | Use `uuid5(namespace, path + index)` |
| Embedding in API route | Blocks event loop; all requests stall | Always use background worker |
| Semantic-only search | Misses exact queries (names, dates, code) | Always use hybrid + RRF |
| Missing chunk metadata | Citations useless without source info | Required fields above are mandatory |
| Both models hot simultaneously | 16GB OOM on M1, swap degrades performance | Ollama handles context switching; don't force preload |
| `/api/embeddings` endpoint | 500 error on Ollama >= 0.1.44 | Use `/api/embed` with `"input"` key |
| Raw LLM output used directly | Hallucinations and format errors | Always validate with Pydantic schema |
| No FTS index on chunks table | FTS queries time out on large knowledge bases | `CREATE INDEX ... USING GIN(fts_vector)` |
| Context too large (> 3000 tokens) | LLM loses focus; accuracy drops | Trim to top-3 chunks for focused answers |

---

## Examples

### Example 1 — Good chunk with metadata
```python
{
    "id": "550e8400-e29b-41d4-a716-446655440000",  # uuid5 deterministic
    "source_path": "/notes/ai-engineering/transformers.md",
    "source_type": "markdown",
    "chunk_index": 3,
    "total_chunks": 12,
    "title": "Transformers — Architecture Overview",
    "content": "The attention mechanism computes a weighted sum of values...",
    "created_at": "2026-06-07T00:00:00Z",
}
```

### Example 2 — RRF in practice
```
Semantic results (rank): [doc_A, doc_C, doc_B, doc_D, doc_E, ...]
FTS results (rank):      [doc_B, doc_A, doc_F, doc_C, doc_G, ...]

RRF scores (k=60):
  doc_A: 1/61 + 1/62 = 0.0325 (rank 1 semantic + rank 2 FTS)
  doc_B: 1/63 + 1/61 = 0.0321 (rank 3 semantic + rank 1 FTS)
  doc_C: 1/62 + 1/64 = 0.0317 (rank 2 semantic + rank 4 FTS)

Final order: [doc_A, doc_B, doc_C, ...]
```

### Example 3 — System prompt with context (Akela format)
```
Sei Akela, l'assistente del secondo cervello personale.
REGOLE: Rispondi SOLO dal contesto. Se non trovi, di' "Non ho trovato informazioni su questo".
Usa la stessa lingua della domanda.

CONTESTO:
[1] Fonte: transformers.md
L'attention mechanism calcola una somma pesata dei valori...

[2] Fonte: llm-notes.md
I modelli transformer usano self-attention per catturare dipendenze...
```
