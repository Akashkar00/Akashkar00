<!-- Absolute raw URLs with a ?v= cache key, not relative paths. GitHub proxies
     README images through camo.githubusercontent.com and caches them hard: after
     regenerating a banner the OLD image keeps serving until the URL changes.
     BUMP ?v= EVERY TIME YOU REGENERATE THE SVGS or nobody will see the change. -->
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/Akashkar00/Akashkar00/main/assets/banner-dark.svg?v=2">
  <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/Akashkar00/Akashkar00/main/assets/banner-light.svg?v=2">
  <img alt="Akash Kar — GenAI, agentic systems, data science and analytics" src="https://raw.githubusercontent.com/Akashkar00/Akashkar00/main/assets/banner-light.svg?v=2" width="100%">
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

### Tech stack

<!-- Animated logo accent row, sourced from
     github.com/Anmol-Baranwal/Cool-GIFs-For-GitHub ("Moving Logos" section).
     Those GIFs are hosted on user-images.githubusercontent.com and hotlinked,
     same as the rest of that repo's own README does.

     Only Python is used here. That collection is a generic web-dev set (JS,
     Python, GitHub, VS Code, Vue, Node, React) with no LangChain/LangGraph/ML
     logos at all, so the rest of the stack below stays as static pills. Don't
     go looking for a LangChain GIF there; it isn't one of the ~20 in that
     section. -->

<p align="center">
  <img src="https://user-images.githubusercontent.com/74038190/212257472-08e52665-c503-4bd9-aa20-f5a4dae769b5.gif" width="52" alt="Python" />
</p>

