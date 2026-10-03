# ELDOCTOR AI Agent — Auto Parts & Services

AI agent for Egyptian SME auto-parts business (ELDOCTOR). Built for the **Agents at Work** hackathon.

## Purpose

ELDOCTOR helps Egyptian auto-parts shops automate:
- Product search & inventory lookup
- Order proposals with stock-aware quantity capping
- Deterministic order confirmation (no LLM-dependent financial decisions)
- Admin inventory & reorder management

## Architecture

```
Frontend (Next.js) → Backend (FastAPI) → Agent (LangGraph) → Tools → FileStore (JSON)
```

- **eldockor/** — Agent package (MockLLM, LangGraph graph, customer + admin tools, FileStore)
- **backend/** — FastAPI server (auth JWT, /agents/message endpoint)
- **frontend/** — Next.js chat UI

## Implemented Capabilities

✅ Product search (by name/category)
✅ Stock check with quantity
✅ Product details
✅ Order proposal via `propose_order` tool (when requested qty > available)
✅ Deterministic confirmation ("أيوه" → create order, "لا" → cancel)
✅ Duplicate confirmation blocked (idempotency key + pending state consumption)
✅ Conversation isolation (separate conversations per user)
✅ Admin tools: inventory summary, low-stock items, reorder drafts
✅ Role-based authorization (customer ≠ admin)
✅ MockLLM (deterministic fallback, no GROQ_API_KEY needed)

## Setup

```bash
# 1. Install dependencies
cd backend && pip install -r requirements.txt
cd frontend && npm install

# 2. Create .env files
cp backend/.env.example backend/.env
cp eldockor/.env.example eldockor/.env
# Add GROQ_API_KEY=your_key in eldockor/.env (or leave empty for MockLLM)

# 3. Seed data is already present in JSON files (no seed script needed)
```

## Environment Variables

| Variable | Location | Purpose |
|----------|----------|---------|
| `GROQ_API_KEY` | `eldockor/.env` | Groq API key (optional — MockLLM used if absent) |
| `NEXT_PUBLIC_API_URL` | `frontend/.env.local` | Backend URL (default: `http://localhost:8000`) |

## Startup

```bash
# Terminal 1 — Backend
cd backend
PYTHONPATH=<project_root> python -m uvicorn app.main:app --host 127.0.0.1 --port 8000

# Terminal 2 — Frontend
cd frontend
npm run dev
```

## Test Instructions

```bash
cd eldockor
PYTHONPATH=<project_root> python test_phase1.py
```

All 28 scenarios should pass (Phase 1–7).

## Demo Workflow

1. Login: `salma@eldoctor.com` / `demo1234`
2. Send: `عايز فلتر زيت` → see search results
3. Send: `عايز 10 من PROD-003` → pending order proposed (capped to available stock)
4. Send: `أيوه` → order created (ORD-XXX)
5. Send: `أيوه` again → duplicate blocked (same order_id)

## Security / Transaction Safety

### `create_order` Tool Exposure

The `create_order` tool IS exposed to the LLM in both `tools_customer.py` and `tools_admin.py`. The LLM CAN call it directly.

### How the Confirmation Flow Works

1. User requests an order → LLM calls `propose_order` (not `create_order`)
2. Graph detects `propose_order` ToolMessage → creates pending state
3. User confirms with "أيوه" → Graph intercepts and calls `FileStore.create_order()` deterministically
4. User says "لا" → Graph clears pending state

### Security Properties

- **Confirmation required**: User must explicitly confirm with "أيوه" before order is created
- **Deterministic execution**: Order creation happens in Python code, not via LLM tool call
- **Duplicate prevention**: Idempotency key + pending state consumption
- **Conversation isolation**: Different conversations don't share pending state
- **Role-based authorization**: Customer cannot access admin tools (enforced at backend)

## Known Limitations / Future Work

- MockLLM is rule-based (not intelligent) — replace with real LLM when GROQ_API_KEY is set
- FileStore is JSON-based (not a database) — suitable for demo, not production scale
- No RAG / vector DB (out of scope for hackathon)
- Frontend confirmation bar works but needs real-browser testing
- GROQ_API_KEY placeholder in repo — replace before production
