import sys, os
sys.path.insert(0, r'C:\Users\msi\OneDrive - Arab Academy for Science and Technology\Documents\AI Engineer\ai agents at work\ai-agents-at-work')

from eldockor.graph import invoke_agent, clear_conversation

clear_conversation('debug-confirm-1')

# Step 1: Create pending order
r1 = invoke_agent(message='عايز 10 من PROD-003', user_id='CUST-001', user_role='customer', conversation_id='debug-confirm-1')
print(f'Step 1: requires_confirmation={r1.get("requires_confirmation")}, pending_order={r1.get("pending_order") is not None}')

# Step 2: Confirm
r2 = invoke_agent(message='أيوه', user_id='CUST-001', user_role='customer', conversation_id='debug-confirm-1')
print(f'Step 2: reply={r2.get("reply","")[:60]}')
print(f'Step 2: action_executed={r2.get("action_executed")}, order_id={r2.get("order_id")}')
print(f'Step 2: requires_confirmation={r2.get("requires_confirmation")}, pending_order={r2.get("pending_order")}')
