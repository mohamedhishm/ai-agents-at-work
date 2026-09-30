# AI Operations Agent — Project Status & Architecture

## 1. Project Overview

This project is an AI-powered operations agent for **ELDOCTOR Auto Parts & Services (شركة الدكتور لتجارة قطع غيار السيارات)**.

The main business problem is that operations currently depend on a mixture of:

- Paper records
- Excel spreadsheets
- Phone orders
- WhatsApp orders
- Manual stock checking
- Manual reconciliation between received products, current stock, and shipped orders

As the number of orders increases, the amount of manual work also increases.

The goal of this project is to build an **AI Agent**, not just a chatbot, that can understand customer/admin requests and interact with the company's transactional data through controlled tools.

---

# 2. Current Project Goal

The agent should eventually support two main roles:

### Customer

The customer should be able to:

- Search for products
- Check product availability
- Check product details
- Request an order
- Handle insufficient-stock situations
- Confirm an order
- Reject an order
- Modify a pending quantity
- Check order status
- View previous orders

### Admin

The admin should eventually be able to:

- View inventory
- Check low-stock products
- Check out-of-stock products
- Prepare reorder drafts
- View existing reorder drafts

The system is designed so that the **LLM handles understanding and reasoning**, while the **Store remains the source of truth for transactional data**.

---

# 3. Important Architecture Principle

The most important design decision in this project is:

> The LLM should NOT be the source of truth for products, stock, prices, or orders.

The system is divided into different responsibilities.

```text
User
  ↓
Backend / API
  ↓
invoke_agent()
  ↓
LangGraph
  ↓
LLM
  ↓
Tools
  ↓
Store
  ↓
JSON Data
```

The LLM understands the user's request and decides which tool is useful.

The Store performs the actual data operations.

For example:

```text
User:
"عايز بطارية PROD-003"

        ↓

LLM understands:
User wants a product/order

        ↓

search_products()

        ↓

Store

        ↓

products.json

        ↓

Tool result

        ↓

LLM

        ↓

Response to user
```

The LLM does not invent stock information.

---

# 4. Technology Stack

Current main technologies:

- Python
- LangChain
- LangGraph
- Groq
- `langchain_groq`
- JSON files as the current database/store
- python-dotenv

Current LLM configuration:

```python
ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0,
    api_key=api_key,
)
```

The API key is loaded from:

```text
.env
```

using:

```python
load_dotenv()
```

---

# 5. Current Repository Structure

The important structure is approximately:

```text
project/
│
├── agent/
│   │
│   ├── graph.py
│   ├── llm.py
│   ├── prompts.py
│   │
│   ├── tools_customer.py
│   ├── tools_admin.py
│   │
│   ├── test_phase1.py
│   │
│   └── store/
│       ├── base.py
│       └── file_store.py
│
├── data/
│   ├── products.json
│   └── orders.json
│
├── .env
│
└── other project files
```

The exact repository may contain additional files, but the files above are the main agent components.

---

# 6. `agent/llm.py`

## Responsibility

This file is responsible for creating and configuring the LLM.

Current implementation uses Groq through LangChain.

Conceptually:

```text
Environment
   ↓
GROQ_API_KEY
   ↓
ChatGroq
   ↓
LLM
```

The important function is:

```python
get_llm()
```

It:

1. Loads the API key
2. Verifies that `GROQ_API_KEY` exists
3. Creates the `ChatGroq` instance
4. Returns the LLM

Current model:

```text
openai/gpt-oss-120b
```

Temperature is:

```text
0
```

This is intentional because the agent should behave consistently for operational tasks.

---

# 7. `agent/prompts.py`

## Responsibility

This file contains the system instructions given to the LLM.

The prompt explains:

- What the agent is
- What it can do
- How it should use tools
- How it should handle products
- How it should handle stock
- How it should handle orders
- How it should behave in Arabic/English
- That it should not invent transactional information

One important rule is:

```text
Do not create an order before confirmation.
```

However, an important discovery was made during the audit:

