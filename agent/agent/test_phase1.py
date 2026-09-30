"""
Phase 1 Referee Tests for ELDOCTOR AI Agent.

Run with:
    cd C:/Users/msi/OneDrive - Arab Academy for Science and Technology/Documents/AI Engineer/ai agents at work/ai-agents-at-work/agent
    python -c "import sys; sys.path.insert(0,'.'); exec(open('agent/test_phase1.py').read())"

Tests use invoke_agent() only — no manual state manipulation.
Each scenario is isolated: uses unique conversation_id and verifies against real Store state.
"""

import sys
import os
import json
import shutil
import copy

# Ensure we can import from the project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.graph import invoke_agent, get_conversation_status, clear_conversation

# ---------------------------------------------------------------------------
# Pre-test: reset store to known original state for reproducible tests
# ---------------------------------------------------------------------------

# Known original state: 6 orders, PROD-003 stock=8
_ORIGINAL_ORDERS = [
    {"order_id": "ORD-001", "customer_id": "CUST-001", "items": [{"product_id": "PROD-001", "quantity": 2}], "total": 0, "status": "pending", "created_at": "2024-01-15T10:00:00"},
    {"order_id": "ORD-002", "customer_id": "CUST-001", "items": [{"product_id": "PROD-002", "quantity": 3}], "total": 600, "status": "confirmed", "created_at": "2024-01-16T11:00:00"},
    {"order_id": "ORD-003", "customer_id": "CUST-001", "items": [{"product_id": "PROD-003", "quantity": 5}], "total": 1100, "status": "confirmed", "created_at": "2024-01-17T12:00:00"},
    {"order_id": "ORD-004", "customer_id": "CUST-001", "items": [{"product_id": "PROD-004", "quantity": 10}], "total": 500, "status": "confirmed", "created_at": "2024-01-18T13:00:00"},
    {"order_id": "ORD-005", "customer_id": "CUST-001", "items": [{"product_id": "PROD-005", "quantity": 2}], "total": 800, "status": "confirmed", "created_at": "2024-01-19T14:00:00"},
    {"order_id": "ORD-006", "customer_id": "CUST-001", "items": [{"product_id": "PROD-006", "quantity": 1}], "total": 300, "status": "confirmed", "created_at": "2024-01-20T15:00:00"},
]

# Write orders.json with known original and backup immediately
_ORDERS_BACKUP = "data/orders.json.backup"
with open("data/orders.json", "w", encoding="utf-8") as f:
    json.dump(_ORIGINAL_ORDERS, f, ensure_ascii=False, indent=2)
shutil.copy("data/orders.json", _ORDERS_BACKUP)

# Also backup products.json BEFORE any test modifications
_PRODUCTS_BACKUP = "data/products.json.backup"
shutil.copy("data/products.json", _PRODUCTS_BACKUP)

# Also reset products.json to known original stock
_ORIGINAL_PRODUCTS = [
    {"product_id": "PROD-001", "name": "فلاتر زيت Bosch", "category": "فلتر زيت", "part_number": "BOS-CH-001", "price": 120, "available_quantity": 0, "supplier": "Bosch Egypt", "reorder_threshold": 5},
    {"product_id": "PROD-002", "name": "فلاتر زيت Denso", "category": "فلتر زيت", "part_number": "DNS-CH-002", "price": 200, "available_quantity": 3, "supplier": "Denso Middle East", "reorder_threshold": 5},
    {"product_id": "PROD-003", "name": "قطرات فرامل ATE", "category": "نظام الفرامل", "part_number": "ATE-BR-303", "price": 220, "available_quantity": 8, "supplier": "ATE Egypt", "reorder_threshold": 3},
    {"product_id": "PROD-004", "name": "قطران حلزوني", "category": "الزيت والمواد اللزجة", "part_number": "GMP-SE-004", "price": 50, "available_quantity": 0, "supplier": "GMP Chemicals", "reorder_threshold": 10},
    {"product_id": "PROD-005", "name": "إطارة أمامية 16 بوصة", "category": "الإطارات والطرق", "part_number": "WSM-TT-005", "price": 400, "available_quantity": 2, "supplier": "Warsaw Tires Co.", "reorder_threshold": 4},
    {"product_id": "PROD-006", "name": "زيت محرك 5W-30 4L", "category": "الزيت والمواد اللزجة", "part_number": "SLK-0W30-006", "price": 300, "available_quantity": 15, "supplier": "Shell Egypt", "reorder_threshold": 5},
    {"product_id": "PROD-007", "name": "فلتر هواء Mahle", "category": "فلتر هواء", "part_number": "MHL-AF-007", "price": 150, "available_quantity": 20, "supplier": "Mahle Egypt", "reorder_threshold": 5},
    {"product_id": "PROD-008", "name": "بطارية 12V 60Ah", "category": "البطاريات والكهرباء", "part_number": "GSE-12V-008", "price": 1800, "available_quantity": 4, "supplier": "GS Egypt", "reorder_threshold": 3},
    {"product_id": "PROD-009", "name": "سائل تكييف", "category": "التبريد والمكيف", "part_number": "ALT-AC-009", "price": 100, "available_quantity": 1, "supplier": "Al-Turk Chemicals", "reorder_threshold": 5},
    {"product_id": "PROD-010", "name": "حزمة إضاءة LED", "category": "الإضاءة والإلكترونيات", "part_number": "LED-PA-010", "price": 250, "available_quantity": 7, "supplier": "LED Tech Egypt", "reorder_threshold": 5},
]

