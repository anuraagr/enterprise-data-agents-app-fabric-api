"""Test Fabric Data Agent API with the corrected flow - creating assistant first."""
import os
import requests
import time
import msal

# Config
FABRIC_WORKSPACE_ID = '4dabd120-bae2-445d-8f6e-5dcd242ebe79'
FABRIC_ARTIFACT_ID = '6ea26d3a-d8dc-49be-8510-63e96bb044db'
FABRIC_CLIENT_ID = '052db582-8e48-4fda-8b74-c388517bf5a6'
FABRIC_CLIENT_SECRET = os.environ.get('FABRIC_CLIENT_SECRET', '<YOUR_CLIENT_SECRET>')
FABRIC_TENANT_ID = '2c6fe00a-9400-47ba-9aff-58ef68cf07f7'

# Original URL (not published)
base_url = f'https://api.fabric.microsoft.com/v1/workspaces/{FABRIC_WORKSPACE_ID}/dataagents/{FABRIC_ARTIFACT_ID}/aiassistant/openai'

print('Getting token via MSAL (client credentials)...')
authority = f'https://login.microsoftonline.com/{FABRIC_TENANT_ID}'
app = msal.ConfidentialClientApplication(
    FABRIC_CLIENT_ID,
    authority=authority,
    client_credential=FABRIC_CLIENT_SECRET
)
result = app.acquire_token_for_client(scopes=['https://api.fabric.microsoft.com/.default'])

if 'access_token' not in result:
    print(f'Token acquisition FAILED!')
    print(f'Error: {result.get("error")}')
    print(f'Description: {result.get("error_description")}')
    exit(1)

token = result['access_token']
print('Token acquired!')

api_version = '2024-07-01-preview'
headers = {
    'Authorization': f'Bearer {token}',
    'Content-Type': 'application/json',
    'Accept': 'application/json'
}

# Step 1: Create assistant (KEY FIX!)
print('\n1. Creating assistant...')
assistant_resp = requests.post(
    f'{base_url}/assistants?api-version={api_version}',
    headers=headers,
    json={'model': 'not used'},
    timeout=30
)
assistant = assistant_resp.json()
assistant_id = assistant.get('id')
model = assistant.get('model')
print(f'   Assistant ID: {assistant_id}')
print(f'   Model: {model}')

# Step 2: Create thread
print('\n2. Creating thread...')
thread_resp = requests.post(
    f'{base_url}/threads?api-version={api_version}',
    headers=headers,
    json={},
    timeout=30
)
thread = thread_resp.json()
thread_id = thread.get('id')
print(f'   Thread ID: {thread_id}')

# Step 3: Add message
print('\n3. Adding message...')
msg_resp = requests.post(
    f'{base_url}/threads/{thread_id}/messages?api-version={api_version}',
    headers=headers,
    json={'role': 'user', 'content': 'How many patients are in the database?'},
    timeout=30
)
print(f'   Status: {msg_resp.status_code}')

# Step 4: Create run with proper assistant ID
print(f'\n4. Creating run with assistant_id={assistant_id}...')
run_resp = requests.post(
    f'{base_url}/threads/{thread_id}/runs?api-version={api_version}',
    headers=headers,
    json={'assistant_id': assistant_id},
    timeout=30
)
run = run_resp.json()
run_id = run.get('id')
run_status = run.get('status')
print(f'   Run ID: {run_id}')
print(f'   Initial Status: {run_status}')

# Step 5: Poll for completion
print('\n5. Polling for completion...')
max_wait = 120
start_time = time.time()
while run_status in ['queued', 'in_progress']:
    if time.time() - start_time > max_wait:
        print('   TIMEOUT!')
        break
    time.sleep(2)
    status_resp = requests.get(
        f'{base_url}/threads/{thread_id}/runs/{run_id}?api-version={api_version}',
        headers=headers,
        timeout=30
    )
    run = status_resp.json()
    run_status = run.get('status')
    print(f'   Status: {run_status}')

print(f'\nFinal run status: {run_status}')

if run_status == 'completed':
    # Get messages
    print('\n6. Getting response...')
    msgs_resp = requests.get(
        f'{base_url}/threads/{thread_id}/messages?api-version={api_version}&order=asc',
        headers=headers,
        timeout=30
    )
    messages = msgs_resp.json()
    msg_count = len(messages.get('data', []))
    print(f'   Found {msg_count} messages')
    
    for msg in messages.get('data', []):
        role = msg.get('role')
        for content in msg.get('content', []):
            if content.get('type') == 'text':
                text = content.get('text', {}).get('value', '')
                print(f'\n=== {role.upper()} ===')
                print(text)
                
elif run_status == 'failed':
    print('\nRun failed!')
    last_error = run.get('last_error')
    print(f'Error: {last_error}')