The system prompt is only an instruction to the LLM.

It is NOT a complete architectural safety mechanism.

This led to the current Phase 1 safety fix described later.

---

# 8. `agent/store/base.py`

## Responsibility

This file defines the Store interface/contract.

The Store is the abstraction between the agent and the actual data source.

For example:

```python
class Store(Protocol):
    def search_products(...):
        ...

    def check_stock(...):
        ...
```

The purpose is to prevent the agent/tools from being tightly coupled to JSON files.

Currently the actual implementation is a file-based store, but later the same interface could be connected to:

- PostgreSQL
- MySQL
- MongoDB
- An actual ERP
- An API

without redesigning the entire agent.

---

# 9. `agent/store/file_store.py`

## Responsibility

This is the current real Store implementation.

It reads/writes the JSON data under:

```text
data/
```

The Store is responsible for transactional data operations such as:

- Searching products
- Getting a product
- Checking stock
- Creating orders
- Getting order status
- Getting customer orders
- Inventory operations
- Reorder operations

The exact methods depend on the current implementation.

The important architectural rule is:

> Tools talk to the Store, not directly to `products.json` or `orders.json`.

---

# 10. `data/products.json`

This is currently the product/inventory data source.

There are currently 10 products.

Current stock values:

```text
PROD-001 → 0
PROD-002 → 3
PROD-003 → 8
PROD-004 → 0
PROD-005 → 2
PROD-006 → 15
PROD-007 → 20
PROD-008 → 4
PROD-009 → 1
PROD-010 → 7
```

This file is currently acting as the inventory source of truth.

---

# 11. `data/orders.json`

This contains the current orders.

The original dataset contained:

```text
ORD-001
ORD-002
ORD-003
ORD-004
ORD-005
ORD-006
```

During testing, temporary orders can be created.

The Phase 1 test suite contains cleanup logic to restore the original data after testing.

The repository should always be checked after tests to make sure no test artifacts remain in the real data.

---

# 12. `agent/tools_customer.py`

## Responsibility

This file contains tools available to customer users.

Important customer tools include:

### `search_products`

Searches for products using the Store.

Flow:

```text
User
 ↓
LLM
 ↓
search_products
 ↓
Store
 ↓
products.json
```

This is currently **not an embedding/vector search**.

It is Store/file-based search.

---

### `check_stock`

Checks actual inventory through the Store.

The LLM should use this instead of guessing stock.

---

### `get_product_details`

Gets detailed information about a specific product.

---

### `create_order`

Creates a real order through:

```text
Store → create_order()
```

This is a **transactional tool**.

Because it changes real data, it is the most sensitive tool in the system.

---

### `get_order_status`

Checks the status of an order.

---

### `get_customer_orders`

Returns the customer's previous orders.

---

### `propose_order`

This was added specifically to make the insufficient-stock workflow safe.

It is different from `create_order`.

`propose_order`:

- Does NOT create an order
- Does NOT modify transactional data
- Checks the available quantity
- Returns a structured proposal

Example:

```json
{
  "status": "proposed",
  "product_id": "PROD-003",
  "quantity": 8,
  "product_name": "...",
  "original_requested": 10,
  "message": "..."
}
```

This allows the graph to create a pending action.

---

# 13. `agent/tools_admin.py`

## Responsibility

Contains tools for admin operations.

Current intended/admin capabilities include:

### Inventory summary

Get overall inventory information.

### Low stock

Find products with low inventory.

### Reorder

Prepare a reorder draft.

### List reorder drafts

View previously prepared reorder drafts.

These tools use the same Store layer.

They are intended to be available only to admins once authorization is properly implemented.

---

# 14. `agent/graph.py`

## Most Important File

This is currently the main brain/orchestration layer of the agent.

It contains the LangGraph workflow.

The graph is responsible for:

- Building the LLM
- Binding tools
- Managing agent state
- Handling pending orders
- Detecting confirmations
- Detecting rejection
- Detecting quantity modifications
- Executing confirmed orders
- Routing between LLM and tools
- Maintaining conversation state