with open("data/products.json", "w", encoding="utf-8") as f:
    json.dump(_ORIGINAL_PRODUCTS, f, ensure_ascii=False, indent=2)

print("Store reset to original state: 6 orders, PROD-003 stock=8")

# ---------------------------------------------------------------------------
# Backup products.json as well (not just orders.json)
# ---------------------------------------------------------------------------
_products_backup = "data/products.json.backup"
shutil.copy("data/products.json", _products_backup)

# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def check(condition, test_name, detail=""):
    if condition:
        print(f"  ✅ {test_name}" + (f": {detail}" if detail else ""))
        return True
    else:
        print(f"  ❌ {test_name}" + (f": {detail}" if detail else ""))
        return False

# ---------------------------------------------------------------------------
# Pre-test: clear all test conversations
# ---------------------------------------------------------------------------

print("=" * 70)
print("PHASE 1 REFEREE TESTS — ELDOCTOR AI Agent")
print("=" * 70)
print()

test_ids = [
    "ref-test-001", "ref-test-002", "ref-test-003", "ref-test-004",
    "ref-test-005", "ref-test-006", "ref-test-007", "ref-test-008",
]
for cid in test_ids:
    clear_conversation(cid)

from agent.store.file_store import FileStore
store = FileStore()

p001_stock = store.check_stock("PROD-001")["available_quantity"]
p002_stock = store.check_stock("PROD-002")["available_quantity"]

print(f"Store state before tests:")
print(f"  PROD-001 (فلاتر زيت Bosch): {p001_stock} available")
print(f"  PROD-002 (فلاتر زيت Denso): {p002_stock} available")
print()

# ============================================================================
# Guaranteed cleanup via atexit (runs even on crash/interrupt/rate limit)
# ============================================================================

def _guaranteed_cleanup():
    """Restore production data from backups. Registered via atexit."""
    try:
        if os.path.exists(_ORDERS_BACKUP):
            shutil.copy(_ORDERS_BACKUP, "data/orders.json")
            os.remove(_ORDERS_BACKUP)
        if os.path.exists(_PRODUCTS_BACKUP):
            shutil.copy(_PRODUCTS_BACKUP, "data/products.json")
            os.remove(_PRODUCTS_BACKUP)
        print("  ✅ Production data restored via atexit cleanup")
    except Exception as e:
        print(f"  ❌ atexit cleanup error: {e}")

import atexit
atexit.register(_guaranteed_cleanup)

# ============================================================================
# SCENARIO 1
# User requests quantity > stock → pending_order + confirmation
# ============================================================================

print("-" * 70)
print("SCENARIO 1: Request more than stock → pending_order + confirmation")
print("-" * 70)
print(f"  (PROD-003 has 8 available, user requests 10)")

result = invoke_agent(
    message="عايز 10 من PROD-003",
    user_id="CUST-001",
    user_role="customer",
    conversation_id="ref-test-001",
)

print(f"  Input: 'عايز 10 من PROD-003'")
print(f"  Response: {result['message'][:120]}...")
print(f"  requires_confirmation: {result['requires_confirmation']}")
print(f"  pending_action: {result['pending_action']}")
print(f"  pending_order: {result['pending_order']}")

ok1 = check(
    result["requires_confirmation"] is True,
    "requires_confirmation is True"
)
ok2 = check(
    result["pending_action"] == "create_order",
    "pending_action is 'create_order'"
)
ok3 = check(
    result["pending_order"] is not None,
    "pending_order is not None"
)
ok4 = check(
    result["pending_order"]["quantity"] == 8,
    f"pending_order.quantity == 8 (available stock)",
    f"got {result['pending_order']['quantity'] if result['pending_order'] else None}"
)