<!-- "Tech Universe"-style pill grid (Akash supplied a reference image,
     icons.png, showing dark rounded badges in each tool's own brand colour).
     Reproduced with shields.io for-the-badge pills on this repo's 0A101F
     background, `logo=` set but logoColor DELIBERATELY OMITTED so each icon
     renders in its own brand colour instead of a forced accent -- that's what
     gives the multi-colour "universe" look instead of a flat monochrome row.
     GitHub wraps the images onto multiple lines by viewport width on its own,
     same as the reference grid.

     This list is Akash's actual stack per the project descriptions above --
     not the generic sample list in icons.png. Tools with a real simple-icons
     logo use one; RAG and LoRA/QLoRA are techniques, not branded tools, so
     they intentionally borrow the Python glyph (logo=python) rather than
     going logo-less. Groq, AWS, MATLAB, Tableau, and OpenAI have no working
     shields.io logo (confirmed via <image> element check, not just HTTP 200)
     and are left out entirely rather than shown broken.

     Re-verify a slug renders before adding one: an <img> with a missing logo
     silently falls back to a text-only pill (no error) -- check the response
     contains an <image> element, not just byte size. -->

<p align="center">
  <img src="https://img.shields.io/badge/Python-0A101F?style=for-the-badge&logo=python" alt="Python" />
  <img src="https://img.shields.io/badge/React-0A101F?style=for-the-badge&logo=react" alt="React" />
  <img src="https://img.shields.io/badge/Electron-0A101F?style=for-the-badge&logo=electron" alt="Electron" />
  <img src="https://img.shields.io/badge/LangChain-0A101F?style=for-the-badge&logo=langchain" alt="LangChain" />
  <img src="https://img.shields.io/badge/LangGraph-0A101F?style=for-the-badge&logo=langgraph" alt="LangGraph" />
  <img src="https://img.shields.io/badge/RAG-0A101F?style=for-the-badge&logo=python" alt="RAG" />
  <img src="https://img.shields.io/badge/LoRA%2FQLoRA-0A101F?style=for-the-badge&logo=python" alt="LoRA/QLoRA" />
  <img src="https://img.shields.io/badge/Pydantic-0A101F?style=for-the-badge&logo=pydantic" alt="Pydantic" />
  <img src="https://img.shields.io/badge/FastAPI-0A101F?style=for-the-badge&logo=fastapi" alt="FastAPI" />
  <img src="https://img.shields.io/badge/Streamlit-0A101F?style=for-the-badge&logo=streamlit" alt="Streamlit" />
  <img src="https://img.shields.io/badge/spaCy-0A101F?style=for-the-badge&logo=spacy" alt="spaCy" />
  <img src="https://img.shields.io/badge/NumPy-0A101F?style=for-the-badge&logo=numpy" alt="NumPy" />
  <img src="https://img.shields.io/badge/Pandas-0A101F?style=for-the-badge&logo=pandas" alt="Pandas" />
  <img src="https://img.shields.io/badge/scikit--learn-0A101F?style=for-the-badge&logo=scikitlearn" alt="scikit-learn" />
  <img src="https://img.shields.io/badge/TensorFlow-0A101F?style=for-the-badge&logo=tensorflow" alt="TensorFlow" />
  <img src="https://img.shields.io/badge/Keras-0A101F?style=for-the-badge&logo=keras" alt="Keras" />
  <img src="https://img.shields.io/badge/Jupyter-0A101F?style=for-the-badge&logo=jupyter" alt="Jupyter" />
  <img src="https://img.shields.io/badge/PostgreSQL-0A101F?style=for-the-badge&logo=postgresql" alt="PostgreSQL" />
  <img src="https://img.shields.io/badge/MySQL-0A101F?style=for-the-badge&logo=mysql" alt="MySQL" />
  <img src="https://img.shields.io/badge/Redis-0A101F?style=for-the-badge&logo=redis" alt="Redis" />
  <img src="https://img.shields.io/badge/Qdrant-0A101F?style=for-the-badge&logo=qdrant" alt="Qdrant" />
  <img src="https://img.shields.io/badge/Docker-0A101F?style=for-the-badge&logo=docker" alt="Docker" />
  <img src="https://img.shields.io/badge/Terraform-0A101F?style=for-the-badge&logo=terraform" alt="Terraform" />
  <img src="https://img.shields.io/badge/Google_Cloud-0A101F?style=for-the-badge&logo=googlecloud" alt="Google Cloud" />
  <img src="https://img.shields.io/badge/Git-0A101F?style=for-the-badge&logo=git" alt="Git" />
  <img src="https://img.shields.io/badge/GitHub-0A101F?style=for-the-badge&logo=github" alt="GitHub" />
  <img src="https://img.shields.io/badge/GitHub_Actions-0A101F?style=for-the-badge&logo=githubactions" alt="GitHub Actions" />
</p>

---

### Contribution graph

<picture>
  <source media="(prefers-color-scheme: dark)"
          srcset="https://raw.githubusercontent.com/Akashkar00/Akashkar00/output/snake-dark.svg">
  <source media="(prefers-color-scheme: light)"
          srcset="https://raw.githubusercontent.com/Akashkar00/Akashkar00/output/snake-light.svg">
  <img alt="Contribution snake"
       src="https://raw.githubusercontent.com/Akashkar00/Akashkar00/output/snake-dark.svg" width="100%">
</picture>

<!-- These resolve only after the "Generate Snake" workflow has run green once:
     the `output` branch does not exist until then. -->

### Find me

<!--
  ============================================================================
  SOCIAL BADGES — READ BEFORE EDITING
  ============================================================================

  Palette: bg 0A101F  |  cyan 22D3EE  |  emerald 10B981  |  violet A78BFA
  All badges use style=for-the-badge and background 0A101F.
  Separator between badges is &nbsp;&nbsp; (do not use plain spaces —
  GitHub collapses them and the badges end up touching).

  ---------------------------------------------------------------------------
  THE LINKEDIN QUIRK — DO NOT "SIMPLIFY" THE LINKEDIN BADGE
  ---------------------------------------------------------------------------
  shields.io's built-in `logo=linkedin` only renders its glyph when the badge
  background is LinkedIn brand blue (0A66C2). On ANY custom background colour
  the glyph is silently dropped — no error, no warning, HTTP 200 — and you get
  a text-only badge that looks "fine" until you notice the icon is missing.

  Measured (2026-07-27):
    https://img.shields.io/badge/LinkedIn-0A101F?style=for-the-badge
      -> 200, 445 bytes                         (text-only baseline)
    https://img.shields.io/badge/LinkedIn-0A101F?style=for-the-badge&logo=linkedin
      -> 200, 445 bytes, no <image> element     (BUG: byte-identical to
                                                 text-only, glyph vanished)
    the data-URI version used below
      -> 200, 1312 bytes, contains <image ... data:image/svg+xml;base64,...>
                                                (glyph actually present)

  THE FIX (already applied below): the LinkedIn glyph is embedded directly in
  the `logo=` query parameter as a URL-encoded base64 SVG data-URI. The SVG
  path comes from simple-icons and is hard-filled #FFFFFF so it reads against
  the dark 0A101F badge. Because the fill is baked into the data-URI,
  `logoColor=` has NO effect on this badge — to recolour the glyph you must
  rebuild the data-URI, not add a query param.

  TO REGENERATE (e.g. if simple-icons updates the mark):
    1. curl -sL https://cdn.jsdelivr.net/npm/simple-icons@latest/icons/linkedin.svg
       (note: the raw.githubusercontent.com/simple-icons/.../icons/linkedin.svg
        path now 404s — the icons moved. jsdelivr works; unpkg 404s too.)
    2. Extract the <path d="..."> and wrap it:
       <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="#FFFFFF"><path d="..."/></svg>
    3. base64 it -> prefix with `data:image/svg+xml;base64,`
       -> URL-encode the WHOLE string -> use as the `logo=` value.
    4. VERIFY, don't assume:
       curl -s -o /tmp/lnkchk.svg -w "%{http_code}" "<full badge url>"
       Require HTTP 200 AND the response to be materially larger than the
       445-byte text-only baseline AND to contain `<image` / `base64`.

  Gmail and Instagram are unaffected — their built-in shields.io logos
  recolour fine on a custom background, so they use `logo=gmail` /
  `logo=instagram` with `logoColor=22D3EE` normally.

  NO GITHUB BADGE HERE — DELIBERATE. This fragment renders on Akash's own
  GitHub profile README, so a "follow me on GitHub" badge would just link the
  reader back to the page they are already looking at. Please don't add one.
  ============================================================================
-->

[![LinkedIn](https://img.shields.io/badge/LinkedIn-0A101F?style=for-the-badge&logo=data%3Aimage%2Fsvg%2Bxml%3Bbase64%2CPHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0iI0ZGRkZGRiI%2BPHBhdGggZD0iTTIwLjQ0NyAyMC40NTJoLTMuNTU0di01LjU2OWMwLTEuMzI4LS4wMjctMy4wMzctMS44NTItMy4wMzctMS44NTMgMC0yLjEzNiAxLjQ0NS0yLjEzNiAyLjkzOXY1LjY2N0g5LjM1MVY5aDMuNDE0djEuNTYxaC4wNDZjLjQ3Ny0uOSAxLjYzNy0xLjg1IDMuMzctMS44NSAzLjYwMSAwIDQuMjY3IDIuMzcgNC4yNjcgNS40NTV2Ni4yODZ6TTUuMzM3IDcuNDMzYy0xLjE0NCAwLTIuMDYzLS45MjYtMi4wNjMtMi4wNjUgMC0xLjEzOC45Mi0yLjA2MyAyLjA2My0yLjA2MyAxLjE0IDAgMi4wNjQuOTI1IDIuMDY0IDIuMDYzIDAgMS4xMzktLjkyNSAyLjA2NS0yLjA2NCAyLjA2NXptMS43ODIgMTMuMDE5SDMuNTU1VjloMy41NjR2MTEuNDUyek0yMi4yMjUgMEgxLjc3MUMuNzkyIDAgMCAuNzc0IDAgMS43Mjl2MjAuNTQyQzAgMjMuMjI3Ljc5MiAyNCAxLjc3MSAyNGgyMC40NTFDMjMuMiAyNCAyNCAyMy4yMjcgMjQgMjIuMjcxVjEuNzI5QzI0IC43NzQgMjMuMiAwIDIyLjIyMiAwaC4wMDN6Ii8%2BPC9zdmc%2B)](https://www.linkedin.com/in/akash-kar-0a7a7826a/)
&nbsp;&nbsp;
[![Gmail](https://img.shields.io/badge/Gmail-0A101F?style=for-the-badge&logo=gmail&logoColor=22D3EE)](mailto:karakash828@gmail.com)
&nbsp;&nbsp;
[![Instagram](https://img.shields.io/badge/Instagram-0A101F?style=for-the-badge&logo=instagram&logoColor=22D3EE)](https://instagram.com/akashkar00)