---

# 15. Basic LangGraph Flow

The basic flow is:

```text
START
  ↓
agent
  ↓
LLM
  ↓
Does the LLM request a tool?
  ↓
YES
  ↓
tools
  ↓
agent
  ↓
final response
```

Conceptually:

```text
              ┌──────────────┐
              │     User     │
              └──────┬───────┘
                     ↓
              ┌──────────────┐
              │   agent_node │
              └──────┬───────┘
                     ↓
                   LLM
                     ↓
              ┌──────┴───────┐
              │              │
          normal reply    tool call
                             ↓
                         ToolNode
                             ↓
                           Store
                             ↓
                         agent_node
```

---

# 16. Agent State

The graph keeps important state such as:

```text
pending_action
pending_order
user_role
user_id
conversation_id
last_order_id
last_result
messages
```

The most important state for the order workflow is:

```text
pending_action
pending_order
```

---

# 17. `pending_action`

This tells the system what action is waiting for user confirmation.

Example:

```text
pending_action = "create_order"
```

This means:

> There is a proposed order waiting for user confirmation.

---

# 18. `pending_order`

This stores the exact order proposal.

For example:

```json
{
  "product_id": "PROD-003",
  "quantity": 8,
  "product_name": "...",
  "original_requested": 10
}
```

This is important because when the user confirms, the system should use this stored data instead of asking the LLM to reconstruct the order.

---

# 19. Why Pending State Exists

Suppose:

```text
User:
عايز 10 من PROD-003
```

But stock is:

```text
8
```

The agent should NOT create an order for 8 automatically.

Instead:

```text
Requested: 10
Available: 8
```

The agent proposes:

```text
I can prepare 8 instead. Do you want to confirm?
```

Then:

```text
pending_action = create_order

pending_order = {
    product_id: PROD-003,
    quantity: 8
}
```

No real order has been created yet.

---

# 20. Confirmation Flow

User:

```text
أيوه
```

The graph detects that there is:

```text
pending_action = create_order
```

and that the message is an explicit confirmation.

Then Python itself executes:

```text
_create_order(...)
```

using:

```text
pending_order
```

The LLM does not reconstruct the order.

This is important for transaction safety.

---

# 21. Rejection Flow

Example:

```text
Agent:
المتاح 3. هل تريد تأكيد الطلب؟

User:
لا
```

The graph clears:

```text
pending_action
pending_order
```

No order is created.

---

# 22. Quantity Modification Flow

Example:

```text
Agent:
المتاح 4. هل تريد تأكيد 4؟

User:
لا خد 3
```

The graph must understand that this is not a rejection of the whole process.

Instead:

```text
old quantity = 4
new quantity = 3
```

Then it updates:

```text
pending_order.quantity = 3
```

and asks for confirmation again.

No order is created until the user confirms.

The ordering of detection was intentionally fixed so that:

```text
"لا خد 3"
```

is detected as a modification before being treated as a rejection.

---

# 23. Confirmation Without Pending Order

Example:

```text
User:
أيوه
```

but there is no pending order.

The system must NOT create anything.

The graph has an early deterministic path for this.

This prevents a random confirmation from triggering a transaction.

---

# 24. Repeated Confirmation

Example:

```text
User:
عايز 10 من PROD-009

Agent:
المتاح 1، هل تريد تأكيد 1؟

User:
أيوه

→ ORD-008 created
```

If the user then says:

```text
أيوه
```

again:

```text
NO second order
```

The pending state has already been cleared.

This prevents duplicate order creation.

---

# 25. Conversation IDs

The system uses:

```text
conversation_id
```

to isolate conversations.

The current service stores conversation state in an in-memory structure:

```text
_conversation_store
```

Conceptually:

```text
conversation-A
    ↓
its own state

conversation-B
    ↓
different state
```

The same conversation ID should preserve pending state across multiple `invoke_agent()` calls.

Different conversation IDs must not share pending orders.

