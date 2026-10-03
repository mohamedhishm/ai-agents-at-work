import json, urllib.request

# Login as customer 1
req = urllib.request.Request(
    "http://localhost:8000/auth/login",
    data=json.dumps({"email": "salma@eldoctor.com", "password": "demo1234"}).encode("utf-8"),
    headers={"Content-Type": "application/json"},
)
resp = urllib.request.urlopen(req)
token1 = json.loads(resp.read().decode("utf-8"))["token"]

# Customer 1 creates pending order
req = urllib.request.Request(
    "http://localhost:8000/agents/message",
    data=json.dumps({"message": "عايز 10 من PROD-003", "conversation_id": "iso-test-1"}).encode("utf-8"),
    headers={"Content-Type": "application/json; charset=utf-8", "Authorization": f"Bearer {token1}"},
)
resp = urllib.request.urlopen(req)
r1 = json.loads(resp.read().decode("utf-8"))
print(f"Customer 1 - proposal: requires_confirmation={r1.get('requires_confirmation')}")

# Login as customer 2
req = urllib.request.Request(
    "http://localhost:8000/auth/login",
    data=json.dumps({"email": "salma@eldoctor.com", "password": "demo1234"}).encode("utf-8"),
    headers={"Content-Type": "application/json"},
)
resp = urllib.request.urlopen(req)
token2 = json.loads(resp.read().decode("utf-8"))["token"]

# Customer 2 tries to confirm customer 1's order
req = urllib.request.Request(
    "http://localhost:8000/agents/message",
    data=json.dumps({"message": "أيوه", "conversation_id": "iso-test-1"}).encode("utf-8"),
    headers={"Content-Type": "application/json; charset=utf-8", "Authorization": f"Bearer {token2}"},
)
resp = urllib.request.urlopen(req)
r2 = json.loads(resp.read().decode("utf-8"))
print(f"Customer 2 - confirmation: reply={r2.get('reply', '')[:60]}")
print(f"Customer 2 - requires_confirmation={r2.get('requires_confirmation')}")

# Customer 1 confirms their own order
req = urllib.request.Request(
    "http://localhost:8000/agents/message",
    data=json.dumps({"message": "أيوه", "conversation_id": "iso-test-1"}).encode("utf-8"),
    headers={"Content-Type": "application/json; charset=utf-8", "Authorization": f"Bearer {token1}"},
)
resp = urllib.request.urlopen(req)
r3 = json.loads(resp.read().decode("utf-8"))
print(f"Customer 1 - confirmation: order_id={r3.get('order_id')}, requires_confirmation={r3.get('requires_confirmation')}")
