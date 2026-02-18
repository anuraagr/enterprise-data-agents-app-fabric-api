"""
Simple sequential test for all quick questions.
Runs each query one at a time to avoid interruptions.
"""

import os
import time
import json
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
import requests
from msal import ConfidentialClientApplication

# Load environment
load_dotenv(Path(__file__).parent.parent / "src" / ".env")

FABRIC_CLIENT_ID = os.getenv('FABRIC_CLIENT_ID')
FABRIC_CLIENT_SECRET = os.getenv('FABRIC_CLIENT_SECRET')
FABRIC_TENANT_ID = os.getenv('FABRIC_TENANT_ID')
FABRIC_WORKSPACE_ID = os.getenv('FABRIC_WORKSPACE_ID')
FABRIC_ARTIFACT_ID = os.getenv('FABRIC_ARTIFACT_ID')
FABRIC_API_BASE = f'https://api.fabric.microsoft.com/v1/workspaces/{FABRIC_WORKSPACE_ID}/dataagents/{FABRIC_ARTIFACT_ID}/aiassistant/openai'
API_VERSION = '2024-07-01-preview'

# Get token once
def get_token():
    authority = f'https://login.microsoftonline.com/{FABRIC_TENANT_ID}'
    app = ConfidentialClientApplication(FABRIC_CLIENT_ID, authority=authority, client_credential=FABRIC_CLIENT_SECRET)
    result = app.acquire_token_for_client(['https://api.fabric.microsoft.com/.default'])
    return result['access_token']

TOKEN = get_token()
HEADERS = {'Authorization': f'Bearer {TOKEN}', 'Content-Type': 'application/json'}

def run_query(query, timeout_secs=120):
    """Run a single query and return result."""
    start = time.time()
    
    try:
        # Create assistant
        resp = requests.post(f'{FABRIC_API_BASE}/assistants?api-version={API_VERSION}', headers=HEADERS, json={'model': 'not used'}, timeout=60)
        resp.raise_for_status()
        assistant_id = resp.json()['id']
        
        # Create thread
        resp = requests.post(f'{FABRIC_API_BASE}/threads?api-version={API_VERSION}', headers=HEADERS, json={}, timeout=30)
        resp.raise_for_status()
        thread_id = resp.json()['id']
        
        # Add message
        resp = requests.post(f'{FABRIC_API_BASE}/threads/{thread_id}/messages?api-version={API_VERSION}', headers=HEADERS, json={'role': 'user', 'content': query}, timeout=30)
        resp.raise_for_status()
        
        # Create run
        resp = requests.post(f'{FABRIC_API_BASE}/threads/{thread_id}/runs?api-version={API_VERSION}', headers=HEADERS, json={'assistant_id': assistant_id}, timeout=30)
        resp.raise_for_status()
        run_id = resp.json()['id']
        run_status = resp.json()['status']
        
        # Poll for completion
        poll_start = time.time()
        while run_status in ['queued', 'in_progress']:
            if time.time() - poll_start > timeout_secs:
                return {'success': False, 'error': 'Timeout', 'elapsed': time.time() - start}
            time.sleep(2)
            resp = requests.get(f'{FABRIC_API_BASE}/threads/{thread_id}/runs/{run_id}?api-version={API_VERSION}', headers=HEADERS, timeout=30)
            run_status = resp.json()['status']
        
        if run_status == 'completed':
            resp = requests.get(f'{FABRIC_API_BASE}/threads/{thread_id}/messages?api-version={API_VERSION}&order=asc', headers=HEADERS, timeout=30)
            messages = resp.json()
            for msg in messages.get('data', []):
                if msg.get('role') == 'assistant':
                    for content in msg.get('content', []):
                        if content.get('type') == 'text':
                            return {
                                'success': True, 
                                'response': content.get('text', {}).get('value', ''),
                                'elapsed': time.time() - start
                            }
        else:
            error = resp.json().get('last_error', {})
            return {'success': False, 'error': f'{run_status}: {error}', 'elapsed': time.time() - start}
            
    except Exception as e:
        return {'success': False, 'error': str(e), 'elapsed': time.time() - start}
    
    return {'success': False, 'error': 'Unknown', 'elapsed': time.time() - start}

# Quick questions from the UI
QUICK_QUESTIONS = [
    ("📊 Database Overview", "Count the total records in each table: patients, conditions, medications, encounters, procedures, observations, allergies, immunizations, careplans, organizations, providers, payers. Present as a summary table."),
    ("🩺 Top 10 Conditions", "From the conditions table, find the top 10 most common conditions. Group by Description, count distinct Patient IDs, and order by count descending. Show the condition Description and patient count."),
    ("💊 Medication Costs", "From the medications table, find the top 10 most expensive medications. Group by Description, sum the TotalCost column, count the number of prescriptions, and show average Base_Cost per prescription. Order by total cost descending."),
    ("🏥 Encounter Breakdown", "From the encounters table, analyze encounter types. Group by EncounterClass, count total encounters, sum Total_Claim_Cost, and calculate average Payer_Coverage. Show percentages of total."),
    ("👥 Patient Demographics", "From the patients table: count total patients, count by Gender (M/F), calculate average age using BirthDate, show counts by Race, and count how many have DeathDate IS NOT NULL (deceased) vs IS NULL (alive)."),
    ("🤧 Common Allergies", "From the allergies table, find the top 10 most common allergies. Group by Description, count distinct Patient IDs. Also show the Category (food, medication, environment) breakdown."),
]

def main():
    print("=" * 70)
    print("QUICK QUESTIONS TEST")
    print(f"Started: {datetime.now()}")
    print("=" * 70)
    
    results = []
    for i, (label, query) in enumerate(QUICK_QUESTIONS, 1):
        print(f"\n[{i}/{len(QUICK_QUESTIONS)}] {label}")
        print(f"Query: {query[:60]}...")
        
        result = run_query(query)
        results.append({'label': label, 'query': query, **result})
        
        if result['success']:
            print(f"✅ SUCCESS ({result['elapsed']:.1f}s)")
            # Print first 300 chars of response
            preview = result['response'][:300].replace('\n', ' ')
            print(f"   Preview: {preview}...")
        else:
            print(f"❌ FAILED ({result['elapsed']:.1f}s): {result['error']}")
        
        # Wait between queries
        if i < len(QUICK_QUESTIONS):
            print("   Waiting 5s...")
            time.sleep(5)
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    successful = sum(1 for r in results if r['success'])
    print(f"Total: {len(results)}")
    print(f"Successful: {successful} ({successful/len(results)*100:.0f}%)")
    print(f"Failed: {len(results) - successful}")
    
    if successful > 0:
        times = [r['elapsed'] for r in results if r['success']]
        print(f"Avg response time: {sum(times)/len(times):.1f}s")
    
    # Save results
    with open('quick_test_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    print("\nResults saved to quick_test_results.json")

if __name__ == "__main__":
    main()
