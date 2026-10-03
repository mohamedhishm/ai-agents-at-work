import sys, os, json
sys.path.insert(0, r'C:\Users\msi\OneDrive - Arab Academy for Science and Technology\Documents\AI Engineer\ai agents at work\ai-agents-at-work')

from eldockor.graph import invoke_agent, clear_conversation, _conversation_store

clear_conversation('http-debug-1')

# Step 1: Create pending order
print("=== Step 1: Create pending order ===")
r1 = invoke_agent(message='عايز 10 من PROD-002', user_id='CUST-001', user_role='customer', conversation_id='http-debug-1')
print(f"requires_confirmation: {r1.get('requires_confirmation')}")
print(f"pending_order: {r1.get('pending_order')}")
print(f"pending_action in conv_store: {_conversation_store.get('http-debug-1', {}).get('pending_action')}")
print(f"pending_order in conv_store: {_conversation_store.get('http-debug-1', {}).get('pending_order')}")
print()

# Step 2: Confirm
print("=== Step 2: Confirm ===")
r2 = invoke_agent(message='أيوه', user_id='CUST-001', user_role='customer', conversation_id='http-debug-1')
print(f"reply: {r2.get('reply', '')[:100]}")
print(f"action_executed: {r2.get('action_executed')}")
print(f"requires_confirmation: {r2.get('requires_confirmation')}")
print(f"pending_order: {r2.get('pending_order')}")
print(f"pending_action in conv_store: {_conversation_store.get('http-debug-1', {}).get('pending_action')}")
print(f"pending_order in conv_store: {_conversation_store.get('http-debug-1', {}).get('pending_order')}")
