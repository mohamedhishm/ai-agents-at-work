"""
LangGraph-based AI Agent for ELDOCTOR Auto Parts.

This module implements the core agent loop using LangGraph with multi-turn state
for order confirmation flows.

Architecture:
    User → service.py → graph.py (LangGraph with State)
         → LLM → Tools → Store → Real Data → Response

State tracking:
- messages: conversation history
- pending_action: current pending action (e.g., "create_order")
- pending_order: details of the pending order
- user_role: user's role (customer/admin)
- user_id: user identifier
- conversation_id: unique identifier for the conversation

Confirmation flow:
1. User requests quantity > available
2. Agent checks stock, proposes available quantity
3. Agent sets pending_action = "create_order" and stores pending_order
4. User confirms ("أيوه", "تمام", etc.) → execute create_order
5. User rejects ("لا", "مش عايز") → cancel pending
6. User modifies ("لا خد 2") → update pending and re-validate
"""

import json
import uuid
from typing import TypedDict, Annotated, Literal

from langgraph.graph import MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from agent.llm import get_llm
from agent.store.file_store import FileStore
from agent.tools_customer import create_customer_tools
from agent.tools_admin import create_admin_tools
from agent.prompts import SYSTEM_PROMPT

# ---------------------------------------------------------------------------
# Multi-turn conversation state storage (in-memory for hackathon)
# ---------------------------------------------------------------------------

# Store conversation states by conversation_id
# Format: { conversation_id: { messages, pending_action, pending_order, ... } }
_conversation_store: dict[str, dict] = {}

# ---------------------------------------------------------------------------
# Helper to get conversation state (used by invoke_agent and agent_node)
# ---------------------------------------------------------------------------

def _get_conv_state(conversation_id: str) -> dict:
    """Get or create conversation state from the store."""
    if conversation_id not in _conversation_store:
        _conversation_store[conversation_id] = {
            "messages": [],
            "pending_action": None,
            "pending_order": None,
            "user_role": "customer",
            "user_id": "unknown",
            "last_order_id": None,
            "last_result": None,
        }
    return _conversation_store[conversation_id]


def get_conversation_state(conversation_id: str) -> dict:
    """Get or create conversation state."""
    if conversation_id not in _conversation_store:
        _conversation_store[conversation_id] = {
            "messages": [],
            "pending_action": None,
            "pending_order": None,
            "user_role": "customer",
            "user_id": "unknown",
            "last_order_id": None,
            "last_result": None,
        }
    return _conversation_store[conversation_id]


def clear_conversation_state(conversation_id: str) -> None:
    """Clear conversation state (for testing/cleanup)."""
    if conversation_id in _conversation_store:
        del _conversation_store[conversation_id]


# ---------------------------------------------------------------------------
# Custom State for multi-turn workflows
# ---------------------------------------------------------------------------

class AgentState(MessagesState):
    """Extended state for multi-turn agent workflows."""
    pending_action: str | None = None
    pending_order: dict | None = None
    user_role: str = "customer"
    user_id: str = "unknown"
    conversation_id: str = "default"
    last_order_id: str | None = None
    last_result: dict | None = None


# ---------------------------------------------------------------------------
# Confirmation detection (deterministic)
# ---------------------------------------------------------------------------

CONFIRMATION_WORDS = {
    "أيوه", "اه", "آه", "تمام", "ماشي", "موافق",
    "نفذ", "اعمل الطلب", "يعني لا", "لاوقت", "يلا",
    "yes", "yep", "yup", "yeah", "ok", "okay", "sure",
    "go ahead", "go for it", "confirmed", "done",
}

REJECTION_WORDS = {
    "لا", "لأ", "مش عايز", "خلاص", "الغيه", "إلغاء",
    "لا عايز", "مش quantizer", "cancel", "no", "nope",
    "not now", "later", "لا지금은",
}

MODIFICATION_WORDS = {
    "خد", "خذ", "غير", "غير الكمية", "عدل", "عدلي",
    "change", "modify", "update", "different",
}


def is_confirmation_word(message: str) -> bool:
    """
    Check if a message is a pure confirmation word (regardless of pending state).
    Used to detect confirmation attempts when no pending order exists.
    """
    msg_lower = message.lower().strip()

    # Exact match for simple confirmation words
    simple_confirmations = {
        "أيوه", "اه", "آه", "تمام", "موافق", "ايوه", "aha", "aywa",
        "yes", "ok", "okay", "yeah", "yep", "sure", "done", "تفضل",
    }
    if msg_lower in simple_confirmations:
        return True

    # Check if message contains ONLY confirmation words (no other content)
    words = set(msg_lower.split())
    if words and words.issubset({w.lower() for w in simple_confirmations}):
        return True

    return False