This was implemented but still needs final execution verification.

---

# 26. `invoke_agent()`

This is the main public interface for calling the agent.

Expected input:

```python
invoke_agent(
    message,
    user_id,
    user_role,
    conversation_id
)
```

Conceptually:

```text
API
 ↓
invoke_agent()
 ↓
load conversation state
 ↓
LangGraph
 ↓
save conversation state
 ↓
return response
```

The expected response contains information similar to:

```json
{
  "message": "...",
  "conversation_id": "...",
  "action": "...",
  "requires_confirmation": false,
  "data": {}
}
```

The exact contract should always be checked against the current implementation rather than assumed.

---

# 27. Transactional vs Non-Transactional Tools

This distinction is very important.

## Read-only tools

Examples:

```text
search_products
check_stock
get_product_details
get_order_status
get_customer_orders
propose_order
```

These should not create a real order.

## Transactional tools

Example:

```text
create_order
```

This changes the database/store.

Therefore it requires stronger protection.

---

# 28. Important Safety Issue Found

During the Phase 1 audit, an architectural problem was discovered.

Currently:

```text
create_order
```

is included in the tools bound to the LLM.

That means technically the LLM could call:

```text
create_order(...)
```

directly.

The system prompt tells the LLM:

```text
Don't create an order without confirmation.
```

But this is only an LLM instruction.

It is not a code-level guarantee.

The unsafe theoretical path is:

```text
User:
عايز 3 من PROD-003

        ↓

LLM

        ↓

create_order()

        ↓

REAL ORDER
```

without a pending confirmation.

---

# 29. Why This Is a Phase 1 Blocker

The intended requirement is:

> No real order may be created unless the user explicitly confirms a pending order.

The current code does not guarantee this architecturally because:

- `create_order` is available to the LLM
- There is no strict tool-level authorization guard
- The system prompt alone cannot guarantee behavior
- The LLM could theoretically call `create_order` directly

Therefore the current status is:

```text
PHASE 1 NOT COMPLETE YET
```

This is the main issue to fix before declaring Phase 1 finished.

---

# 30. Planned Safety Fix

The current agreed direction is:

### Primary protection

Do not expose:

```text
create_order
```

to the LLM during the normal non-confirmation flow.

The deterministic Python confirmation path should be responsible for real order creation.

### Additional protection

Add a code-level guard so that even if an unexpected `create_order` call is produced, it cannot execute without valid pending state.

The guard should verify more than just:

```text
pending_action exists
```

It should conceptually require:

```text
valid pending_action
+
valid pending_order
+
explicit user confirmation
+
order data comes from pending_order
```

Do NOT create an order and then attempt to roll it back.

---

# 31. Phase 1 Testing

The main test file is:

```text
agent/test_phase1.py
```

The tests use the real:

```text
invoke_agent()
```

and real Store/data.

The tests should NOT manually manipulate AgentState.

---

# 32. Phase 1 Scenarios

The original Phase 1 test suite contains 8 scenarios.

## S1 — Insufficient Stock

Example:

```text
PROD-003
requested = 10
stock = 8
```

Expected:

```text
pending_action = create_order
pending_order.quantity = 8
```

No real order yet.

---

## S2 — Confirmation

Continue S1 with:

```text
أيوه
```

Expected:

```text
real order created
```

with:

```text
quantity = 8
```

---

## S3 — Rejection

Example:

```text
PROD-002
requested = 10
stock = 3
```

Agent proposes 3.

User:

```text
لا
```

Expected:

```text
pending state cleared
no order created
```

---

## S4 — Quantity Modification

Example:

```text
PROD-008
stock = 4
requested = 10
```

Agent proposes 4.

User:

```text
لا خد 3
```

Expected:

```text
pending quantity:
4 → 3
```

No order yet.

---

## S5 — Confirmation Without Pending

Example:

```text
أيوه
```

with no pending order.

Expected:

```text
no order
no transaction
```

---

## S6 — Repeated Confirmation

Create an order once.

Then send:

