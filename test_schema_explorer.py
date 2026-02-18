"""Explore the Synthea database schema through Fabric Data Agent."""
import os
import requests
import time
import msal
import json

# Config
FABRIC_WORKSPACE_ID = '4dabd120-bae2-445d-8f6e-5dcd242ebe79'
FABRIC_ARTIFACT_ID = '6ea26d3a-d8dc-49be-8510-63e96bb044db'
FABRIC_CLIENT_ID = '052db582-8e48-4fda-8b74-c388517bf5a6'
FABRIC_CLIENT_SECRET = os.environ.get('FABRIC_CLIENT_SECRET', '<YOUR_CLIENT_SECRET>')
FABRIC_TENANT_ID = '2c6fe00a-9400-47ba-9aff-58ef68cf07f7'

base_url = f'https://api.fabric.microsoft.com/v1/workspaces/{FABRIC_WORKSPACE_ID}/dataagents/{FABRIC_ARTIFACT_ID}/aiassistant/openai'
api_version = '2024-07-01-preview'

def get_token():
    authority = f'https://login.microsoftonline.com/{FABRIC_TENANT_ID}'
    app = msal.ConfidentialClientApplication(
        FABRIC_CLIENT_ID,
        authority=authority,
        client_credential=FABRIC_CLIENT_SECRET
    )
    result = app.acquire_token_for_client(scopes=['https://api.fabric.microsoft.com/.default'])
    if 'access_token' not in result:
        raise Exception(f"Token acquisition failed: {result.get('error_description')}")
    return result['access_token']

def query_agent(question, token):
    """Send a question to the Fabric Data Agent and get the response."""
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    
    # Step 1: Create assistant
    assistant_resp = requests.post(
        f'{base_url}/assistants?api-version={api_version}',
        headers=headers,
        json={'model': 'not used'},
        timeout=30
    )
    if assistant_resp.status_code != 200:
        print(f"Assistant creation failed: {assistant_resp.status_code} - {assistant_resp.text}")
        return None
    assistant = assistant_resp.json()
    assistant_id = assistant.get('id')
    
    # Step 2: Create thread
    thread_resp = requests.post(
        f'{base_url}/threads?api-version={api_version}',
        headers=headers,
        json={},
        timeout=30
    )
    thread = thread_resp.json()
    thread_id = thread.get('id')
    
    # Step 3: Add message
    msg_resp = requests.post(
        f'{base_url}/threads/{thread_id}/messages?api-version={api_version}',
        headers=headers,
        json={'role': 'user', 'content': question},
        timeout=30
    )
    
    # Step 4: Create run
    run_resp = requests.post(
        f'{base_url}/threads/{thread_id}/runs?api-version={api_version}',
        headers=headers,
        json={'assistant_id': assistant_id},
        timeout=30
    )
    run = run_resp.json()
    run_id = run.get('id')
    run_status = run.get('status')
    
    # Step 5: Poll for completion
    max_wait = 180
    start_time = time.time()
    while run_status in ['queued', 'in_progress']:
        if time.time() - start_time > max_wait:
            return "TIMEOUT"
        time.sleep(3)
        status_resp = requests.get(
            f'{base_url}/threads/{thread_id}/runs/{run_id}?api-version={api_version}',
            headers=headers,
            timeout=30
        )
        run = status_resp.json()
        run_status = run.get('status')
        print(f"   Status: {run_status}")
    
    if run_status == 'completed':
        # Get messages
        msgs_resp = requests.get(
            f'{base_url}/threads/{thread_id}/messages?api-version={api_version}&order=asc',
            headers=headers,
            timeout=30
        )
        messages = msgs_resp.json()
        
        for msg in messages.get('data', []):
            if msg.get('role') == 'assistant':
                for content in msg.get('content', []):
                    if content.get('type') == 'text':
                        return content.get('text', {}).get('value', '')
    elif run_status == 'failed':
        return f"FAILED: {run.get('last_error')}"
    
    return None

def main():
    print("=" * 60)
    print("SYNTHEA DATABASE SCHEMA EXPLORER")
    print("=" * 60)
    
    token = get_token()
    print("Token acquired!\n")
    
    # List of schema exploration queries
    queries = [
        ("Table List", "List all tables available in the database. Just give me the table names."),
        ("Record Counts", "For each table in the database, tell me the exact row count. Format as: table_name: count"),
        ("Patients Schema", "What columns are in the patients table? List column names and their data types."),
        ("Conditions Schema", "What columns are in the conditions table? List column names."),
        ("Medications Schema", "What columns are in the medications table? List column names."),
        ("Encounters Schema", "What columns are in the encounters table? List column names."),
        ("Sample Patient", "Show me 1 sample row from the patients table with all columns."),
    ]
    
    results = {}
    
    for name, query in queries:
        print(f"\n{'='*60}")
        print(f"QUERY: {name}")
        print(f"{'='*60}")
        print(f"Question: {query}")
        print("-" * 40)
        
        try:
            result = query_agent(query, token)
            results[name] = result
            print(f"\nRESULT:\n{result}")
        except Exception as e:
            print(f"ERROR: {e}")
            results[name] = f"ERROR: {e}"
    
    # Save results
    with open('schema_exploration_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    print("\n\nResults saved to schema_exploration_results.json")

if __name__ == "__main__":
    main()
