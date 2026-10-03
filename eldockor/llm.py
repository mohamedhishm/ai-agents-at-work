import os
import re

from dotenv import load_dotenv
from langchain_core.messages import AIMessage

# Try to load .env from multiple locations
_loaded = False
_searched_paths = []

# Method 1: Load from agent package directory
_agent_dir = os.path.dirname(os.path.abspath(__file__))
_env_path = os.path.join(_agent_dir, ".env")
_searched_paths.append(_env_path)
if os.path.exists(_env_path):
    load_dotenv(_env_path, override=True)
    _loaded = True

# Method 2: Load from backend directory (sibling project)
_backend_dir = os.path.normpath(os.path.join(_agent_dir, "..", "backend"))
_backend_env = os.path.join(_backend_dir, ".env")
_searched_paths.append(_backend_env)
if os.path.exists(_backend_env):
    load_dotenv(_backend_env, override=True)
    _loaded = True

# Method 3: Fallback to default search
if not _loaded or not os.getenv("GROQ_API_KEY"):
    load_dotenv()
    _searched_paths.append("current directory (fallback)")


def _is_placeholder_key(api_key):
    """Check if the API key appears to be a test/placeholder value."""
    if not api_key:
        return True
    if "..." in api_key:
        return True
    if len(api_key) < 30:
        return True
    if api_key.strip().endswith("0jeu"):
        return True
    return False


# Arabic-Indic digit translation
_AR_TO_EN = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")

# Keywords for intent detection (lowercased)
_STOCK_WORDS = {"مخزون", "متوفر", "فيه", "موجود", "كم", "كمية", "عدد"}
_DETAIL_WORDS = {"تفاصيل", "عرض", "info", "product", "معلومات"}
_STATUS_WORDS = {"حالة", "ستاتس", "status", "تتبع", "تتبع"}
_ORDER_LIST_WORDS = {"طلباتي", "orders", "طلبات بتاعتي", "طلباتي"}
_SEARCH_WORDS = {"فلتر", "زيت", "هواء", "بطارية", "مصباح", "إطارة",
                  "زيت", "search", "find", "اعرض", "عايز", "غيار", "قطعة",
                  "مكبس", "فلام", "سحب", "سرب"}
_ADMIN_WORDS = {"مخزون الكل", "كل المنتجات", "inventory", "ملخص المخزون", "ايه المخزون", "المخزون كله", "اللي قربت تخلص", "المسودات", "ايه المسودات"}

_PID_RE = re.compile(r"(PROD-\d+)", re.IGNORECASE)
_OID_RE = re.compile(r"(ORD-\d+)", re.IGNORECASE)
_QTY_RE = re.compile(r"(\d+)")


def _extract_pid(text):
    m = _PID_RE.search(text)
    return m.group(1) if m else None


def _extract_oid(text):
    m = _OID_RE.search(text)
    return m.group(1) if m else None


def _extract_qty(text):
    """Extract an integer quantity from Arabic/English text."""
    clean = text.translate(_AR_TO_EN)
    # Remove product IDs (PROD-XXX) to avoid extracting quantities from them
    clean = re.sub(r'PROD-\d+', '', clean)
    nums = _QTY_RE.findall(clean)
    for n in nums:
        val = int(n)
        if 1 <= val <= 9999:
            return val
    return None


def _build_tool_call(name, args):
    """Return a single-element tool_calls list in LangGraph format."""
    return [{
        "name": name,
        "args": args,
        "id": f"call_{name}",
        "type": "tool_call",
    }]


