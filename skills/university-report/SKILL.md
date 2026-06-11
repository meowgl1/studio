---
name: university-report
description: Generate a university-level technical report about the current project. Reads project context, changelogs, research docs, and gotchas to produce a structured academic article with abstract, data tables, algorithm analysis, design decisions, and a priority matrix. Activate on: "voglio un report universitario", "technical article", "scrivi un articolo tecnico", "report accademico", or similar.
---

# Skill — University Report

Generate a structured technical report, written at university level, grounded in the actual project. No generic filler — every claim traces to a file, a decision, or a measurement.

---

## Before writing: load project intelligence

Read the following in order. Stop if a file is missing — do not fabricate content.

1. `.studio/context.md` — identity, stack decisions, current status table
2. `.studio/tasks.md` — what is done, what is in progress, what is blocked
3. `.studio/gotchas.md` — known failure modes and constraints
4. `.studio/research/` — any research documents present (read all)
5. `.studio/changelog/` — the 3 most recent entries (for "what was built")
6. Source code (selective) — read only files relevant to the section being written

Do not load `memory/`, `agents/`, or `output-styles/` unless the user asks.

---

## Report structure

Use this structure exactly. Mark each section with its heading level. Never skip a section — if data for it is genuinely unavailable, write one sentence noting the gap instead.

```
## Abstract
## 1. Introduction
## 2. System Architecture
## 3. [Core Technical Topic 1]   ← varies per project
## 4. [Core Technical Topic 2]   ← varies per project
## 5. Design Decisions
## 6. Experimental Results / Performance
## 7. Feature Roadmap
## Conclusion
```

The two "Core Technical Topic" sections are the heart of the report. Identify them from the project's main engineering challenges — not from generic categories. Examples from Akela: "3. Hybrid Search and Retrieval" and "4. Vector Store Abstraction".

---

## Section-by-section rules

### Abstract

3–5 sentences. Must answer: What is the system? What problem does it solve? What is the main architectural contribution of this report? No citations, no code, no tables.

### 1. Introduction

- Problem statement: what gap does the project fill?
- Motivation: why now, why local/self-hosted, why this stack?
- Scope: what is in scope vs out of scope?
- Report structure: one sentence per section, what the reader will find there.

### 2. System Architecture

Include an ASCII diagram or Mermaid block showing the main components and their connections. Read the existing architecture diagram from README or context.md if present — adapt, do not recreate from scratch.

Describe each component in one paragraph: what it does, why it was chosen, what it connects to.

End with a **component table**:

| Component | Technology | Role | Interface |
|-----------|-----------|------|-----------|
| Backend | FastAPI | ... | REST |
| ... | ... | ... | ... |

### Core Technical Topic sections

Each section must contain:

1. **Problem statement** — what challenge this component solves (1 paragraph)
2. **Design** — how it works, with a code snippet if it clarifies the mechanism
3. **Data table** — measurements, comparisons, or complexity analysis. If no data is available from source files or research docs, note it explicitly: *"Benchmark data not yet collected — planned for vX.Y"*
4. **Tradeoffs** — what was NOT chosen and why (1 short paragraph or table)

For algorithm-heavy sections, include:
- Input/output specification
- Step-by-step process (numbered list)
- Time/space complexity where knowable

### 5. Design Decisions

A table of every non-trivial architectural decision made in the project. Source from `context.md` stack decisions and `gotchas.md`.

| Decision | Option chosen | Alternative considered | Reason |
|----------|--------------|----------------------|--------|
| Vector DB | Qdrant | Pinecone, pgvector | ... |
| ... | ... | ... | ... |

### 6. Experimental Results / Performance

Pull from: changelogs (measured latency, throughput), research docs (benchmark numbers), gotchas (failure modes with observed effects). If nothing is measured yet, say so and list what should be measured.

Include a **legend** for any notation used in tables:
> **Legend:** tok/s = tokens per second; ms = milliseconds; dim = vector dimensions; Q4 = 4-bit quantization; RRF = Reciprocal Rank Fusion

### 7. Feature Roadmap

A prioritized table sourced from `tasks.md` Next items and any roadmap in research docs.

| Feature | Description | Complexity | Value | Status |
|---------|-------------|-----------|-------|--------|
| ... | ... | Low/Med/High | Low/Med/High | Planned/Next/Doing |

Add a brief paragraph explaining the priority order rationale.

### Conclusion

3–5 sentences. What was built, what was the key architectural insight, what is the next milestone.

---

## Style rules

- **University register** — precise terminology, no colloquialisms, no marketing language
- **First person avoided in abstract and conclusion** — use "the system", "this work", "the implementation"
- **Technical terms defined on first use** — write term, then parenthetical definition: *"Reciprocal Rank Fusion (RRF) — a rank aggregation method that combines multiple ranked lists without requiring score normalization"*
- **Every quantitative claim needs a source** — cite the file or doc it comes from: *(source: .studio/research/airllm-hermes-agent.md)*
- **No fabricated benchmarks** — if a measurement doesn't exist in the project files, say so
- **Tables preferred over prose for comparisons** — four or more items in a comparison → always a table
- **Code blocks** — use language tags (```python, ```sql, ```bash) always
- **Consistent heading hierarchy** — never skip levels

---

## Output format

Return the report as a Markdown document. Do not wrap in a code block — deliver raw Markdown. The user will paste it into their own document.

Length: typically 800–2000 words of prose, plus tables and code blocks. Quality over length — if the project is small, 800 words is correct; do not pad.

---

## Trigger examples

- "Scrivi un report universitario su questa sessione"
- "Voglio un articolo tecnico da consegnare all'università"
- "Technical write-up of what we built today"
- "University-level explanation of the VectorStore abstraction"
- "Dammi il report accademico del progetto"