def is_confirmation(message: str, pending_action: str | None) -> bool:
    """
    Check if a message is a confirmation.

    Confirmation only counts if there's a valid pending action.
    """
    if not pending_action:
        return False

    msg_lower = message.lower().strip()

    # Check for confirmation words
    for word in CONFIRMATION_WORDS:
        if word.lower() in msg_lower:
            return True

    # Check for "نعم" / "yes" variants
    if msg_lower in ("نعم", "نعم", "aye", "aha", "correct"):
        return True

    # Check if message is just a simple affirmative
    simple_affirmatives = {"نعم", "أيو", "أه", "آه", "يلا", "OK", "ok"}
    if msg_lower.strip() in simple_affirmatives:
        return True

    return False


def is_rejection(message: str) -> bool:
    """Check if a message is a rejection."""
    msg_lower = message.lower().strip()

    for word in REJECTION_WORDS:
        if word.lower() in msg_lower:
            return True

    # Check for common rejection patterns
    rejection_patterns = [
        "مش عايز", "مش ال", "ما necesito", "I don't",
        "لا أريد", "لا لا", "no thanks", "not interested",
    ]
    for pattern in rejection_patterns:
        if pattern.lower() in msg_lower:
            return True

    return False


def extract_quantity_from_message(message: str) -> int | None:
    """
    Try to extract a quantity number from a message.

    Examples:
        "لا خد 2" → 2
        "أخذ 5" → 5
        "عايز 10" → 10
    """
    import re

    # Look for Arabic/English number patterns
    # Matches: "خد 2", "خذ 5", "عايز 10", "خد ٢"
    patterns = [
        r'(?:خد|خذ|عايز|عيّش|عامل|ساوِر|حضي|تسلم|جيب)\s*[٠-٩0-9]+\s*([٠-٩0-9]+)',
        r'(?:خد|خذ|عايز|عيّش|عامل|ساوِر|حضي|تسلم|جيب)\s*([٠-٩0-9]+)',
        r'\b([0-9]+)\s*(?:قطع|pieces|واحد|شيء)\b',
        r'\b([0-9]+)\b',
    ]

    for pattern in patterns:
        match = re.search(pattern, message, re.IGNORECASE)
        if match:
            try:
                num_str = match.group(1)
                # Convert Arabic-Indic digits to Western digits
                num_str = num_str.translate(
                    str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
                )
                return int(num_str)
            except (ValueError, AttributeError):
                continue

    return None


def detect_modification_request(message: str, pending_order: dict | None) -> dict | None:
    """
    Detect if user is requesting a quantity modification.

    Returns updated pending_order dict or None.
    """
    if not pending_order:
        return None

    msg_lower = message.lower().strip()

    # Check for modification keywords
    has_modification_word = any(
        word.lower() in msg_lower for word in MODIFICATION_WORDS
    )

    if not has_modification_word:
        return None

    # Try to extract new quantity
    new_quantity = extract_quantity_from_message(message)

    if new_quantity is None:
        return None

    # Validate the new quantity
    product_id = pending_order.get("product_id")
    if not product_id:
        return None

    return {
        "product_id": product_id,
        "quantity": new_quantity,
        "original_requested": pending_order.get("original_requested"),
    }


# ---------------------------------------------------------------------------
# Store helper functions
# ---------------------------------------------------------------------------

def _get_store() -> FileStore:
    """Get singleton store instance."""
    return FileStore()


def _check_stock(product_id: str) -> dict:
    """Check stock for a product."""
    store = _get_store()
    return store.check_stock(product_id)


def _create_order(customer_id: str, items: list[dict], idempotency_key: str | None = None) -> dict:
    """Create an order."""
    store = _get_store()
    return store.create_order(customer_id, items, idempotency_key)


# ---------------------------------------------------------------------------
# Agent graph with multi-turn state
# ---------------------------------------------------------------------------