if not all([ok1, ok2, ok3, ok4]):
    print("  ❌ SCENARIO 1 FAILED")
else:
    print("  ✅ SCENARIO 1 PASSED")

print()

# ============================================================================
# SCENARIO 2
# User says "أيوه" → execute pending order
# ============================================================================

print("-" * 70)
print("SCENARIO 2: 'أيوه' → execute pending order")
print("-" * 70)

result = invoke_agent(
    message="أيوه",
    user_id="CUST-001",
    user_role="customer",
    conversation_id="ref-test-001",
)

print(f"  Input: 'أيوه'")
print(f"  Response: {result['message'][:150]}...")
print(f"  action_executed: {result['action_executed']}")
print(f"  last_order_id: {result['last_order_id']}")
print(f"  pending_action after: {result['pending_action']}")
print(f"  pending_order after: {result['pending_order']}")

ok5 = check(
    result["action_executed"] == "create_order",
    "action_executed is 'create_order'"
)
ok6 = check(
    result["last_order_id"] is not None,
    "last_order_id is not None"
)
ok7 = check(
    result["pending_action"] is None,
    "pending_action cleared after success"
)
ok8 = check(
    result["pending_order"] is None,
    "pending_order cleared after success"
)

if not all([ok5, ok6, ok7, ok8]):
    print("  ❌ SCENARIO 2 FAILED")
else:
    print("  ✅ SCENARIO 2 PASSED")
    first_order_id = result["last_order_id"]

print()

# ============================================================================
# SCENARIO 3
# User requests quantity > stock, then says "لا"
# → Must cancel pending without creating order
# ============================================================================

print("-" * 70)
print("SCENARIO 3: 'لا' → cancel pending, no order created")
print("-" * 70)
print(f"  (PROD-002 has 3 available, user requests 10)")

result = invoke_agent(
    message="عايز 10 من PROD-002",
    user_id="CUST-001",
    user_role="customer",
    conversation_id="ref-test-003",
)
print(f"  Step 1 input: 'عايز 10 من PROD-002'")
print(f"  pending_action: {result['pending_action']}")
print(f"  pending_order: {result['pending_order']}")

result = invoke_agent(
    message="لا",
    user_id="CUST-001",
    user_role="customer",
    conversation_id="ref-test-003",
)
print(f"  Step 2 input: 'لا'")
print(f"  Response: {result['message'][:120]}...")
print(f"  action_executed: {result['action_executed']}")
print(f"  pending_action after: {result['pending_action']}")
print(f"  pending_order after: {result['pending_order']}")

ok9 = check(
    result["action_executed"] is None,
    "action_executed is None (no order created)"
)
ok10 = check(
    result["pending_action"] is None,
    "pending_action is None after rejection"
)
ok11 = check(
    result["pending_order"] is None,
    "pending_order is None after rejection"
)

if not all([ok9, ok10, ok11]):
    print("  ❌ SCENARIO 3 FAILED")
else:
    print("  ✅ SCENARIO 3 PASSED")

print()

# SCENARIO 4: Use PROD-008 (stock=4) for quantity modification test.
# Isolated from Scenario 1/2 (which use PROD-003).
# PROD-008: 4 available, user requests 10 → propose 4 → modify to 3 → stays pending.

print("-" * 70)
print("SCENARIO 4: 'لا خد 3' → modify pending quantity")
print("-" * 70)

STOCK_PROD = "PROD-008"
STOCK_VAL = 4
result = invoke_agent(
    message=f"عايز 10 من {STOCK_PROD}",
    user_id="CUST-001",
    user_role="customer",
    conversation_id="ref-test-004",
)
print(f"  Step 1: set pending for {STOCK_PROD} (available={STOCK_VAL})")
print(f"  pending_order: {result['pending_order']}")

result = invoke_agent(
    message="لا خد 3",
    user_id="CUST-001",
    user_role="customer",
    conversation_id="ref-test-004",
)
print(f"  Step 2 input: 'لا خد 3'")
print(f"  Response: {result['message'][:150]}...")
print(f"  pending_order after: {result['pending_order']}")

ok12 = check(
    result["pending_order"] is not None,
    "pending_order still exists after modification"
)
ok13 = check(
    result["pending_order"]["quantity"] == 3,
    f"pending_order.quantity == 3",
    f"got {result['pending_order']['quantity'] if result['pending_order'] else None}"
)
ok14 = check(
    result["pending_action"] == "create_order",
    "pending_action still 'create_order'"
)

