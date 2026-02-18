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

# Try to get the Data Agent definition
print('Getting Data Agent definition...')
resp = requests.post(f'https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}/dataagents/{artifact_id}/getDefinition', headers=headers)
print(f'Status: {resp.status_code}')
print(f'Response: {resp.text[:2000]}')

# Try the items endpoint with getDefinition
print('\n\nTrying items/getDefinition...')
resp2 = requests.post(f'https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}/items/{artifact_id}/getDefinition', headers=headers)
print(f'Status: {resp2.status_code}')
print(f'Response: {resp2.text[:2000]}')
