import json, urllib.request

# Login
req = urllib.request.Request(
    "http://localhost:8000/auth/login",
    data=json.dumps({"email": "salma@eldoctor.com", "password": "demo1234"}).encode("utf-8"),
    headers={"Content-Type": "application/json"},
)
resp = urllib.request.urlopen(req)
token = json.loads(resp.read().decode("utf-8"))["token"]
print(f"Token: {token[:20]}...")

# Step 1: Create pending order
req = urllib.request.Request(
    "http://localhost:8000/agents/message",
    data=json.dumps({"message": "عايز 10 من PROD-003", "conversation_id": "http-py-1"}).encode("utf-8"),
    headers={"Content-Type": "application/json; charset=utf-8", "Authorization": f"Bearer {token}"},
)
resp = urllib.request.urlopen(req)
r1 = json.loads(resp.read().decode("utf-8"))
print(f"\nStep 1 - proposal:")
print(f"  reply: {r1.get('reply', '')[:80]}")
print(f"  requires_confirmation: {r1.get('requires_confirmation')}")
print(f"  pending_order: {r1.get('pending_order')}")

# Step 2: Confirm
req = urllib.request.Request(
    "http://localhost:8000/agents/message",
    data=json.dumps({"message": "أيوه", "conversation_id": "http-py-1"}).encode("utf-8"),
    headers={"Content-Type": "application/json; charset=utf-8", "Authorization": f"Bearer {token}"},
)
resp = urllib.request.urlopen(req)
r2 = json.loads(resp.read().decode("utf-8"))
print(f"\nStep 2 - confirmation:")
print(f"  reply: {r2.get('reply', '')[:80]}")
print(f"  action_executed: {r2.get('action_executed')}")
print(f"  order_id: {r2.get('order_id')}")
print(f"  requires_confirmation: {r2.get('requires_confirmation')}")
print(f"  pending_order: {r2.get('pending_order')}")
