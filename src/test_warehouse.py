import msal
from dotenv import load_dotenv
import os
import requests

load_dotenv()

client_id = os.getenv('FABRIC_CLIENT_ID')
client_secret = os.getenv('FABRIC_CLIENT_SECRET')
tenant_id = os.getenv('FABRIC_TENANT_ID')
workspace_id = os.getenv('FABRIC_WORKSPACE_ID')

authority = f'https://login.microsoftonline.com/{tenant_id}'
app = msal.ConfidentialClientApplication(client_id, authority=authority, client_credential=client_secret)
result = app.acquire_token_for_client(scopes=['https://api.fabric.microsoft.com/.default'])
token = result['access_token']
headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}

print('=== Testing SQL Endpoint Queries ===\n')

# The HLS_Synthea_Warehouse - this is likely where the patient data is
warehouse_id = '690955f3-44e7-4fcf-adb4-a6a72998e11a'

# Try to execute SQL query on warehouse
print(f'1. Testing SQL query on HLS_Synthea_Warehouse...')
sql_body = {
    "query": "SELECT COUNT(*) as patient_count FROM patients"
}
resp = requests.post(
    f'https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}/warehouses/{warehouse_id}/executeQueries',
    headers=headers,
    json=sql_body
)
print(f'   Status: {resp.status_code}')
print(f'   Response: {resp.text[:500]}')

# Try lakehouses instead
print('\n2. Checking lakehouses for patient data...')
lakehouses = [
    ('healthcare1_msft_silver', '9293b35f-4f58-43d2-910e-e697d9e6ede6'),
    ('healthcare1_msft_bronze', '72cf4131-22c6-439f-a5ac-983d655023a2'),
]

for name, lh_id in lakehouses:
    print(f'\n   Lakehouse: {name}')
    # Try to list tables
    resp = requests.get(
        f'https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}/lakehouses/{lh_id}/tables',
        headers=headers
    )
    print(f'   Tables Status: {resp.status_code}')
    if resp.status_code == 200:
        tables = resp.json().get('value', [])
        print(f'   Found {len(tables)} tables')
        for t in tables[:10]:
            print(f'      - {t.get("name")}')
