# ELDOCTOR AI Operations Agent

> **An AI-powered operations agent for Egyptian auto-parts SMEs**

Built by **The Shifters** for the **Agents at Work Hackathon**.

ELDOCTOR AI Operations Agent helps auto-parts businesses manage customer requests, inventory, and orders through a single intelligent interface instead of relying on manual searches across multiple sources.

---

## 💡 The Problem

Auto-parts businesses often manage daily operations across **WhatsApp, phone calls, Excel files, and paper records**.

This creates repetitive manual work when employees need to:

- Search for products and availability
- Check stock quantities
- Track customer orders
- Handle repetitive customer questions
- Reconcile information across different sources
- Prepare inventory and reorder information

As order volume grows, the business needs more manual effort to handle the same operational workflow.

---

## 🤖 Our Solution

**ELDOCTOR AI Operations Agent** acts as an intelligent bridge between users and the business data.

Customers can interact with the agent to:

- Search for auto parts
- Check product availability and quantity
- View product details
- Request specific quantities
- Create and track orders

Admins can use the agent to:

- Check inventory
- View low-stock products
- Review operational information
- Prepare reorder drafts
- Manage business operations through agent tools

The goal is not simply to answer questions, but to connect the user's request with the appropriate **data, tools, and business workflow**.

---

## 🏗️ Architecture

```text
┌───────────────┐
│   Frontend    │
│   Next.js     │
└───────┬───────┘
        │
        ▼
┌───────────────┐
│    Backend    │
│    FastAPI    │
└───────┬───────┘
        │
        ▼
┌───────────────┐
│  Agent Layer  │
│   LangGraph   │
└───────┬───────┘
        │
        ▼
┌───────────────┐
│     Tools     │
│ Customer/Admin│
└───────┬───────┘
        │
        ▼
┌───────────────┐
│   FileStore   │
│     JSON      │
└───────────────┘
```

### Project Structure

```text
ELDOCTOR/
├── eldockor/       # Agent, LangGraph graph, tools, FileStore
├── backend/        # FastAPI API, authentication, agent endpoint
└── frontend/       # Next.js web application
```

---

## ✨ Key Capabilities

### Customer Operations

- 🔎 Product search by name or category
- 📦 Real-time stock lookup from business data
- 📋 Product details
- 🛒 Quantity-aware order proposals
- 📌 Order confirmation workflow
- 📍 Order status lookup
- 🔐 Customer-specific conversation isolation

### Admin Operations

- 📊 Inventory summary
- ⚠️ Low-stock detection
- 🔄 Reorder draft generation
- 📦 Inventory lookup
- 🔐 Role-based access control

---

## 🔒 Transaction Safety

A key design principle is that the **LLM does not make the final decision to create an order**.

The order workflow is:

```text
User Request
     ↓
Agent understands the request
     ↓
Check product & available stock
     ↓
Generate Order Proposal
     ↓
User Confirmation
     ↓
Deterministic Order Creation
     ↓
Order ID Returned
```

For example:

```text
User: عايز 10 من PROD-003

Agent:
Available stock = 6
Order proposal = 6 units

User: أيوه

Agent:
Order created → ORD-XXX
```

If the user does not confirm, the order is not created.

### Safety Properties

- Explicit confirmation before order creation
- Deterministic order execution
- Duplicate confirmation protection
- Pending-state consumption
- Conversation isolation
- Customer/Admin role separation

---

## 🧠 Agent, Not Just a Chatbot

The agent follows a tool-based workflow instead of simply generating text.

```text
User Request
     ↓
Intent Understanding
     ↓
Select Required Tool
     ↓
Access Business Data
     ↓
Apply Business Rules
     ↓
Return Result / Execute Action
```

For example, when a customer asks for a product, the agent can search the inventory data and return the available quantity instead of guessing.

---

## 🛠️ Tech Stack