class MockLLM:
    """Deterministic mock LLM for integration testing.

    When a valid GROQ_API_KEY is not present, this mock parses the user
    message, decides which Store-backed tool to call, and returns an
    AIMessage with the appropriate ``tool_calls``.

    The mock is **not** used in production. It exists purely so the
    integration can run end-to-end and the Phase 1 referee tests can
    validate the deterministic transaction-safety paths without
    consuming Groq quota.
    """

    model_name = "mock-llm-fallback"
    _tools = None  # dict mapping tool name -> tool object

    # ------------------------------------------------------------------
    # LangChain compatibility shims
    # ------------------------------------------------------------------
    def bind_tools(self, tools):
        self._tools = {t.name: t for t in tools}
        return self

    def __getattr__(self, name):
        """Gracefully swallow any method calls that ChatGroq would have."""
        if name.startswith("_"):
            raise AttributeError(name)
        return lambda *a, **kw: None

    # ------------------------------------------------------------------
    # Main entry point — called by LangGraph's agent node
    # ------------------------------------------------------------------
    def invoke(self, messages, **kwargs):
        from langchain_core.messages import ToolMessage, HumanMessage, AIMessage as _AIMessage
        
        # Check for ToolMessages from previous tool calls
        for msg in messages:
            if isinstance(msg, ToolMessage):
                content = getattr(msg, "content", "")
                tool_name = getattr(msg, "name", "")
                
                # Parse content if it's a JSON string
                if isinstance(content, str) and content.strip().startswith("{"):
                    try:
                        import json as _json
                        content = _json.loads(content)
                    except (ValueError, TypeError):
                        pass
                
                # If we just ran check_stock and the user wanted to order,
                # now call propose_order with the available quantity
                if tool_name == "check_stock" and content and isinstance(content, dict):
                    # Find the original user request for quantity
                    qty = None
                    pid = None
                    for m in reversed(messages):
                        if isinstance(m, HumanMessage):
                            content_str = m.content
                            pid = _extract_pid(content_str)  # use original case
                            qty = _extract_qty(content_str)
                            break
                    
                    if pid and qty and qty > 0:
                        available = content.get("available_quantity", 0)
                        if available > 0:
                            total_requested = qty
                            proposed_qty = min(total_requested, available)
                            product_name = content.get("part_name") or content.get("name") or pid
                            # Get original request
                            original_requested = total_requested
                            return AIMessage(
                                content=f"المتاح {proposed_qty} قطعة من {product_name}.",
                                tool_calls=_build_tool_call("propose_order", {
                                    "product_id": pid,
                                    "quantity": proposed_qty,
                                    "product_name": product_name,
                                    "original_requested": original_requested,
                                }),
                            )
                        else:
                            return AIMessage(
                                content="المنتج غير متوفر بالمخزون حالياً. ممكن أساعدك بمنتج تاني؟",
                                tool_calls=[],
                            )
                
                # If we just ran search_products, format results
                if tool_name == "search_products" and content:
                    if isinstance(content, dict) and content.get("count", 0) > 0:
                        products_list = content.get("results", [])
                        msg_text = "لقيت لك شوية منتجات:\n\n"
                        for p in products_list[:5]:
                            msg_text += f"- {p.get('product_id')}: {p.get('name', p.get('part_name', ''))} — {p.get('price', 0)} جنيه — متوفر {p.get('available_quantity', 0)} قطعة\n"
                        return AIMessage(content=msg_text, tool_calls=[])
                    elif isinstance(content, dict) and content.get("count", 0) == 0:
                        return AIMessage(
                            content="معنديش أي نتيجة لبحث. جرب تديني تفاصيل أكتر مثل رقم المنتج أو الماركة.",
                            tool_calls=[],
                        )
                    elif isinstance(content, str):
                        return AIMessage(content=content, tool_calls=[])
                
                # If we just ran get_order_status, format the result
                if tool_name == "get_order_status" and content:
                    if isinstance(content, dict):
                        status = content.get("status", "unknown")
                        order_id = content.get("order_id", "unknown")
                        if status:
                            return AIMessage(
                                content=f"الطلب {order_id} حالته: {status}.",
                                tool_calls=[],
                            )
                        else:
                            return AIMessage(
                                content=f"الطلب {order_id} غير موجود.",
                                tool_calls=[],
                            )
                    elif isinstance(content, str):
                        return AIMessage(content=content, tool_calls=[])
                
                # If we just ran get_product_details, format the result
                if tool_name == "get_product_details" and content:
                    if isinstance(content, dict):
                        name = content.get("name", content.get("part_name", "unknown"))
                        qty = content.get("available_quantity", 0)
                        price = content.get("price", 0)
                        return AIMessage(
                            content=f"📦 {name} — المتاح: {qty} قطعة — السعر: {price} جنيه",
                            tool_calls=[],
                        )
                    elif isinstance(content, str):
                        return AIMessage(content=content, tool_calls=[])
                
                # If we just ran get_inventory_summary, format the result
                if tool_name == "get_inventory_summary" and content:
                    if isinstance(content, dict):
                        total = content.get("total_items", 0)
                        out_of_stock = content.get("out_of_stock_count", 0)
                        low_stock = content.get("low_stock_count", 0)
                        return AIMessage(
                            content=f"📋 ملخص المخزون: {total} منتجات، {out_of_stock} نفذت، {low_stock} قريبة من النفاد.",
                            tool_calls=[],
                        )
                    elif isinstance(content, str):
                        return AIMessage(content=content, tool_calls=[])
                
                # If we just ran get_low_stock_items, format the result
                if tool_name == "get_low_stock_items" and content:
                    if isinstance(content, dict):
                        items = content.get("items", [])
                        return AIMessage(
                            content=f"📋 المنتجات قليلة المخزون: {len(items)} منتج.",
                            tool_calls=[],
                        )
                    elif isinstance(content, str):
                        return AIMessage(content=content, tool_calls=[])
                
                # If we just ran list_reorder_drafts, format the result
                if tool_name == "list_reorder_drafts" and content:
                    if isinstance(content, dict):
                        drafts = content.get("reorder_drafts", [])
                        return AIMessage(
                            content=f"📋 مسودات إعادة الطلب: {len(drafts)} مسودة.",
                            tool_calls=[],
                        )
                    elif isinstance(content, str):
                        return AIMessage(content=content, tool_calls=[])

        # No ToolMessage in conversation — parse the human message
        last = messages[-1] if messages else None
        content = getattr(last, "content", "") or ""
        content_l = content.lower().strip()
        pid = _extract_pid(content)  # use original case to preserve PROD-003
        oid = _extract_oid(content)
        qty = _extract_qty(content)

        # 1. Order request: "عايز 10 من PROD-003"
        if pid and qty and qty > 0:
            return AIMessage(
                content=f"جاري التحقق من المخزون لـ {pid}.",
                tool_calls=_build_tool_call("check_stock", {"product_id": pid}),
            )

        # 2. Product search: "فلتر زيت" or "عايز فلتر زيت"
        if any(kw in content_l for kw in _SEARCH_WORDS) and not pid:
            return AIMessage(
                content=f"جاري البحث عن: {content}",
                tool_calls=_build_tool_call("search_products", {"query": content}),
            )

        # 3. Stock check for specific product: "كم مخزون PROD-003"
        if pid and any(kw in content_l for kw in _STOCK_WORDS):
            return AIMessage(
                content=f"جاري فحص المخزون لـ {pid}.",
                tool_calls=_build_tool_call("check_stock", {"product_id": pid}),
            )

        # 4. Product details: "تفاصيل PROD-003"
        if pid and any(kw in content_l for kw in _DETAIL_WORDS):
            return AIMessage(
                content=f"جاري عرض تفاصيل {pid}.",
                tool_calls=_build_tool_call("get_product_details", {"product_id": pid}),
            )

        # 5. Order status: "حالة الطلب ORD-001"
        if oid and any(kw in content_l for kw in _STATUS_WORDS):
            return AIMessage(
                content=f"جاري فحص حالة الطلب {oid}.",
                tool_calls=_build_tool_call("get_order_status", {"order_id": oid}),
            )

        # 6. Customer orders / history
        if any(kw in content_l for kw in _ORDER_LIST_WORDS):
            # Return a prompt for the user to specify an order ID
            return AIMessage(
                content="يمكنك متابعة طلبك برقمه. مثلاً: 'حالة الطلب ORD-001'",
                tool_calls=[],
            )

        # 7. Admin-level inventory request via natural language
        if any(kw in content_l for kw in _ADMIN_WORDS):
            if "get_inventory_summary" in (self._tools or {}):
                return AIMessage(
                    content="جاري تجهيز ملخص المخزون.",
                    tool_calls=_build_tool_call("get_inventory_summary", {}),
                )
            if "get_low_stock_items" in (self._tools or {}):
                return AIMessage(
                    content="جاري فحص المنتجات منخفضة المخزون.",
                    tool_calls=_build_tool_call("get_low_stock_items", {}),
                )
            if "list_reorder_drafts" in (self._tools or {}):
                return AIMessage(
                    content="جاري تجهيز مسودات إعادة الطلب.",
                    tool_calls=_build_tool_call("list_reorder_drafts", {}),
                )
            # Customer asking for admin-level info → blocked
            return AIMessage(
                content="⚠️ غير مسموح. أدوات الأدمن مخصصة للأدمن فقط. "
                        "تواصل مع الأدمن للاستفسار عن المخزون أو إعادة الطلب.",
                tool_calls=[],
            )

        # Default fallback
        return AIMessage(
            content=(
                "أقدر أساعدك في: بحث عن قطع غيار، متابعة طلب، أو طلب جديد.\n"
                "مثلاً: 'عايز فلتر زيت' أو 'حالة الطلب ORD-001' أو 'تفاصيل PROD-003'"
            ),
            tool_calls=[],
        )


def get_llm():
    """Return a real ChatGroq if the API key is valid, otherwise MockLLM."""
    api_key = os.getenv("GROQ_API_KEY")

    if _is_placeholder_key(api_key):
        return MockLLM()

    try:
        from langchain_groq import ChatGroq

        return ChatGroq(
            model="openai/gpt-oss-120b",
            temperature=0,
            api_key=api_key,
        )
    except Exception as exc:
        print(f"WARNING: Could not initialise ChatGroq ({exc}); using MockLLM.")
        return MockLLM()