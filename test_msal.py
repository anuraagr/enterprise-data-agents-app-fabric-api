"""Test MSAL token acquisition with the client secret."""
import os
import msal

FABRIC_CLIENT_ID = '052db582-8e48-4fda-8b74-c388517bf5a6'
FABRIC_CLIENT_SECRET = os.environ.get('FABRIC_CLIENT_SECRET', '<YOUR_CLIENT_SECRET>')
FABRIC_TENANT_ID = '2c6fe00a-9400-47ba-9aff-58ef68cf07f7'

print('Testing MSAL token acquisition...')
authority = f'https://login.microsoftonline.com/{FABRIC_TENANT_ID}'
app = msal.ConfidentialClientApplication(
    FABRIC_CLIENT_ID,
    authority=authority,
    client_credential=FABRIC_CLIENT_SECRET
)

scopes = ['https://api.fabric.microsoft.com/.default']
result = app.acquire_token_for_client(scopes=scopes)

if 'access_token' in result:
    token = result['access_token']
    print(f'SUCCESS! Token acquired: {token[:50]}...')
else:
    print('FAILED!')
    print(f'Error: {result.get("error")}')
    print(f'Description: {result.get("error_description")}')
