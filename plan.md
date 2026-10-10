# Project: Natural Language-to-Code Compiler (NL2Code)

## Role
You are a senior full-stack engineer and compiler-design expert. Build the full project below end to end. Work in phases, run and verify each phase before moving on, and keep the structure modular and production-grade.

## Goal
A web app that **compiles plain-English descriptions into verified, runnable code**. It is not a one-shot LLM wrapper. It runs a real compiler-style pipeline with an intermediate representation, validation, sandboxed execution, and an automatic repair loop.

## Pipeline (Compiler Stages)

```
NL Input -> [1] Intent Parser -> [2] Spec / IR Builder -> [3] Code Generator
         -> [4] Static Validator -> [5] Sandbox Executor -> [6] Repair Loop -> Output
```

1. **Intent Parser**: extracts task, inputs, outputs, constraints, edge cases, target language.
2. **Spec / IR Builder**: produces a strict JSON IR (validated with Pydantic):
   - `function_name`, `signature`, `inputs[]`, `outputs`, `constraints[]`, `edge_cases[]`, `complexity_target`, `test_cases[]`
3. **Code Generator**: IR to code via a pluggable LLM provider. Language-specific prompt templates.
4. **Static Validator**: syntax check and lint per language.
   - Python: `ast.parse`, `ruff`
   - C++: `g++ -fsyntax-only -Wall -Wextra`
   - Java: `javac`
   - JavaScript: `node --check`
5. **Sandbox Executor**: runs generated code against IR `test_cases` inside an isolated Docker container (no network, CPU/memory/time limits, read-only FS, non-root user).
6. **Repair Loop**: on compile or test failure, feed errors plus failing cases back to the LLM. Max 3 iterations. Return the full attempt history.

## Features
- Target languages: **Python, C++, Java, JavaScript** (extensible via a `LanguageAdapter` interface)
- Auto-generated unit tests from the IR
- Complexity explanation (time and space) for generated code
- Streaming pipeline progress to the UI (SSE or WebSocket) with per-stage status
- Side-by-side view: English input, IR (JSON), generated code, test results
- Compile history (SQLite), with re-run and export
- Download as a file or copy to clipboard
- Provider abstraction: Gemini, Anthropic, OpenAI (selected via env var)
- Rate limiting, request validation, structured logging

## Tech Stack
- **Backend**: Python 3.11+, FastAPI, Pydantic v2, SQLAlchemy + SQLite, Docker SDK for Python
- **Frontend**: React + Vite + TypeScript, Tailwind CSS, Monaco Editor
- **Infra**: Docker, docker-compose, GitHub Actions (lint + tests)
- **Testing**: pytest (backend), Vitest (frontend)

## Folder Structure

```
nl2code/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── api/
│   │   │   ├── routes_compile.py
│   │   │   ├── routes_history.py
│   │   │   └── schemas.py
│   │   ├── core/
│   │   │   ├── pipeline.py
│   │   │   ├── intent_parser.py
│   │   │   ├── ir_builder.py
│   │   │   ├── code_generator.py
│   │   │   ├── validator.py
│   │   │   ├── sandbox.py
│   │   │   └── repair_loop.py
│   │   ├── languages/
│   │   │   ├── base.py
│   │   │   ├── python_adapter.py
│   │   │   ├── cpp_adapter.py
│   │   │   ├── java_adapter.py
│   │   │   └── js_adapter.py
│   │   ├── llm/
│   │   │   ├── base.py
│   │   │   ├── gemini.py
│   │   │   ├── anthropic_client.py
│   │   │   └── openai_client.py
│   │   ├── models/
│   │   │   ├── ir.py
│   │   │   └── db.py
│   │   └── prompts/
│   │       ├── intent.md
│   │       ├── ir.md
│   │       ├── codegen_python.md
│   │       ├── codegen_cpp.md
│   │       ├── codegen_java.md
│   │       ├── codegen_js.md
│   │       └── repair.md
│   ├── sandbox_images/
│   │   ├── Dockerfile.python
│   │   ├── Dockerfile.cpp
│   │   ├── Dockerfile.java
│   │   └── Dockerfile.node
│   ├── tests/
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── PromptPanel.tsx
│   │   │   ├── PipelineTimeline.tsx
│   │   │   ├── IRViewer.tsx
│   │   │   ├── CodeEditor.tsx
│   │   │   ├── TestResults.tsx
│   │   │   └── HistorySidebar.tsx
│   │   ├── hooks/useCompileStream.ts
│   │   ├── lib/api.ts
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   └── vite.config.ts
├── docker-compose.yml
├── .env.example
├── .github/workflows/ci.yml
└── README.md
```

