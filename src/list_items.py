import msal
from dotenv import load_dotenv
import os
import requests

load_dotenv()

client_id = os.getenv('FABRIC_CLIENT_ID')
client_secret = os.getenv('FABRIC_CLIENT_SECRET')
tenant_id = os.getenv('FABRIC_TENANT_ID')
workspace_id = os.getenv('FABRIC_WORKSPACE_ID')
artifact_id = os.getenv('FABRIC_ARTIFACT_ID')

authority = f'https://login.microsoftonline.com/{tenant_id}'
app = msal.ConfidentialClientApplication(client_id, authority=authority, client_credential=client_secret)
result = app.acquire_token_for_client(scopes=['https://api.fabric.microsoft.com/.default'])
token = result['access_token']
headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}

# List all items in workspace to see what types are available
print('Listing workspace items...')
resp = requests.get(f'https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}/items', headers=headers)
if resp.status_code == 200:
    items = resp.json().get('value', [])
    print(f'Found {len(items)} items:')
    for item in items:
        print(f"  - {item.get('type')}: {item.get('displayName')} ({item.get('id')})")
else:
    print(f'Error: {resp.status_code} - {resp.text}')