def create_agent_graph(
    user_role: str = "customer",
    user_id: str = "unknown",
    conversation_id: str = None,
):
    """
    Create a LangGraph agent workflow with multi-turn state.

    Args:
        user_role: "customer" or "admin"
        user_id: User identifier
        conversation_id: Unique ID for this conversation

    Returns:
        Compiled LangGraph application
    """
    if conversation_id is None:
        conversation_id = str(uuid.uuid4())[:8]

    # Select tools based on role
    store = FileStore()
    if user_role == "admin":
        tools = create_admin_tools(store)
    else:
        tools = create_customer_tools(store)

    # Bind tools to LLM
    llm = get_llm()
    llm_with_tools = llm.bind_tools(tools)

    # System message with role context
    system_content = SYSTEM_PROMPT.format(
        user_role=user_role,
        user_id=user_id,
        role_upper=user_role.upper()
    )
    system_message = SystemMessage(content=system_content)

    def agent_node(state: AgentState) -> dict:
        """
        Agent node with multi-turn state handling.

        Key behavior:
        1. If there's a pending confirmation and user confirms → execute
        2. If there's a pending rejection → cancel
        3. If there's a pending modification → update
        4. Otherwise → normal LLM processing
        """
        messages = state["messages"]
        pending_action = state.get("pending_action")
        pending_order = state.get("pending_order")
        user_role = state.get("user_role", "customer")
        user_id = state.get("user_id", "unknown")
        conversation_id = state.get("conversation_id", "default")

        # Get the latest human message
        latest_message = None
        for msg in reversed(messages):
            if isinstance(msg, HumanMessage):
                latest_message = msg.content
                break

        if not latest_message:
            return {"messages": [AIMessage(content="من فضلك أرسل رسالة.")]}

        # --- Handle pending confirmation ---
        if pending_action and pending_action == "create_order" and pending_order:

            # Check for quantity modification FIRST (before rejection)
            # "لا خد 3" contains "لا" which triggers rejection, but it's a modification
            modified_order = detect_modification_request(latest_message, pending_order)
            if modified_order:
                # Update pending order with new quantity
                new_quantity = modified_order["quantity"]
                product_id = modified_order["product_id"]

                # Check stock for the new quantity
                stock_info = _check_stock(product_id)
                available = stock_info.get("available_quantity", 0)

                if new_quantity <= available:
                    # New quantity is available, update pending
                    updated_pending = {
                        "product_id": product_id,
                        "quantity": new_quantity,
                        "product_name": pending_order.get("product_name"),
                        "original_requested": pending_order.get("original_requested"),
                    }
                    response_text = (
                        f"✅ تم تعديل الكمية إلى {new_quantity} قطعة.\n\n"
                        f"المتاح: {available} قطعة\n"
                        f"هل تؤكد طلب {new_quantity} قطعة؟"
                    )
                    return {
                        "messages": [AIMessage(content=response_text)],
                        "pending_action": "create_order",
                        "pending_order": updated_pending,
                    }
                else:
                    # New quantity exceeds stock
                    shortage = new_quantity - available
                    response_text = (
                        f"⚠️ الكمية المطلوبة ({new_quantity}) غير متاحة.\n\n"
                        f"المتاح حالياً: {available} قطعة فقط.\n"
                        f"النقص: {shortage} قطعة.\n\n"
                        f"اختر من الخيارات:\n"
                        f"١. أخذ الـ {available} المتاح\n"
                        f"٢. انتظار التوريد\n"
                        f"٣. منتج بديل"
                    )
                    # Keep pending state with updated quantity, ask user to choose
                    updated_pending = {
                        "product_id": product_id,
                        "quantity": new_quantity,
                        "product_name": pending_order.get("product_name"),
                        "original_requested": pending_order.get("original_requested"),
                    }
                    return {
                        "messages": [AIMessage(content=response_text)],
                        "pending_action": "create_order",
                        "pending_order": updated_pending,
                    }

            # Check for rejection
            if is_rejection(latest_message):
                # Cancel pending action
                response_text = (
                    "تم إلغاء الطلب. لا يوجد طلب جديد تم إنشاؤه. "
                    "إذا أردت بداية طلب آخر، أخبرني بالمنتج والكمية."
                )
                return {
                    "messages": [AIMessage(content=response_text)],
                    "pending_action": None,
                    "pending_order": None,
                }

            # Check for confirmation
            if is_confirmation(latest_message, pending_action):
                # Execute the pending order
                customer_id = user_id
                product_id = pending_order["product_id"]
                quantity = pending_order["quantity"]

                # Execute create_order
                order_result = _create_order(
                    customer_id=customer_id,
                    items=[{"product_id": product_id, "quantity": quantity}],
                    idempotency_key=f"{conversation_id}-{product_id}-{quantity}"
                )

                if order_result.get("success"):
                    order_id = order_result.get("order_id")
                    total = order_result.get("total", 0)
                    response_text = (
                        f"✅ تم إنشاء الطلب بنجاح!\n\n"
                        f"رقم الطلب: {order_id}\n"
                        f"المنتج: {pending_order.get('product_name', 'غير معروف')}\n"
                        f"الكمية: {quantity}\n"
                        f"الإجمالي: {total} جنيه\n\n"
                        f"شكرًا لتسليمك، ويمكنك متابعة حالة طلبك في أي وقت."
                    )
                else:
                    errors = order_result.get("errors", [])
                    response_text = (
                        f"⚠️ لم يتم إنشاء الطلب بسبب:\n"
                        f"{'؛ '.join(errors) if errors else 'خطأ غير معروف'}\n\n"
                        f"يرجى مراجعة الكمية أو اختيار منتج آخر."
                    )

                # Clear pending state
                return {
                    "messages": [AIMessage(content=response_text)],
                    "pending_action": None,
                    "pending_order": None,
                    "last_order_id": order_result.get("order_id") if order_result.get("success") else None,
                    "last_result": order_result,
                }

            # Check for quantity modification
            modified_order = detect_modification_request(latest_message, pending_order)
            if modified_order:
                # Update pending order with new quantity
                new_quantity = modified_order["quantity"]
                product_id = modified_order["product_id"]

                # Check stock for the new quantity
                stock_info = _check_stock(product_id)
                available = stock_info.get("available_quantity", 0)

                if new_quantity <= available:
                    # New quantity is available, update pending
                    updated_pending = {
                        "product_id": product_id,
                        "quantity": new_quantity,
                        "product_name": pending_order.get("product_name"),
                        "original_requested": pending_order.get("original_requested"),
                    }
                    response_text = (
                        f"✅ تم تعديل الكمية إلى {new_quantity} قطعة.\n\n"
                        f"المتاح: {available} قطعة\n"
                        f"هل تؤكد طلب {new_quantity} قطعة؟"
                    )
                    return {
                        "messages": [AIMessage(content=response_text)],
                        "pending_order": updated_pending,
                        # Keep pending_action as "create_order"
                    }
                else:
                    # New quantity exceeds stock
                    shortage = new_quantity - available
                    response_text = (
                        f"⚠️ الكمية المطلوبة ({new_quantity}) غير متاحة.\n\n"
                        f"المتاح حالياً: {available} قطعة فقط.\n"
                        f"النقص: {shortage} قطعة.\n\n"
                        f"اختر من الخيارات:\n"
                        f"١. أخذ الـ {available} المتاح\n"
                        f"٢. انتظار التوريد\n"
                        f"٣. منتج بديل"
                    )
                    # Don't change pending state, ask user to choose
                    return {"messages": [AIMessage(content=response_text)]}

        # --- No pending action: normal LLM processing ---
        # Prepend system message
        if not messages or not isinstance(messages[0], SystemMessage):
            messages = [system_message] + messages

        # Intercept: if user sent a pure confirmation word with NO pending action,
        # don't let the LLM call propose_order. Return a helpful message directly.
        if is_confirmation_word(latest_message):
            _conv_state = _get_conv_state(conversation_id)
            last_order_id_value = _conv_state.get("last_order_id")
            if last_order_id_value:
                response_text = (
                    f"✅ تم إنشاء الطلب من قبل: {last_order_id_value}.\n\n"
                    f"لا يوجد طلب قيد الانتظار حالياً للتأكيد.\n"
                    f"لو عايز تبدأ طلب جديد، قل لي اسم القطعة أو رقمها والكمية."
                )
            else:
                response_text = (
                    f"✅ عايز تؤكد حاجة؟ لا يوجد طلب قيد الانتظار حالياً.\n\n"
                    f"لو عايز تبدأ طلب جديد، قل لي اسم القطعة أو رقمها والكمية."
                )
            return {
                "messages": [AIMessage(content=response_text)],
                "pending_action": None,
                "pending_order": None,
                "last_order_id": _conv_state.get("last_order_id"),
                "last_result": None,
            }

        response = llm_with_tools.invoke(messages)

        # Check if LLM returned a tool call
        if hasattr(response, 'tool_calls') and response.tool_calls:
            tool_calls = response.tool_calls
        else:
            tool_calls = []

        result = {"messages": [response]}

        # Check if a propose_order ToolMessage was just executed
        # (comes back from ToolNode after LLM called propose_order)
        for msg in messages:
            from langchain_core.messages import ToolMessage
            if isinstance(msg, ToolMessage) and getattr(msg, 'name', None) == 'propose_order':
                tool_result = msg.content
                # ToolMessage.content may be a dict or a JSON string
                if isinstance(tool_result, dict):
                    proposal = tool_result
                elif isinstance(tool_result, str):
                    import json as _json
                    try:
                        proposal = _json.loads(tool_result)
                    except (_json.JSONDecodeError, TypeError):
                        proposal = {}
                else:
                    proposal = {}

                if proposal.get('status') == 'proposed':
                    product_id = proposal.get('product_id')
                    quantity = proposal.get('quantity', 0)
                    product_name = proposal.get('product_name', product_id)
                    original_requested = proposal.get('original_requested', quantity)

                    pending_order = {
                        'product_id': product_id,
                        'quantity': quantity,
                        'product_name': product_name,
                        'original_requested': original_requested,
                    }
                    response_text = (
                        f"✅ تم اقتراح طلب {quantity} قطعة من {product_name}.\n\n"
                        f'أيوه لتأكيد الطلب أو "لا" للإلغاء.'
                    )
                    return {
                        'messages': [AIMessage(content=response_text)],
                        'pending_action': 'create_order',
                        'pending_order': pending_order,
                    }

        # Fallback: if LLM returned text (no tool calls), check for
        # stock proposal text as a last resort
        if not tool_calls and isinstance(response, AIMessage) and response.content:
            content = response.content

            is_proposal = (
                "تقدر تختار" in content
                or "خيارات" in content
                or "تختار" in content
                or "1" in content
                or "متاح" in content
                or "قطع" in content
            )

            if is_proposal and latest_message:
                import re as _re

                pid_match = _re.search(r"PROD-\d+", latest_message)
                if not pid_match:
                    pid_match = _re.search(r"PROD-\d+", content)

                if pid_match:
                    product_id = pid_match.group(0)
                    stock_info = _check_stock(product_id)
                    available = stock_info.get("available_quantity", 0)

                    if available > 0:
                        product_name = stock_info.get(
                            "part_name",
                            stock_info.get("product_name", product_id),
                        )
                        pending_order = {
                            "product_id": product_id,
                            "quantity": available,
                            "product_name": product_name,
                            "original_requested": (
                                extract_quantity_from_message(latest_message)
                                or available
                            ),
                        }
                        enhanced = (
                            content
                            + "\n\n✅ الكمية متاحّة وبيُنتظر تأكيدك. رد بـ \"أيوه\" للمتابعة أو \"لا\" للإلغاء."
                        )
                        return {
                            "messages": [AIMessage(content=enhanced)],
                            "pending_action": "create_order",
                            "pending_order": pending_order,
                        }

        return result

    # Build the graph
    graph = StateGraph(AgentState)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", ToolNode(tools))

    # Conditional edge
    graph.add_conditional_edges(
        "agent",
        tools_condition,
        {"tools": "tools", "__end__": "__end__"}
    )

    # After tools execute, go back to agent
    graph.add_edge("tools", "agent")

    # Set entry point
    graph.set_entry_point("agent")

    return graph.compile()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def invoke_agent(
    message: str,
    user_role: str = "customer",
    user_id: str = "unknown",
    conversation_id: str = None,
) -> dict:
    """
    Invoke the agent with a user message.

    This is the main public API that Omar's backend should call.

    Args:
        message: User's natural language input
        user_role: "customer" or "admin"
        user_id: User identifier
        conversation_id: Unique ID for this conversation (optional)

    Returns:
        dict with:
            - message: Agent's response text
            - conversation_id: The conversation ID
            - requires_confirmation: True if pending confirmation
            - pending_action: Current pending action (if any)
            - pending_order: Pending order details (if any)
            - last_order_id: Last created order ID (if any)
            - action_executed: Name of action executed (if any)
            - state_changed: Whether state was modified
    """
    if conversation_id is None:
        conversation_id = str(uuid.uuid4())[:8]

    # Get or create conversation state
    conv_state = get_conversation_state(conversation_id)
    conv_state["user_role"] = user_role
    conv_state["user_id"] = user_id

    # Create the agent graph
    app = create_agent_graph(
        user_role=user_role,
        user_id=user_id,
        conversation_id=conversation_id
    )

    # Build messages from conversation state
    messages = list(conv_state.get("messages", []))

    # Add new human message
    messages.append(HumanMessage(content=message))

    # Invoke the graph — pass ALL conversation state fields so pending state persists
    initial_state = {
        "messages": messages,
        "pending_action": conv_state.get("pending_action"),
        "pending_order": conv_state.get("pending_order"),
        "user_role": user_role,
        "user_id": user_id,
        "conversation_id": conversation_id,
        "last_order_id": conv_state.get("last_order_id"),
        "last_result": conv_state.get("last_result"),
    }
    result = app.invoke(initial_state)

    # Update conversation state with new messages
    conv_state["messages"] = result.get("messages", [])

    # Extract response
    response_text = None
    last_ai_message = None
    for msg in reversed(result.get("messages", [])):
        if isinstance(msg, AIMessage) and msg.content:
            response_text = msg.content
            last_ai_message = msg
            break

    if not response_text:
        response_text = "عذراً، لم أتمكن من معالجة طلبك. حاول مرة أخرى."

    # Build response object
    pending_action = result.get("pending_action")
    pending_order = result.get("pending_order")
    last_order_id = result.get("last_order_id") or conv_state.get("last_order_id")
    last_result = result.get("last_result")

    # Update conversation state with new values
    if "pending_action" in result:
        conv_state["pending_action"] = result["pending_action"]
    if "pending_order" in result:
        conv_state["pending_order"] = result["pending_order"]
    if "last_order_id" in result:
        conv_state["last_order_id"] = result["last_order_id"]
    if "last_result" in result:
        conv_state["last_result"] = result["last_result"]

    # Determine if action was executed
    action_executed = None
    if last_result and isinstance(last_result, dict):
        if last_result.get("success") and last_result.get("order_id"):
            action_executed = "create_order"

    # Check if requires confirmation (has pending action)
    requires_confirmation = (
        conv_state.get("pending_action") is not None and
        conv_state.get("pending_order") is not None
    )

    return {
        "message": response_text,
        "conversation_id": conversation_id,
        "requires_confirmation": requires_confirmation,
        "pending_action": conv_state.get("pending_action"),
        "pending_order": conv_state.get("pending_order"),
        "last_order_id": last_order_id,
        "last_result": last_result,
        "action_executed": action_executed,
        "state_changed": (
            result.get("pending_action") is not None or
            result.get("pending_order") is not None or
            result.get("last_order_id") is not None
        ),
    }