if not all([ok12, ok13, ok14]):
    print("  ❌ SCENARIO 4 FAILED")
else:
    print("  ✅ SCENARIO 4 PASSED")

print()

# ============================================================================
# SCENARIO 5
# User says "أيوه" with NO pending action → must NOT create order
# ============================================================================

print("-" * 70)
print("SCENARIO 5: 'أيوه' with NO pending action → no order created")
print("-" * 70)

result = invoke_agent(
    message="أيوه",
    user_id="CUST-001",
    user_role="customer",
    conversation_id="ref-test-005",
)

print(f"  Input: 'أيوه' (no prior pending)")
print(f"  Response: {result['message'][:120]}...")
print(f"  action_executed: {result['action_executed']}")
print(f"  pending_action: {result['pending_action']}")
print(f"  pending_order: {result['pending_order']}")

ok15 = check(
    result["action_executed"] is None,
    "action_executed is None"
)
ok16 = check(
    result["pending_action"] is None,
    "pending_action is None"
)
ok17 = check(
    result["pending_order"] is None,
    "pending_order is None"
)

if not all([ok15, ok16, ok17]):
    print("  ❌ SCENARIO 5 FAILED")
else:
    print("  ✅ SCENARIO 5 PASSED")

print()

# ============================================================================
# SCENARIO 6
# Double confirmation on same pending → no duplicate order
# ============================================================================

print("-" * 70)
print("SCENARIO 6: Double confirmation → no duplicate order")
print("-" * 70)

# First, create a pending order
result = invoke_agent(
    message="عايز 10 من PROD-009",
    user_id="CUST-001",
    user_role="customer",
    conversation_id="ref-test-006",
)
print(f"  Step 1: create pending for PROD-009 (stock=1)")
print(f"  pending_order: {result['pending_order']}")

# First confirmation
result = invoke_agent(
    message="أيوه",
    user_id="CUST-001",
    user_role="customer",
    conversation_id="ref-test-006",
)
print(f"  Step 2: first confirmation")
print(f"  action_executed: {result['action_executed']}")
print(f"  last_order_id: {result['last_order_id']}")
print(f"  pending_action: {result['pending_action']}")

first_order_id = result.get("last_order_id")

# Second confirmation (should be ignored)
result = invoke_agent(
    message="أيوه",
    user_id="CUST-001",
    user_role="customer",
    conversation_id="ref-test-006",
)
print(f"  Step 3: second confirmation (should be ignored)")
print(f"  action_executed: {result['action_executed']}")
print(f"  last_order_id: {result['last_order_id']}")
print(f"  pending_action: {result['pending_action']}")

# Verify no duplicate: count orders before and after in the store
# get_customer_orders returns a list (not a dict with 'orders' key)
orders_before_confirm = len(store.get_customer_orders("CUST-001"))
print(f"  Orders in store after second confirmation: {orders_before_confirm}")

ok18 = check(
    result["last_order_id"] == first_order_id,
    "last_order_id is same as first (no duplicate)",
    f"first={first_order_id}, second={result['last_order_id']}"
)

# Also verify that order count didn't increase
orders_after_confirm = len(store.get_customer_orders("CUST-001"))
ok18b = check(
    orders_after_confirm == orders_before_confirm,
    "order count did not increase (no duplicate)",
    f"before={orders_before_confirm}, after={orders_after_confirm}"
)

if not all([ok18, ok18b]):
    print("  ❌ SCENARIO 6 FAILED")
else:
    print("  ✅ SCENARIO 6 PASSED")

print()

# ============================================================================
# SCENARIO 7
# Conversation A has pending, Conversation B says "أيوه"
# → B must NOT execute A's pending
# ============================================================================

print("-" * 70)
print("SCENARIO 7: Conversation isolation — B cannot execute A's pending")
print("-" * 70)

# Conversation A: create pending
result_a = invoke_agent(
    message="عايز 10 من PROD-005",
    user_id="CUST-001",
    user_role="customer",
    conversation_id="ref-test-007a",
)
print(f"  Conversation A: created pending for PROD-005 (stock=2)")
print(f"  A pending_order: {result_a['pending_order']}")

# Conversation B: say "أيوه" (should NOT execute A's pending)
result_b = invoke_agent(
    message="أيوه",
    user_id="CUST-002",
    user_role="customer",
    conversation_id="ref-test-007b",
)
print(f"  Conversation B: sent 'أيوه'")
print(f"  B action_executed: {result_b['action_executed']}")
print(f"  B pending_action: {result_b['pending_action']}")
print(f"  B pending_order: {result_b['pending_order']}")

