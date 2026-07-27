<picture>
  <source media="(prefers-color-scheme: dark)" srcset="./assets/banner-dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="./assets/banner-light.svg">
  <img alt="Akash Kar — GenAI, agentic systems, data science and analytics" src="./assets/banner-light.svg" width="100%">
</picture>

---

### What I'm building

I build **agentic AI systems that survive contact with production** — graph-orchestrated
LLM pipelines with guardrails, gateways, evals and tracing, not notebook demos. Most of my
work lands somewhere in **healthcare AI**: clinical trials, consultation notes, prescriptions.

**Enterprise Agentic RAG** — four Cloud Run microservices (api, ui, evals, ingestion).
A LangGraph state machine routes *Planner → Retriever → Grade Docs → Rewriter / Web Search →
Context Guard → Responder → Output Guard*, fronted by NeMo Guardrails and a Portkey gateway
with Llama 3.3 70B → 3.1 8B fallback. Qdrant + FlashRank reranking, Redis semantic cache,
RAGAS evals, Postgres-backed LangGraph checkpointing, Eventarc-triggered ingestion,
Logfire + LangSmith traces.

**Clinical Trial Matcher** — matches patients to ClinicalTrials.gov studies through LLM
clinical reasoning. Five-node LangGraph pipeline, PubMedBERT embeddings, Qdrant, and a real
eval suite with ground truth and synthetic patients rather than vibes.

**AI Clinical Scribe** — consultation audio → structured clinical documentation. Whisper STT,
spaCy entity extraction, FastAPI backend, React + TypeScript front end.

**MedGuide AI** — handwritten prescription analysis via Grok-4 vision, with a real
handwritten-prescription dataset and an evals folder.

### How I work

- **Evals before claims.** If I say a system works, there's a scored suite behind it. One of
  my own project reviews notes a classifier's 99% accuracy is mostly one feature doing the
  work — I'd rather write that down than quietly ship the number.
- **Guardrails by default.** Prompt-injection defense, output sanitisation and PII redaction
  show up in my projects even when nobody asked for them.
- **Infra is part of the model.** Docker, Terraform, Cloud Run, CI, and tracing are how a
  pipeline becomes a system.

### Currently

Deepening **multi-agent orchestration** and **MCP**, and pushing the Enterprise RAG stack from
a monolith into properly separated services. Open to collaborating on **agentic AI** and
**clinical/health-tech ML**.

---
