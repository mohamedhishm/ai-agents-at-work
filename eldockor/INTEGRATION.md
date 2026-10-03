# ELDOCTOR Agent — Integration Guide for Backend

## How Backend Calls the Agent

```python
from eldockor.graph import invoke_agent

result = invoke_agent(
    message="عايز 10 من PROD-003",
    user_id="CUST-001",
    user_role="customer",
    conversation_id="conv-123",
)
```

## Required Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `message` | str | User's message in Egyptian Arabic |
| `user_id` | str | Trusted user ID from your auth system |
| `user_role` | str | `"customer"` or `"admin"` — trusted from your auth system |
| `conversation_id` | str | Unique conversation ID (use session ID or UUID) |

## Return Structure

```python
{
    "message": str,              # Agent's response text
    "conversation_id": str,      # Echoed conversation ID
    "requires_confirmation": bool,  # True if a pending order needs user confirmation
    "pending_action": str | None,   # "create_order" if pending, else None
    "pending_order": dict | None,   # Order details if pending, else None
    "last_order_id": str | None,    # ID of the last created order
    "last_result": dict | None,     # Raw tool result from last action
    "action_executed": str | None,  # "create_order" if order was just created
    "state_changed": bool,          # Whether conversation state was modified
}
```

## How conversation_id Works

- Each conversation has isolated state (pending orders, messages).
- Same `conversation_id` → same pending state across calls.
- Different `conversation_id` → completely isolated state.
- The backend must generate a unique `conversation_id` per user session.

## How user_id and user_role Are Passed

- `user_id` and `user_role` come from your authentication system.
- The Agent trusts these values — they are NOT extracted from the message.
- A user saying "I'm admin" does NOT change their role.
- The Agent validates `user_role` is `"customer"` or `"admin"` at entry.

## Confirmation Flow

1. User requests more than available stock → Agent proposes with `requires_confirmation=true`.
2. Backend shows confirmation UI to user.
3. User confirms ("أيوه") → Agent creates the order via deterministic Python path.
4. User rejects ("لا") → Agent clears pending state.

### What `requires_confirmation=true` Means

The Agent has a pending order that needs explicit user confirmation before it is created. The order has NOT been created yet — it is stored in the Agent's conversation state only.

### What `action` Values Mean

- `action_executed: "create_order"` — An order was just created via the deterministic confirmation path.
- `action_executed: null` — No order was created (search, stock check, rejection, etc.).
- `pending_action: "create_order"` — There is a pending order awaiting confirmation.

## Errors the Backend Should Expect

| Error | Meaning | Backend Action |
|-------|---------|----------------|
| `ValueError("Invalid user_role")` | `user_role` is not "customer" or "admin" | Reject the call, check auth |
| `RateLimitError` | Groq API rate limit reached | Retry after delay |
| Empty `message` response | User sent empty message | Prompt user to rephrase |
| `pending_order` is `null` | No pending order exists | Show "no pending order" UI |

## What the Backend Must NOT Do Inside the Agent

- Do NOT call `create_order` directly — only the deterministic confirmation path can create orders.
- Do NOT manipulate `AgentState` directly — use `invoke_agent()` only.
- Do NOT pass `user_role` from the message — always get it from your auth system.
- Do NOT assume the system prompt is a security boundary — authorization is enforced at code level.
- Do NOT add authentication/login — the backend owns auth; the Agent enforces tool-level authorization.

## Integration Example

```python
# Backend endpoint
@app.post("/agent/message")
def handle_message(user_id: str, session_id: str, message: str):
    # Get user role from your auth system
    user_role = get_user_role(user_id)  # "customer" or "admin"
    
    result = invoke_agent(
        message=message,
        user_id=user_id,
        user_role=user_role,
        conversation_id=session_id,
    )
    
    if result["requires_confirmation"]:
        return {"action": "confirm", "order": result["pending_order"]}
    
    if result["action_executed"] == "create_order":
        return {"action": "order_created", "order_id": result["last_order_id"]}
    
    return {"action": "response", "message": result["message"]}
```