def get_conversation_status(conversation_id: str) -> dict:
    """Get the current status of a conversation."""
    conv_state = get_conversation_state(conversation_id)
    return {
        "conversation_id": conversation_id,
        "pending_action": conv_state.get("pending_action"),
        "pending_order": conv_state.get("pending_order"),
        "user_role": conv_state.get("user_role"),
        "user_id": conv_state.get("user_id"),
        "last_order_id": conv_state.get("last_order_id"),
        "message_count": len(conv_state.get("messages", [])),
    }


def clear_conversation(conversation_id: str) -> None:
    """Clear a conversation's state."""
    clear_conversation_state(conversation_id)


# ---------------------------------------------------------------------------
# Interactive terminal
# ---------------------------------------------------------------------------

def run_interactive():
    """
    Run an interactive terminal session for testing the agent.
    """
    print("=" * 60)
    print("  ELDOCTOR AI Operations Agent")
    print("  Type a message or 'quit' to exit")
    print("=" * 60)

    role_input = input("\nAre you a [c]ustomer or [a]dmin? (c/a): ").strip().lower()
    if role_input == "a":
        user_role = "admin"
    else:
        user_role = "customer"

    user_id = input("Enter your customer/admin ID (e.g. CUST-001): ").strip()
    if not user_id:
        user_id = "CUST-001" if user_role == "customer" else "ADMIN-001"

    conversation_id = input("Conversation ID (optional, default: auto): ").strip()
    if not conversation_id:
        conversation_id = str(uuid.uuid4())[:8]

    print(f"\n--- Role: {user_role.upper()} | ID: {user_id} | Conversation: {conversation_id} ---\n")

    while True:
        try:
            user_input = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if user_input.lower() in ("quit", "exit", "q"):
            print("Goodbye!")
            break

        if not user_input:
            continue

        print()

        response = invoke_agent(
            message=user_input,
            user_role=user_role,
            user_id=user_id,
            conversation_id=conversation_id
        )

        print(f"{response['message']}\n")

        if response.get("requires_confirmation"):
            print(f"⚠️  Waiting for confirmation... (pending: {response.get('pending_action')})")
            if response.get("pending_order"):
                po = response["pending_order"]
                print(f"   Product: {po.get('product_name', po.get('product_id'))}")
                print(f"   Quantity: {po.get('quantity')}")
            print()


if __name__ == "__main__":
    run_interactive()