| Component | Technology |
|---|---|
| Frontend | Next.js |
| Backend | FastAPI |
| Agent Framework | LangGraph |
| Language Model | Groq / MockLLM fallback |
| Data Store | JSON FileStore |
| Authentication | JWT |
| Language | Python / TypeScript |

---

## 🚀 Setup

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt

cd ../frontend
npm install
```

### 2. Configure Environment Variables

Create the required `.env` files:

```bash
cp backend/.env.example backend/.env
cp eldockor/.env.example eldockor/.env
```

`GROQ_API_KEY` is optional for the demo because the project includes a deterministic **MockLLM fallback**.

### Environment Variables

| Variable | Location | Description |
|---|---|---|
| `GROQ_API_KEY` | `eldockor/.env` | Optional Groq API key |
| `NEXT_PUBLIC_API_URL` | `frontend/.env.local` | Backend URL |

Default backend URL:

```text
http://localhost:8000
```

---

## ▶️ Run the Application

### Backend

```bash
cd backend
PYTHONPATH=<project_root> python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### Frontend

In another terminal:

```bash
cd frontend
npm run dev
```

Then open the frontend in your browser.

---

## 🧪 Testing

The project includes automated tests covering the main agent and transaction-safety workflows.

```bash
cd eldockor
PYTHONPATH=<project_root> python test_phase1.py
```

Expected result:

```text
28/28 PASS
```

The test suite covers scenarios across the implemented agent phases, including order proposals, confirmation, duplicate prevention, authorization, and conversation isolation.

---

## 🎬 Demo Workflow

A simple customer flow:

### 1. Login

```text
Email: salma@eldoctor.com
Password: demo1234
```

### 2. Search for a product

```text
عايز فلتر زيت
```

### 3. Request a quantity

```text
عايز 10 من PROD-003
```

If the requested quantity is greater than available stock, the agent creates a proposal based on the available quantity.

### 4. Confirm

```text
أيوه
```

The order is created and an order ID is returned.

### 5. Test Duplicate Confirmation

```text
أيوه
```

The system prevents the same pending order from being created again.

---

## 📈 Business Impact

ELDOCTOR AI Operations Agent is designed to reduce repetitive operational work and help SMEs handle more requests without increasing the same amount of manual effort.

### Time Saved

Instead of manually searching across multiple sources for every request, employees can use the agent to retrieve operational information directly.

### Cost Saved

Reducing repetitive manual work can reduce the number of employee hours required for routine operational tasks.

### Revenue Opportunity

Faster responses to availability and pricing questions can reduce missed sales opportunities caused by slow manual verification.

### Accuracy

Centralizing the interaction with business data reduces unnecessary manual transfers between paper, Excel, WhatsApp, and employees.

---

## ⚠️ Current Limitations

This project is a **hackathon prototype**, not a production deployment.

Current limitations include:

- JSON-based FileStore instead of a production database
- MockLLM available as a deterministic fallback
- No RAG/vector database
- Browser testing of some frontend interactions is still limited
- Production deployment, monitoring, and scaling are outside the current scope

---

## 🔮 Future Improvements

Potential next steps include:

- Replace FileStore with PostgreSQL or another production database
- Add RAG for business documentation and product knowledge
- Integrate WhatsApp directly
- Add supplier and delivery workflows
- Add analytics and operational dashboards
- Add production-grade authentication and monitoring
- Support larger inventories and higher request volumes

---

## 👥 Team — The Shifters

- **Mohamed Hisham**
- **Salma Mohamed**
- **Nour Hussien**
- **Omar El Azab**
- **Kareem Wahba**

Built by **The Shifters** for the **Agents at Work Hackathon**.

Built for the **Agents at Work Hackathon**.

Our goal was to transform a real SME operational problem into an agentic workflow that reduces manual work, improves response time, and gives the business more operational capacity.

---

## 📌 Demo

The repository contains the complete implementation and test scenarios required to run and evaluate the agent locally.
