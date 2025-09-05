### Initial Research: StudyRAG

1. Research summary

1.1 Project concept

Research date: 2025-09-04
Project idea: Student learning SaaS: upload course documents → RAG chat with citations → generate quizzes → practice personalized and gamified.

1.2 Key findings

- The AI-in-education market is expanding rapidly (2025 est. $7–8.3B; 31–43% CAGR to 2030–2034), driven by demand for personalization and cloud-native tools. Students already rely on AI-enhanced platforms (e.g., Quizlet) for daily study, validating strong B2C demand.
- Differentiation should focus on trustworthy, cited answers and quiz items grounded in user documents, EU-only data handling, and fast ingestion-to-practice flow (≤2–3 minutes to first quiz; P95 chat latency ≤2.5s). Use pgvector HNSW for low-latency retrieval and MarkItDown/Unstructured for robust multi-format parsing.

### 2. Market opportunity

2.1 Current landscape

- Market state: 2025 est. $7.05–$8.30B, with projections to $32–$112B by 2030–2034 (CAGR ~31–43%). Sources vary but agree on strong growth, North America lead, APAC fastest growth.
- Key trends: (1) Personalized learning and AI tutors; (2) Cloud-native adoption in education; (3) Multimodal and document-grounded AI (Q&A on docs); (4) EU AI Act compliance pressure; (5) Micro-credentialing and continuous assessment.
- User demand: Quizlet reports 60M+ monthly users and high engagement with AI features; Notion’s Q&A shows strong usage for “ask your docs.”

  2.2 Target users

- Primary audience: University students (18–30), PDF/slide-heavy programs (business, CS, law, medicine), EU-first privacy expectations.
- Core pain points: Long, dense PDFs; difficulty verifying correctness; time to convert notes into practice; low motivation and fragmentation across tools.
- Current solutions: Quizlet (sets + AI features), generic chatbots without citations, Notion Q&A for knowledge base search (not study-specific), manual flashcards.

### 3. Competitive landscape

3.1 Main competitors

- Quizlet: Large content library and AI study tools (Learn, Magic Notes; prior Q-Chat tutor now discontinued as of Jun 2025). Strengths: scale, habit, mobile; Risks: less document-grounded, mixed source citation.
- Notion AI Q&A: Instant answers across workspace docs; strong connectors and enterprise positioning. Strengths: search across tools, speed; Weaknesses for our niche: not study-specific, limited quiz generation and pedagogy.
- (Adjacent) LMS add-ons and note apps with AI (general-purpose, not focused on citations + quizzes from user PDFs).

  3.2 Market gaps

- Unmet needs: Fast, reliable ingestion from PDFs/DOCX/Slides with structure-aware chunking; verifiable citations in every answer and question; EU-only data; seamless “upload → chat/quiz” in minutes.
- Differentiation opportunities: “No source, no claim” policy; quiz questions with source_ref per item; EU data residency by default; performance guarantees (P95 chat ≤2.5s), and frictionless multi-format upload.

### 4. Technical recommendations

4.1 Recommended tech stack

- Frontend: React + Vite + TypeScript + Tailwind + shadcn (already in place) for fast, responsive UI and mobile-first design.
- Backend: FastAPI (Python 3.11/3.12) with async I/O; Celery/RQ for ingestion queue; OpenTelemetry for traces.
- Database: Postgres 16 + pgvector with HNSW indexes for approximate nearest neighbor; BM25 hybrid via tsvector; partitioning as data scales.
- Deployment: EU-only hosting (e.g., Supabase Postgres EU region; FastAPI on Fly.io/OVH/Hetzner EU); CDN for assets; feature flags.
- Additional tools: MarkItDown or Unstructured for parsing; SSE/Fetch Streams for chat; structured logging and trace IDs; model observability on citation coverage.

  4.2 Technical considerations

- Performance expectations: P95 chat latency ≤2.5s after warm-up; ingestion-to-ready in <2–5 min for typical 30–80 page PDFs; streaming answers; hybrid search (vector + BM25) with re-ranking optional v1.
- Scalability: Background ingestion, chunk/batch writes; HNSW tuning (ef_search, m); sharding or Citus only when necessary; materialized views for recent items.
- Security: EU AI Act awareness (education AI can be high-risk when used for admissions/assessment decisions; our use is learner support). Maintain transparency, human oversight, audit logs, no PII in logs, GDPR compliance; signed URLs for storage.

### 5. User experience insights

5.1 Design expectations