```text
أيوه
```

again.

Expected:

```text
no duplicate order
```

---

## S7 — Conversation Isolation

Conversation A creates a pending order.

Conversation B sends confirmation.

Expected:

```text
B cannot confirm A's pending order.
```

---

## S8 — State Persistence

Use the same:

```text
conversation_id
```

across separate `invoke_agent()` calls.

Expected:

```text
pending state survives between calls
```

until confirmation/rejection.

---

# 33. Latest Phase 1 Test Status

The first complete run previously showed:

```text
S1 PASS
S2 PASS
S3 PASS
S4 PASS
S5 PASS
S6 PASS
S7 PASS
S8 PASS
```

However, during the latest clean verification run, Groq rate limiting stopped execution around Scenario 7.

Therefore the latest audit did NOT consider Phase 1 fully verified.

The latest verified status was:

```text
S1 → PASS
S2 → PASS
S3 → PASS
S4 → PASS
S5 → PASS
S6 → PASS
S7 → NOT VERIFIED
S8 → NOT VERIFIED
```

So the correct project status is:

```text
Phase 1 functionality: mostly implemented
Phase 1 verification: incomplete
Phase 1 safety: one blocker identified
```

Do not claim Phase 1 is fully complete until the safety fix and full test run are completed.

---

# 34. Data Cleanup

Testing can modify:

```text
products.json
orders.json
```

The test suite contains cleanup logic that attempts to restore the original data.

The original order data should return to:

```text
ORD-001 → ORD-006
```

and the original product inventory should be restored.

Important:

After interrupted tests, always check:

```text
git status
git diff
```

and inspect:

```text
data/products.json
data/orders.json
```

to make sure test artifacts did not remain.

---

# 35. Current Data Integrity Status

The data was manually restored after the latest interrupted/rate-limited run.

The known original product data is currently:

```text
PROD-001 → 0
PROD-002 → 3
PROD-003 → 8
PROD-004 → 0
PROD-005 → 2
PROD-006 → 15
PROD-007 → 20
PROD-008 → 4
PROD-009 → 1
PROD-010 → 7
```

But automated cleanup after an unexpected interruption has not been fully verified.

---

# 36. Current Capabilities

At the point of this documentation, the agent can:

- Search products
- Check stock
- Get product details
- Detect insufficient stock
- Propose a smaller quantity
- Store pending order state
- Ask for confirmation
- Create an order after confirmation
- Reject an order proposal
- Modify pending quantity
- Prevent confirmation without pending
- Prevent repeated confirmation from creating another order
- Maintain conversation state
- Isolate conversations
- Check order status
- Get customer order history
- Perform admin inventory operations
- Prepare reorder drafts
- Work with Arabic and English requests
- Use real Store data

---

# 37. Current Limitations

The following are not fully completed/verified yet.

## Authorization

User roles exist in state:

```text
user_role
```

but complete runtime authorization is not yet implemented.

The system still needs stronger enforcement for:

```text
customer
admin
```

so a customer cannot invoke admin operations.

---

## Authentication

Authentication is not currently implemented inside the agent layer.

The future backend should authenticate users and pass trusted:

```text
user_id
user_role
```

to:

```text
invoke_agent()
```

The agent should not blindly trust user-provided role information.

---

## Persistent State

Current conversation state is stored in memory:

```text
_conversation_store
```

This means state is lost if the Python process restarts.

For production, it should eventually be moved to something persistent such as:

```text
Redis
PostgreSQL
database-backed checkpointing
```

---

## Concurrency

The current in-memory conversation store is not yet designed as a production-grade concurrent persistence layer.

Concurrency/thread-safety still needs testing.

---

# 38. Product Search and Embeddings

An important architectural clarification:

The current product search does NOT use embeddings.

The current flow is:

```text
User
 ↓
LLM understands query
 ↓
search_products(query)
 ↓
FileStore
 ↓
products.json
```

Embeddings/RAG are not necessary for basic transactional operations.

---

# 39. Future RAG Layer

