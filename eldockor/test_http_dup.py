import json, urllib.request

# Login
req = urllib.request.Request(
    "http://localhost:8000/auth/login",
    data=json.dumps({"email": "salma@eldoctor.com", "password": "demo1234"}).encode("utf-8"),
    headers={"Content-Type": "application/json"},
)
resp = urllib.request.urlopen(req)
token = json.loads(resp.read().decode("utf-8"))["token"]

# Step 1: Create pending order
req = urllib.request.Request(
    "http://localhost:8000/agents/message",
    data=json.dumps({"message": "عايز 10 من PROD-003", "conversation_id": "http-dup-1"}).encode("utf-8"),
    headers={"Content-Type": "application/json; charset=utf-8", "Authorization": f"Bearer {token}"},
)
resp = urllib.request.urlopen(req)
r1 = json.loads(resp.read().decode("utf-8"))
print(f"Step 1 - proposal: requires_confirmation={r1.get('requires_confirmation')}")

# Step 2: Confirm
req = urllib.request.Request(
    "http://localhost:8000/agents/message",
    data=json.dumps({"message": "أيوه", "conversation_id": "http-dup-1"}).encode("utf-8"),
    headers={"Content-Type": "application/json; charset=utf-8", "Authorization": f"Bearer {token}"},
)
resp = urllib.request.urlopen(req)
r2 = json.loads(resp.read().decode("utf-8"))
print(f"Step 2 - confirmation: order_id={r2.get('order_id')}, requires_confirmation={r2.get('requires_confirmation')}")

# Step 3: Duplicate confirmation
req = urllib.request.Request(
    "http://localhost:8000/agents/message",
    data=json.dumps({"message": "أيوه", "conversation_id": "http-dup-1"}).encode("utf-8"),
    headers={"Content-Type": "application/json; charset=utf-8", "Authorization": f"Bearer {token}"},
)
resp = urllib.request.urlopen(req)
r3 = json.loads(resp.read().decode("utf-8"))
print(f"Step 3 - duplicate: order_id={r3.get('order_id')}, requires_confirmation={r3.get('requires_confirmation')}")

# Check orders count
req = urllib.request.Request(
    "http://localhost:8000/agents/message",
    data=json.dumps({"message": "ايه الطلبات", "conversation_id": "http-dup-1"}).encode("utf-8"),
    headers={"Content-Type": "application/json; charset=utf-8", "Authorization": f"Bearer {token}"},
)
resp = urllib.request.urlopen(req)
r4 = json.loads(resp.read().decode("utf-8"))
print(f"Step 4 - orders: {r4.get('reply', '')[:200]}")