- UI patterns: Document library with statuses; chat with inline citations and snippet previews; quiz review with explanations and sources; progress and streaks.
- User flow: Upload → ingestion status → select doc → chat with citations → generate quiz → attempt → review → practice weak areas.
- Device usage: Optimize for mobile portrait (reading, quizzes), ensure responsive chat; keyboard shortcuts for desktop power users.

  5.2 Feature priorities

- Must-have features: Multi-format upload; ingestion with structure-aware chunking; hybrid retrieval; chat with mandatory citations; quiz generation with per-question source_ref; attempts + score + explanations; progress basics.
- Nice-to-have features: Re-ranking; spaced repetition; tag-based study plans; study groups/sharing; teacher mode (later).

### 6. Key opportunities and risks

6.1 Opportunities

- Market timing: Rapid AI adoption in study workflows; students actively seek AI help and accept personalized tools.
- Growth potential: Expand from personal study to course packs and small-group sharing; later teacher dashboards.
- Competitive advantage: Verifiable citations, EU-first privacy, and fastest path from document to quiz.

  6.2 Risks to consider

- Technical challenges: Parsing failures, hallucinations if retrieval weak, slow ingestion on large PDFs, cost of embeddings.
- Market risks: Incumbent network effects (Quizlet); AI feature parity pressure.
- User adoption: Trust in citations must be earned; onboarding friction if ingestion slow or error-prone.

### 7. Recommendations for PRD

7.1 Focus areas

- Primary value proposition: Turn course PDFs into trustworthy answers and source-backed quizzes in minutes.
- Target user segment: University students in PDF-heavy courses (EU-first), starting with B2C.
- Core features: Upload/ingestion (PDF/DOCX/MD/TXT), chat with citations, quiz generation with source_ref, attempts + explanations, progress basics, EU data residency.

  7.2 Success metrics to track

- User metrics: D7 retention; weekly active study minutes; % sessions with a completed quiz; “helpful” rating on answers (target ≥80% positive); upload→first-quiz conversion rate.
- Business metrics: Free→paid conversion; paid retention; CAC/LTV (later).
- Technical metrics: P95 chat latency ≤2.5s; ≥95% answers with ≥1 citation; ingestion success rate; average ingestion time; retrieval recall@k on eval set.

### 8. Sources

- AI in Education market sizes and growth:
  - Precedence Research (updated Jul 2025): $7.05B (2025) to $112.3B (2034), 36% CAGR. [Link](https://www.precedenceresearch.com/ai-in-education-market)
  - Grand View Research (2025): $5.88B (2024) → $32.27B (2030), 31.2% CAGR. [Link](https://www.grandviewresearch.com/industry-analysis/artificial-intelligence-ai-education-market-report)
  - Mordor Intelligence (2025): $6.90B (2025) → $41.01B (2030), 42.83% CAGR. [Link](https://www.mordorintelligence.com/industry-reports/ai-in-education-market)
  - IMARC (2025): $4.8B (2024) → $75.1B (2033), 34% CAGR. [Link](https://www.imarcgroup.com/ai-in-education-market)
- Competitor signals (Quizlet, Notion):
  - Quizlet back-to-school AI features (Aug 2025). [Link](https://www.prnewswire.com/news-releases/quizlet-launches-new-ai-powered-experience-for-back-to-school-302521126.html)
  - Quizlet Q-Chat announcement (note: no longer available as of Jun 2025). [Link](https://quizlet.com/blog/meet-q-chat)
  - Fortune overview of Quizlet AI tools (Oct 2023). [Link](https://fortune.com/education/articles/quizlet-ai-powered-tools-q-chat-magic-notes-quick-summary-gpt/)
  - Notion AI Q&A (Nov 2023) and connectors (2024). [Link](https://www.notion.com/blog/introducing-q-and-a) • [Link](https://www.notion.com/releases/2024-09-25)
- Tech stack validation:
  - pgvector (HNSW/IVFFlat, latest features). [Link](https://github.com/pgvector/pgvector)
  - pgvector 0.6.0 release (perf/memory/WAL improvements). [Link](https://www.postgresql.org/about/news/pgvector-060-released-2799/)
  - Microsoft MarkItDown (multi-format to Markdown). [Link](https://github.com/microsoft/markitdown)
- Regulation (EU focus):
  - EU AI Act official page and risk approach/timeline (2024–2026+). [Link](https://digital-strategy.ec.europa.eu/en/policies/regulatory-framework-ai)
  - European Parliament overview & compliance timeline (updated Feb 2025). [Link](https://www.europarl.europa.eu/topics/en/article/20230601STO93804/eu-ai-act-first-regulation-on-artificial-intelligence)