## API Contract

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/compile` | Start compile, returns `job_id` |
| GET | `/api/compile/{job_id}/stream` | SSE stream of stage events |
| GET | `/api/history` | List past compilations |
| GET | `/api/history/{id}` | Full record (IR, code, tests, attempts) |
| GET | `/api/health` | Health check |

**POST `/api/compile` body**
```json
{ "prompt": "string", "language": "python|cpp|java|javascript", "max_repairs": 3 }
```

**SSE event shape**
```json
{ "stage": "intent|ir|codegen|validate|sandbox|repair|done|error", "status": "running|ok|failed", "payload": {} }
```

## Security Requirements
- Never execute generated code on the host. Docker sandbox only.
- Sandbox: `--network none`, memory cap (256 MB), CPU cap, 5 s timeout, read-only root FS, non-root user, PID limit.
- Treat user prompts and LLM output as untrusted. Validate all inputs with Pydantic.
- API keys only via env vars. Never log them.
- Per-IP rate limiting on `/api/compile`.

## UI / UX Requirements
- Modern, clean, responsive layout (mobile to desktop), dark and light themes
- Three-pane layout: Prompt | IR + Pipeline timeline | Code + Test results
- Animated pipeline timeline showing the live stage status
- Monaco editor with syntax highlighting per language
- Clear error states, loading skeletons, keyboard shortcut (Ctrl+Enter to compile)
- Accessible (ARIA labels, focus states, contrast)

## Quality Bar
- Clean, modular code. No dead code, minimal comments.
- Type hints everywhere (Python) and strict TypeScript.
- Each pipeline stage independently unit-tested, with the LLM mocked.
- Edge cases handled: empty input, ambiguous prompts (return clarifying questions), unsupported language, sandbox timeout, malformed IR, LLM failure or retry with backoff.
- Target: end-to-end compile under ~15 s for simple tasks.

## Phased Execution (verify each before continuing)
1. **Scaffold**: repo, config, docker-compose, health endpoint, CI
2. **Core models**: IR schema, language adapters, LLM provider abstraction
3. **Pipeline**: intent, IR, codegen, with mocked-LLM tests
4. **Validation + Sandbox**: Docker images, resource limits, test runner
5. **Repair loop**: error feedback, attempt history
6. **Streaming API + history persistence**
7. **Frontend**: UI, SSE hook, Monaco, history sidebar
8. **Polish**: error handling, rate limiting, README, demo prompts

## Deliverables
- Full working code for every file in the structure above
- `.env.example` with all required variables
- `README.md` containing:
  - Architecture diagram (Mermaid)
  - Setup instructions (local and Docker)
  - Run, test, and lint commands
  - Example prompts and expected output
  - Complexity and scalability notes

## Demo Prompts to Verify
1. "Write a function that returns the k most frequent elements in an array" (Python)
2. "Check if a string is a valid palindrome ignoring punctuation and case" (C++)
3. "Merge overlapping intervals" (Java)
4. "Debounce a function by N milliseconds" (JavaScript)

## Acceptance Criteria
- All 4 demo prompts compile, pass generated tests, and display in the UI
- A deliberately broken generation triggers the repair loop and recovers within 3 attempts
- The sandbox blocks network access and enforces timeouts
- `docker-compose up` starts the full stack with one command
- CI passes (lint + tests)

Start with Phase 1. After each phase, summarize what was built, show the verification result, and proceed.