RAG is intended for static company knowledge such as:

- Warranty policy
- Return policy
- Working hours
- Company information
- Delivery policy
- General FAQs

Example:

```text
User:
"هل المنتج عليه ضمان؟"

        ↓

RAG

        ↓

Company knowledge

        ↓

Answer
```

Transactional information such as:

```text
current stock
order status
customer orders
```

should continue to come from the Store.

---

# 40. Product Typos / Semantic Search

A future issue to handle is Arabic spelling variation.

Example:

User:

```text
بطريه
```

Database:

```text
بطارية
```

Simple keyword matching may fail.

Possible future solution:

```text
User query
   ↓
LLM normalization
   ↓
exact/keyword search
   ↓
fuzzy matching
   ↓
semantic search if needed
   ↓
candidate products
   ↓
exact product verification
   ↓
stock check
   ↓
confirmation
```

Important:

A fuzzy or semantic match should NEVER directly trigger an order.

The exact product ID must be verified before any transaction.

---

# 41. Important Safety Principle

The agent follows this general rule:

```text
Flexible understanding
        +
Deterministic transactional execution
```

The LLM is useful for:

- Understanding natural language
- Choosing tools
- Extracting intent
- Handling Arabic/English conversation

Python/Store should control:

- Actual stock
- Actual orders
- Transaction execution
- Pending state
- Confirmation
- Authorization
- Idempotency

This separation is one of the most important architectural principles in the project.

---

# 42. Current Phase 1 Audit

The latest audit concluded:

### Implemented

```text
LLM integration                    ✅
LangGraph                          ✅
Store layer                        ✅
Product search                     ✅
Stock checking                     ✅
Product details                    ✅
Insufficient stock proposal        ✅
Pending order state                ✅
Confirmation                       ✅
Rejection                          ✅
Quantity modification              ✅
No-pending confirmation handling  ✅
Duplicate prevention               ✅
Order creation                     ✅
Admin tools                        ✅
Conversation state architecture    ✅
```

### Implemented but needs final verification

```text
Conversation isolation              ⚠️
State persistence                   ⚠️
Order status                        ⚠️
Customer order history              ⚠️
Admin E2E workflows                 ⚠️
Store failure handling              ⚠️
Full Phase 1 test suite             ⚠️
Cleanup after interruption          ⚠️
```

### Needs fixing

```text
Direct LLM access to create_order   ❌
Runtime authorization               ❌
Authentication                      ❌
Production persistent state         ❌
```

---

# 43. Exact Point Where Development Stopped

The current development session stopped at the discovery of the following issue:

```text
create_order is still exposed as an LLM tool.
```

The audit concluded:

```text
MUST FIX BEFORE PHASE 1
```

No code modification for this specific fix should be assumed yet.

The next development task is:

```text
1. Fix create_order architectural safety
2. Test direct LLM create_order cannot execute
3. Run original 8 Phase 1 scenarios again
4. Verify S7 and S8
5. Verify data cleanup
6. Inspect git diff
7. Only then declare Phase 1 complete
```

---

# 44. Recommended Next Test Set

After the safety fix, run at least:

```text
S1 → insufficient stock
S2 → confirmation
S3 → rejection
S4 → quantity modification
S5 → confirmation without pending
S6 → repeated confirmation
S7 → conversation isolation
S8 → state persistence
```

Then add safety-specific tests:

```text
S9  → sufficient-stock request must NOT directly create
S10 → malicious/unexpected direct create_order tool call must be blocked
S11 → valid confirmation creates exactly one order
S12 → confirmation with no pending creates nothing
```

All tests should use:

```text
invoke_agent()
```

and the real Store.

Do not manually manipulate AgentState inside tests.

---

# 45. Phase 2 Plan

After Phase 1 is stable, Phase 2 should expand testing and production readiness.

The planned comprehensive test set includes:

1. Arabic search
2. English search
3. Product ID search
4. Nonexistent product
5. Stock lookup
6. Zero stock
7. Low stock
8. Normal stock
9. Valid order within stock
10. Insufficient stock proposal
11. Confirmation creates order
12. "اه"
13. "تمام"
14. "لا"
15. "مش عايز"
16. "لا خد 2/3"
17. Confirmation without pending
18. Order status
19. Customer order history
20. Admin inventory
21. Admin low stock
22. Admin out-of-stock
23. Customer attempts admin tool
24. Missing product
25. Invalid quantity
26. Store failure
27. LLM failure
28. Malformed Store response
29. Multiple turns in same conversation
30. Different conversation IDs
31. Repeated confirmation
32. Full customer E2E
33. Full admin E2E

---

# 46. Future Production Architecture

The long-term architecture should look like:

```text
                  ┌─────────────────────┐
                  │ Customer/Admin UI   │
                  └──────────┬──────────┘
                             ↓
                  ┌─────────────────────┐
                  │ Backend / API       │
                  │ Authentication      │
                  └──────────┬──────────┘
                             ↓
                  ┌─────────────────────┐
                  │ invoke_agent()     │
                  └──────────┬──────────┘
                             ↓
                  ┌─────────────────────┐
                  │ LangGraph Agent     │
                  │                     │
                  │ State + Rules       │
                  └──────┬───────┬──────┘
                         ↓       ↓
                      LLM      Tools
                         │       │
                         │       ↓
                         │    Store
                         │       │
                         │       ↓
                         │   Database
                         │
                         ↓
                       RAG
                         │
                         ↓
                Static Company Knowledge
```

The important separation is:

```text
LLM
↓
understanding/reasoning

Tools + Store
↓
real business operations

RAG
↓
static knowledge

Backend/Auth
↓
identity and permissions

LangGraph
↓
workflow/state/control
```

---

# 47. How a New Developer Should Continue

If someone joins this project tomorrow, they should follow this order:

### Step 1

Read:

```text
agent/graph.py
```

Understand:

- `invoke_agent`
- `agent_node`
- state
- pending order
- confirmation flow
- tool routing

### Step 2

Read:

```text
agent/tools_customer.py
agent/tools_admin.py
```

Understand every tool and whether it is read-only or transactional.

### Step 3

Read:

```text
agent/store/base.py
agent/store/file_store.py
```

Understand how tools access the data.

### Step 4

Inspect:

```text
data/products.json
data/orders.json
```

Understand the current test data.

### Step 5

Read:

```text
agent/prompts.py
```

Understand the LLM instructions.

### Step 6

Run:

```text
agent/test_phase1.py
```

after ensuring the Groq API is available and test cleanup is safe.

### Step 7

Fix the `create_order` safety issue before adding new functionality.

### Step 8

Verify all 8 Phase 1 scenarios.

### Step 9

Run the additional safety tests.

### Step 10

Only then move to Phase 2.

---

# 48. Final Project Status

Current status:

```text
Project foundation                 ✅
LLM integration                    ✅
LangGraph workflow                 ✅
Store architecture                 ✅
Customer tools                     ✅
Admin tools                        ✅
Pending-order workflow             ✅
Confirmation workflow              ✅
Rejection workflow                 ✅
Quantity modification              ✅
Duplicate prevention               ✅
Conversation state                 ✅
Phase 1 tests                      ⚠️ Partial verification
Authorization                      ❌
Authentication                     ❌
Persistent production state        ❌
Direct create_order safety         ❌ MUST FIX
```

Therefore:

> **The project is not starting from zero. The core agent workflow is already implemented. The immediate next task is a focused transaction-safety fix, followed by a clean full Phase 1 verification.**

Do not rewrite the architecture.

Do not replace LangGraph.

Do not replace the Store.

Do not add unnecessary RAG/embeddings before the transactional workflow is stable.

The next milestone is simply:

```text
Secure create_order
        ↓
Pass all Phase 1 tests
        ↓
Verify data integrity
        ↓
Declare Phase 1 complete
        ↓
Move to authorization + production hardening + Phase 2
```