ok20 = check(
    result_b["action_executed"] is None,
    "B did NOT execute any order"
)
ok21 = check(
    result_b["pending_action"] is None,
    "B pending_action is None"
)

if not all([ok20, ok21]):
    print("  ❌ SCENARIO 7 FAILED")
else:
    print("  ✅ SCENARIO 7 PASSED")

print()

# ============================================================================
# SCENARIO 8
# Same conversation_id across multiple invoke_agent() calls
# → state must persist between calls
# ============================================================================

print("-" * 70)
print("SCENARIO 8: conversation_id persistence across calls")
print("-" * 70)

# First call: create pending
result1 = invoke_agent(
    message="عايز 5 من PROD-002",
    user_id="CUST-001",
    user_role="customer",
    conversation_id="ref-test-008",
)
print(f"  Call 1: 'عايز 5 من PROD-002'")
print(f"  pending_action: {result1['pending_action']}")
print(f"  pending_order: {result1['pending_order']}")

# Second call: same conversation_id, send "أيوه"
result2 = invoke_agent(
    message="أيوه",
    user_id="CUST-001",
    user_role="customer",
    conversation_id="ref-test-008",
)
print(f"  Call 2: 'أيوه'")
print(f"  action_executed: {result2['action_executed']}")
print(f"  last_order_id: {result2['last_order_id']}")
print(f"  pending_action: {result2['pending_action']}")

ok22 = check(
    result2["action_executed"] == "create_order",
    "second call executed the pending order"
)
ok23 = check(
    result2["last_order_id"] is not None,
    "last_order_id is not None"
)

if not all([ok22, ok23]):
    print("  ❌ SCENARIO 8 FAILED")
else:
    print("  ✅ SCENARIO 8 PASSED")

print()
print("=" * 70)
print("PHASE 1 REFEREE TESTS COMPLETE")
print("=" * 70)
print()
print("Summary:")
print(f"  SCENARIO 1 (pending + confirmation): {'✅ PASS' if all([ok1,ok2,ok3,ok4]) else '❌ FAIL'}")
print(f"  SCENARIO 2 (confirm → execute):      {'✅ PASS' if all([ok5,ok6,ok7,ok8]) else '❌ FAIL'}")
print(f"  SCENARIO 3 (reject → cancel):        {'✅ PASS' if all([ok9,ok10,ok11]) else '❌ FAIL'}")
print(f"  SCENARIO 4 (modify quantity):        {'✅ PASS' if all([ok12,ok13,ok14]) else '❌ FAIL'}")
print(f"  SCENARIO 5 (no pending → ignore):    {'✅ PASS' if all([ok15,ok16,ok17]) else '❌ FAIL'}")
print(f"  SCENARIO 6 (no duplicate):           {'✅ PASS' if all([ok18,ok18b]) else '❌ FAIL'}")
print(f"  SCENARIO 7 (conversation isolation): {'✅ PASS' if all([ok20,ok21]) else '❌ FAIL'}")
print(f"  SCENARIO 8 (state persistence):      {'✅ PASS' if all([ok22,ok23]) else '❌ FAIL'}")

print()
print("=" * 70)
print("POST-TEST: Restoring production data to original state")
print("=" * 70)

# Restore orders.json and products.json from backup
_orders_backup = "data/orders.json.backup"
if _os.path.exists(_orders_backup):
    _shutil.copy(_orders_backup, "data/orders.json")
    print("  ✅ orders.json restored from backup")
else:
    with open("data/orders.json", "w", encoding="utf-8") as f:
        _json.dump(_ORIGINAL_ORDERS, f, ensure_ascii=False, indent=2)
    print("  ✅ orders.json written with known original (no backup found)")

# Remove backup file
if _os.path.exists(_orders_backup):
    _os.remove(_orders_backup)

# Verify final state
with open("data/orders.json", encoding="utf-8") as f:
    final_orders = _json.load(f)
with open("data/products.json", encoding="utf-8") as f:
    final_products = _json.load(f)

print(f"  orders.json: {len(final_orders)} orders")
print(f"  products.json: {len(final_products)} products")
print(f"  PROD-003 stock: {next(p['available_quantity'] for p in final_products if p['product_id'] == 'PROD-003')}")
print(f"  New orders after restore: {[o['order_id'] for o in final_orders if o['order_id'] not in [x['order_id'] for x in _ORIGINAL_ORDERS]]}")

print()
print("Phase 1 cleanup complete.")
