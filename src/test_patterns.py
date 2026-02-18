import msal
from dotenv import load_dotenv
import os
import requests
import time

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

print('=== Testing Data Agent Query Patterns ===\n')

# Pattern 1: Try /jobs endpoint (long-running operation pattern)
print('1. Testing /jobs endpoint (POST)...')
job_body = {
    "executionData": {
        "query": "How many patients are in the database?"
    }
}
resp = requests.post(
    f'https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}/dataagents/{artifact_id}/jobs/instances?jobType=Query',
    headers=headers,
    json=job_body
)
print(f'   Status: {resp.status_code}')
print(f'   Response: {resp.text[:500]}')

# Pattern 2: Try executeQueries
print('\n2. Testing /executeQueries endpoint...')
query_body = {
    "queries": [
        {"query": "How many patients are in the database?"}
    ]
}
resp2 = requests.post(
    f'https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}/dataagents/{artifact_id}/executeQueries',
    headers=headers,
    json=query_body
)
print(f'   Status: {resp2.status_code}')
print(f'   Response: {resp2.text[:500]}')

# Pattern 3: Try Semantic Model query (the Data Agent might be backed by a semantic model)
print('\n3. Looking for connected Semantic Models...')
# Get HLS Synthea semantic model
semantic_model_id = 'd9c2a413-1f5b-4e3c-8641-cf8df167e867'  # HLS Synthea- DirectLake Model
dax_query = {
    "queries": [
        {"query": "EVALUATE ROW(\"PatientCount\", COUNTROWS(patients))"}
    ]
}
resp3 = requests.post(
    f'https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}/semanticModels/{semantic_model_id}/executeQueries',
    headers=headers,
    json=dax_query
)
print(f'   Semantic Model Query Status: {resp3.status_code}')
print(f'   Response: {resp3.text[:500]}')

# Pattern 4: Check if there's a /publish endpoint
print('\n4. Testing various other endpoints...')
endpoints = [
    ('GET', f'https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}/dataagents/{artifact_id}/status'),
    ('POST', f'https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}/dataagents/{artifact_id}/publish'),
    ('GET', f'https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}/dataagents/{artifact_id}/datasources'),
]

for method, url in endpoints:
    try:
        if method == 'GET':
            r = requests.get(url, headers=headers, timeout=10)
        else:
            r = requests.post(url, headers=headers, json={}, timeout=10)
        print(f'   {method} ...{url[-50:]}: {r.status_code}')
        if r.status_code < 400:
            print(f'      Response: {r.text[:200]}')
    except Exception as e:
        print(f'   {method} ...{url[-50:]}: Error - {e}')
