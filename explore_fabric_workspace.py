"""Explore Synthea data directly from Fabric Lakehouse/Warehouse."""
import os
import requests
import msal
import json

# Config
FABRIC_WORKSPACE_ID = '4dabd120-bae2-445d-8f6e-5dcd242ebe79'
FABRIC_CLIENT_ID = '052db582-8e48-4fda-8b74-c388517bf5a6'
FABRIC_CLIENT_SECRET = os.environ.get('FABRIC_CLIENT_SECRET', '<YOUR_CLIENT_SECRET>')
FABRIC_TENANT_ID = '2c6fe00a-9400-47ba-9aff-58ef68cf07f7'

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

def main():
    token = get_token()
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    
    print("=" * 60)
    print("FABRIC WORKSPACE ITEMS EXPLORER")
    print("=" * 60)
    
    # List all items in workspace
    print("\n1. Listing all workspace items...")
    resp = requests.get(
        f'https://api.fabric.microsoft.com/v1/workspaces/{FABRIC_WORKSPACE_ID}/items',
        headers=headers
    )
    
    if resp.status_code == 200:
        items = resp.json().get('value', [])
        print(f"\nFound {len(items)} items:")
        
        # Group by type
        by_type = {}
        for item in items:
            item_type = item.get('type')
            if item_type not in by_type:
                by_type[item_type] = []
            by_type[item_type].append(item)
        
        for item_type, type_items in sorted(by_type.items()):
            print(f"\n  {item_type} ({len(type_items)}):")
            for item in type_items:
                print(f"    - {item.get('displayName')} (ID: {item.get('id')})")
        
        # Find lakehouses
        lakehouses = [i for i in items if i.get('type') == 'Lakehouse']
        
        print("\n" + "=" * 60)
        print("2. Exploring Lakehouses...")
        print("=" * 60)
        
        for lh in lakehouses:
            lh_id = lh.get('id')
            lh_name = lh.get('displayName')
            print(f"\n  Lakehouse: {lh_name}")
            
            # Get lakehouse tables
            tables_resp = requests.get(
                f'https://api.fabric.microsoft.com/v1/workspaces/{FABRIC_WORKSPACE_ID}/lakehouses/{lh_id}/tables',
                headers=headers
            )
            
            if tables_resp.status_code == 200:
                tables = tables_resp.json().get('value', [])
                print(f"    Tables ({len(tables)}):")
                for table in tables:
                    print(f"      - {table.get('name')} (format: {table.get('format')}, rows: {table.get('rowCount', 'N/A')})")
            else:
                print(f"    Error getting tables: {tables_resp.status_code} - {tables_resp.text[:200]}")
        
        # Find SQL Endpoints
        sql_endpoints = [i for i in items if i.get('type') == 'SQLEndpoint']
        
        print("\n" + "=" * 60)
        print("3. SQL Endpoints...")
        print("=" * 60)
        
        for ep in sql_endpoints:
            print(f"  - {ep.get('displayName')} (ID: {ep.get('id')})")
        
        # Find Warehouses
        warehouses = [i for i in items if i.get('type') == 'Warehouse']
        
        print("\n" + "=" * 60)
        print("4. Warehouses...")
        print("=" * 60)
        
        for wh in warehouses:
            print(f"  - {wh.get('displayName')} (ID: {wh.get('id')})")
        
        # Find Data Agents
        data_agents = [i for i in items if i.get('type') == 'DataAgent']
        
        print("\n" + "=" * 60)
        print("5. Data Agents...")
        print("=" * 60)
        
        for da in data_agents:
            da_id = da.get('id')
            da_name = da.get('displayName')
            print(f"  - {da_name} (ID: {da_id})")
            
            # Get Data Agent details
            da_resp = requests.get(
                f'https://api.fabric.microsoft.com/v1/workspaces/{FABRIC_WORKSPACE_ID}/dataagents/{da_id}',
                headers=headers
            )
            if da_resp.status_code == 200:
                da_details = da_resp.json()
                print(f"    Description: {da_details.get('description', 'N/A')}")
            
        # Save full item list
        with open('fabric_workspace_items.json', 'w') as f:
            json.dump(items, f, indent=2)
        print("\n\nFull item list saved to fabric_workspace_items.json")
        
    else:
        print(f"Error: {resp.status_code} - {resp.text}")

if __name__ == "__main__":
    main()
