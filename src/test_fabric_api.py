import msal
from dotenv import load_dotenv
import os
import requests
import time
from openai import OpenAI

load_dotenv()

client_id = os.getenv('FABRIC_CLIENT_ID')
client_secret = os.getenv('FABRIC_CLIENT_SECRET')
tenant_id = os.getenv('FABRIC_TENANT_ID')
workspace_id = os.getenv('FABRIC_WORKSPACE_ID')
artifact_id = os.getenv('FABRIC_ARTIFACT_ID')

print(f'Client ID: {client_id}')
print(f'Tenant ID: {tenant_id}')
print(f'Workspace ID: {workspace_id}')
print(f'Artifact ID: {artifact_id}')
print(f'Secret length: {len(client_secret) if client_secret else 0}')

# Get token using MSAL
authority = f'https://login.microsoftonline.com/{tenant_id}'
app = msal.ConfidentialClientApplication(client_id, authority=authority, client_credential=client_secret)
result = app.acquire_token_for_client(scopes=['https://api.fabric.microsoft.com/.default'])

if 'access_token' in result:
    print('\n✅ Token acquired successfully!')
    token = result['access_token']
    print(f'Token length: {len(token)}')
    
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    
    # First test: Can we access the Data Agent?
    url = f'https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}/dataagents/{artifact_id}'
    response = requests.get(url, headers=headers)
    print(f'\nData Agent GET: {response.status_code}')
    print(response.text[:500] if response.text else 'No response')
    
    if response.status_code == 200:
        print('\n--- Testing OpenAI Assistants API Pattern ---')
        
        # The Fabric Data Agent exposes an OpenAI-compatible endpoint
        fabric_openai_base = f'https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}/dataagents/{artifact_id}/openai'
        
        print(f'\nTrying OpenAI SDK with base URL: {fabric_openai_base}')
        
        try:
            # Create OpenAI client pointing to Fabric Data Agent
            client = OpenAI(
                base_url=fabric_openai_base,
                api_key=token,
                default_headers={
                    "Authorization": f"Bearer {token}"
                }
            )
            
            # Try listing assistants first
            print('\n1. Testing /assistants endpoint...')
            try:
                assistants = client.beta.assistants.list()
                print(f'   Assistants: {assistants}')
            except Exception as e:
                print(f'   Assistants error: {e}')
            
            # Try creating a thread
            print('\n2. Testing /threads endpoint...')
            try:
                thread = client.beta.threads.create()
                print(f'   Thread created: {thread.id}')
                
                # Add a message to the thread
                print('\n3. Adding message to thread...')
                message = client.beta.threads.messages.create(
                    thread_id=thread.id,
                    role="user",
                    content="How many patients are in the database?"
                )
                print(f'   Message created: {message.id}')
                
                # Create a run
                print('\n4. Creating run...')
                run = client.beta.threads.runs.create(
                    thread_id=thread.id,
                    assistant_id=artifact_id  # Use the Data Agent ID as assistant ID
                )
                print(f'   Run created: {run.id}, status: {run.status}')
                
                # Poll for completion
                print('\n5. Waiting for completion...')
                while run.status in ['queued', 'in_progress']:
                    time.sleep(2)
                    run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
                    print(f'   Status: {run.status}')
                
                if run.status == 'completed':
                    print('\n6. Retrieving messages...')
                    messages = client.beta.threads.messages.list(thread_id=thread.id)
                    for msg in messages.data:
                        if msg.role == 'assistant':
                            print(f'\n✅ ASSISTANT RESPONSE:')
                            for content in msg.content:
                                if hasattr(content, 'text'):
                                    print(content.text.value)
                else:
                    print(f'\n❌ Run ended with status: {run.status}')
                    if run.last_error:
                        print(f'   Error: {run.last_error}')
                        
            except Exception as e:
                print(f'   Thread error: {e}')
                
        except Exception as e:
            print(f'\nOpenAI SDK error: {e}')
        
        # Also try direct REST endpoints
        print('\n--- Testing Direct REST Endpoints ---')
        
        endpoints_to_test = [
            ('GET', f'{fabric_openai_base}/assistants', None),
            ('GET', f'{fabric_openai_base}/v1/assistants', None),
            ('POST', f'{fabric_openai_base}/threads', {}),
            ('POST', f'{fabric_openai_base}/v1/threads', {}),
        ]
        
        for method, endpoint, body in endpoints_to_test:
            try:
                if method == 'GET':
                    resp = requests.get(endpoint, headers=headers, timeout=30)
                else:
                    resp = requests.post(endpoint, headers=headers, json=body, timeout=30)
                print(f'\n{method} {endpoint}')
                print(f'   Status: {resp.status_code}')
                print(f'   Response: {resp.text[:200]}')
            except Exception as e:
                print(f'\n{method} {endpoint}')
                print(f'   Error: {e}')
else:
    print(f'\n❌ Token error: {result.get("error_description", result)}')
