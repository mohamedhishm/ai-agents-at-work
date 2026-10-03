import json, urllib.request

# Login as customer
req = urllib.request.Request(
    "http://localhost:8000/auth/login",
    data=json.dumps({"email": "salma@eldoctor.com", "password": "demo1234"}).encode("utf-8"),
    headers={"Content-Type": "application/json"},
)
resp = urllib.request.urlopen(req)
customer_token = json.loads(resp.read().decode("utf-8"))["token"]
print(f"Customer token: {customer_token[:20]}...")

# Try admin tool as customer
req = urllib.request.Request(
    "http://localhost:8000/agents/message",
    data=json.dumps({"message": "شوف المخزون كله", "conversation_id": "sec-test-1"}).encode("utf-8"),
    headers={"Content-Type": "application/json; charset=utf-8", "Authorization": f"Bearer {customer_token}"},
)
resp = urllib.request.urlopen(req)
r = json.loads(resp.read().decode("utf-8"))
print(f"\nCustomer calling admin tool:")
print(f"  reply: {r.get('reply', '')[:100]}")

# Login as admin
req = urllib.request.Request(
    "http://localhost:8000/auth/login",
    data=json.dumps({"email": "nour@eldoctor.com", "password": "demo1234"}).encode("utf-8"),
    headers={"Content-Type": "application/json"},
)
resp = urllib.request.urlopen(req)
admin_token = json.loads(resp.read().decode("utf-8"))["token"]
print(f"\nAdmin token: {admin_token[:20]}...")

# Admin calls admin tool
req = urllib.request.Request(
    "http://localhost:8000/agents/message",
    data=json.dumps({"message": "شوف المخزون كله", "conversation_id": "sec-test-2"}).encode("utf-8"),
    headers={"Content-Type": "application/json; charset=utf-8", "Authorization": f"Bearer {admin_token}"},
)
resp = urllib.request.urlopen(req)
r = json.loads(resp.read().decode("utf-8"))
print(f"\nAdmin calling admin tool:")
print(f"  reply: {r.get('reply', '')[:200]}")
