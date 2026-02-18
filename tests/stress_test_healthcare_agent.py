"""
Comprehensive Stress Test for Healthcare Agent with Synthea Data
Tests all quick questions and various complex queries against the Fabric Data Agent
"""

import os
import sys
import time
import json
from datetime import datetime
from pathlib import Path

# Add parent directory to path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
import requests
from msal import ConfidentialClientApplication

# Load environment variables from src directory
env_path = Path(__file__).parent.parent / "src" / ".env"
if env_path.exists():
    load_dotenv(env_path)
    print(f"✅ Loaded environment from: {env_path}")
else:
    # Try loading from current directory
    load_dotenv()
    print("⚠️ Using default .env location")

# Fabric configuration
FABRIC_API_BASE = os.getenv("FABRIC_API_BASE")
FABRIC_WORKSPACE_ID = os.getenv("FABRIC_WORKSPACE_ID")
FABRIC_ARTIFACT_ID = os.getenv("FABRIC_ARTIFACT_ID")
FABRIC_TENANT_ID = os.getenv("FABRIC_TENANT_ID")
FABRIC_CLIENT_ID = os.getenv("FABRIC_CLIENT_ID")
FABRIC_CLIENT_SECRET = os.getenv("FABRIC_CLIENT_SECRET")

# Test categories
TEST_CATEGORIES = {
    "schema_discovery": [
        "What tables are available in the database?",
        "Show me the schema of the patients table",
        "List all columns in the conditions table",
        "What are the data types for columns in the medications table?",
    ],
    "patient_queries": [
        "How many patients are in the database?",
        "What is the gender distribution of patients?",
        "What are the most common races among patients?",
        "Show me the age distribution of patients",
        "What is the average healthcare expense per patient?",
    ],
    "condition_queries": [
        "What are the top 10 most common conditions?",
        "How many unique conditions are there?",
        "Show me conditions by category",
        "What conditions have the longest average duration?",
    ],
    "medication_queries": [
        "What are the most prescribed medications?",
        "What is the total cost of all medications?",
        "Show me the average medication cost by type",
        "Which medications have the highest base cost?",
        "What is the average number of dispenses per medication?",
    ],
    "encounter_queries": [
        "How many encounters are in the database?",
        "What is the breakdown of encounters by type?",
        "What is the average encounter cost?",
        "Show me encounters by month",
        "Which organizations have the most encounters?",
    ],
    "complex_joins": [
        "What are the most common conditions for patients over 65?",
        "Show me medication costs grouped by patient gender",
        "What is the average healthcare expense by race?",
        "Which providers have treated the most patients?",
        "What are the most common allergies by age group?",
    ],
    "aggregate_analytics": [
        "What is the total healthcare spending in the database?",
        "Show me monthly trends in patient admissions",
        "Calculate the average cost per encounter type",
        "What percentage of patients have died?",
        "Show me the top 5 organizations by total claims",
    ],
    "quick_questions": [
        "Show me all available tables and their row counts",
        "Show the top 10 most common conditions with patient counts",
        "What are the top 10 most expensive medications by total cost?",
        "Show breakdown of encounter types with average costs",
        "Show patient demographics summary including counts by gender, race, and average age",
        "What are the top 10 most common allergies in the database?",
        "List all organizations with their patient counts",
        "Show provider statistics including specialty distribution",
        "Show immunization rates by vaccine type",
        "What is the total healthcare spending across all patients?",
        "Show all active care plans with their conditions",
        "Show vital sign observations (body weight, blood pressure, heart rate) statistics",
    ],
}


def get_fabric_token():
    """Get authentication token using MSAL."""
    authority = f"https://login.microsoftonline.com/{FABRIC_TENANT_ID}"
    
    app = ConfidentialClientApplication(
        FABRIC_CLIENT_ID,
        authority=authority,
        client_credential=FABRIC_CLIENT_SECRET
    )
    
    scopes = ["https://api.fabric.microsoft.com/.default"]
    result = app.acquire_token_for_client(scopes=scopes)
    
    if "access_token" in result:
        return result["access_token"]
    else:
        raise Exception(f"Token acquisition failed: {result.get('error_description', result)}")


def call_fabric_agent(user_message, max_retries=3):
    """Call the Fabric Data Agent API with retry logic."""
    
    for attempt in range(max_retries):
        try:
            token = get_fabric_token()
            base_url = FABRIC_API_BASE
            api_version = "2024-07-01-preview"
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            
            # Step 1: Create an assistant
            assistant_resp = requests.post(
                f"{base_url}/assistants?api-version={api_version}",
                headers=headers,
                json={"model": "not used"},
                timeout=60
            )
            
            # Check for Capacity Not Active error
            if assistant_resp.status_code == 404:
                resp_json = assistant_resp.json() if assistant_resp.text else {}
                if resp_json.get("errorCode") == "CapacityNotActive":
                    return {
                        "success": False,
                        "error": "CapacityNotActive",
                        "message": "Fabric capacity is paused"
                    }
            
            assistant_resp.raise_for_status()
            assistant = assistant_resp.json()
            assistant_id = assistant.get("id")
            
            # Step 2: Create a thread
            thread_resp = requests.post(
                f"{base_url}/threads?api-version={api_version}",
                headers=headers,
                json={},
                timeout=30
            )
            thread_resp.raise_for_status()
            thread = thread_resp.json()
            thread_id = thread.get("id")
            
            # Step 3: Add message to thread
            msg_resp = requests.post(
                f"{base_url}/threads/{thread_id}/messages?api-version={api_version}",
                headers=headers,
                json={"role": "user", "content": user_message},
                timeout=30
            )
            msg_resp.raise_for_status()
            
            # Step 4: Create a run
            run_resp = requests.post(
                f"{base_url}/threads/{thread_id}/runs?api-version={api_version}",
                headers=headers,
                json={"assistant_id": assistant_id},
                timeout=30
            )
            run_resp.raise_for_status()
            run = run_resp.json()
            run_id = run.get("id")
            run_status = run.get("status")
            
            # Step 5: Poll for completion
            max_wait = 120  # 2 minutes max
            poll_interval = 2
            start_time = time.time()
            
            while run_status in ['queued', 'in_progress']:
                if time.time() - start_time > max_wait:
                    return {
                        "success": False,
                        "error": "Timeout",
                        "message": "Request timed out"
                    }
                time.sleep(poll_interval)
                
                status_resp = requests.get(
                    f"{base_url}/threads/{thread_id}/runs/{run_id}?api-version={api_version}",
                    headers=headers,
                    timeout=30
                )
                status_resp.raise_for_status()
                run = status_resp.json()
                run_status = run.get("status")
            
            if run_status == 'completed':
                # Get messages
                msgs_resp = requests.get(
                    f"{base_url}/threads/{thread_id}/messages?api-version={api_version}&order=asc",
                    headers=headers,
                    timeout=30
                )
                msgs_resp.raise_for_status()
                messages = msgs_resp.json()
                
                # Find assistant's response
                assistant_response = ""
                for msg in messages.get("data", []):
                    if msg.get("role") == "assistant":
                        for content in msg.get("content", []):
                            if content.get("type") == "text":
                                assistant_response = content.get("text", {}).get("value", "")
                
                # Cleanup
                try:
                    requests.delete(
                        f"{base_url}/threads/{thread_id}?api-version={api_version}",
                        headers=headers,
                        timeout=10
                    )
                except:
                    pass
                
                elapsed = time.time() - start_time
                return {
                    "success": True,
                    "response": assistant_response,
                    "elapsed_time": elapsed,
                    "thread_id": thread_id
                }
            else:
                last_error = run.get("last_error", {})
                return {
                    "success": False,
                    "error": last_error.get("code", "unknown"),
                    "message": last_error.get("message", str(last_error)),
                    "run_status": run_status
                }
                
        except requests.exceptions.HTTPError as e:
            if e.response and e.response.status_code >= 500 and attempt < max_retries - 1:
                time.sleep((2 ** attempt) * 2)
                continue
            return {
                "success": False,
                "error": f"HTTP {e.response.status_code if e.response else 'unknown'}",
                "message": e.response.text[:200] if e.response else str(e)
            }
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep((2 ** attempt) * 2)
                continue
            return {
                "success": False,
                "error": "Exception",
                "message": str(e)
            }
    
    return {"success": False, "error": "MaxRetries", "message": "Failed after max retries"}


def run_stress_test(categories=None, delay_between_queries=2):
    """Run the stress test across specified categories."""
    
    print("=" * 80)
    print("HEALTHCARE AGENT STRESS TEST")
    print(f"Started: {datetime.now().isoformat()}")
    print("=" * 80)
    
    # Verify configuration
    print("\nConfiguration Check:")
    print(f"  API Base: {FABRIC_API_BASE}")
    print(f"  Workspace ID: {FABRIC_WORKSPACE_ID}")
    print(f"  Artifact ID: {FABRIC_ARTIFACT_ID}")
    print(f"  Tenant ID: {FABRIC_TENANT_ID}")
    print(f"  Client ID: {FABRIC_CLIENT_ID[:8]}..." if FABRIC_CLIENT_ID else "  Client ID: NOT SET")
    
    if not all([FABRIC_API_BASE, FABRIC_WORKSPACE_ID, FABRIC_ARTIFACT_ID, FABRIC_TENANT_ID, FABRIC_CLIENT_ID, FABRIC_CLIENT_SECRET]):
        print("\n❌ ERROR: Missing required environment variables!")
        return
    
    # Select categories to test
    if categories is None:
        categories = list(TEST_CATEGORIES.keys())
    
    results = {
        "total_tests": 0,
        "successful": 0,
        "failed": 0,
        "capacity_errors": 0,
        "timeouts": 0,
        "details": []
    }
    
    print(f"\n🧪 Running tests for categories: {', '.join(categories)}")
    print("-" * 80)
    
    for category in categories:
        if category not in TEST_CATEGORIES:
            print(f"⚠️ Unknown category: {category}")
            continue
            
        queries = TEST_CATEGORIES[category]
        print(f"\n📁 Category: {category.upper()} ({len(queries)} queries)")
        print("-" * 40)
        
        for i, query in enumerate(queries, 1):
            results["total_tests"] += 1
            print(f"\n  [{i}/{len(queries)}] Testing: {query[:60]}...")
            
            start = time.time()
            result = call_fabric_agent(query)
            elapsed = time.time() - start
            
            test_result = {
                "category": category,
                "query": query,
                "elapsed": elapsed,
                "result": result
            }
            results["details"].append(test_result)
            
            if result["success"]:
                results["successful"] += 1
                response_preview = result["response"][:100].replace("\n", " ") if result["response"] else "Empty"
                print(f"  ✅ SUCCESS ({elapsed:.1f}s): {response_preview}...")
            else:
                results["failed"] += 1
                error_type = result.get("error", "unknown")
                
                if error_type == "CapacityNotActive":
                    results["capacity_errors"] += 1
                    print(f"  ⚠️ CAPACITY NOT ACTIVE - Fabric is paused")
                    # If capacity is not active, stop testing
                    print("\n🛑 Stopping test - Fabric capacity needs to be resumed")
                    break
                elif error_type == "Timeout":
                    results["timeouts"] += 1
                    print(f"  ⏱️ TIMEOUT ({elapsed:.1f}s)")
                else:
                    print(f"  ❌ FAILED ({elapsed:.1f}s): {error_type} - {result.get('message', '')[:100]}")
            
            # Delay between queries to avoid rate limiting
            if i < len(queries):
                time.sleep(delay_between_queries)
        
        # Check if we hit capacity error
        if results["capacity_errors"] > 0:
            break
    
    # Print summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Total Tests: {results['total_tests']}")
    print(f"✅ Successful: {results['successful']} ({results['successful']/max(results['total_tests'],1)*100:.1f}%)")
    print(f"❌ Failed: {results['failed']}")
    print(f"⚠️ Capacity Errors: {results['capacity_errors']}")
    print(f"⏱️ Timeouts: {results['timeouts']}")
    
    if results["successful"] > 0:
        successful_times = [r["elapsed"] for r in results["details"] if r["result"]["success"]]
        print(f"\nResponse Times:")
        print(f"  Average: {sum(successful_times)/len(successful_times):.1f}s")
        print(f"  Min: {min(successful_times):.1f}s")
        print(f"  Max: {max(successful_times):.1f}s")
    
    # Save results to file
    results_file = f"stress_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\n📄 Detailed results saved to: {results_file}")
    
    return results


def quick_connectivity_test():
    """Run a quick test to verify connectivity."""
    print("\n🔌 Quick Connectivity Test")
    print("-" * 40)
    
    result = call_fabric_agent("What tables are available?")
    
    if result["success"]:
        print("✅ Connection successful!")
        print(f"Response preview: {result['response'][:200]}...")
        return True
    else:
        print(f"❌ Connection failed: {result.get('error')} - {result.get('message')}")
        if result.get("error") == "CapacityNotActive":
            print("\n💡 To resume Fabric capacity:")
            print("   1. Go to https://app.fabric.microsoft.com/admin-portal")
            print("   2. Navigate to Capacity settings")
            print("   3. Find your capacity and click 'Resume'")
        return False


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Stress test the Healthcare Agent")
    parser.add_argument("--quick", action="store_true", help="Run quick connectivity test only")
    parser.add_argument("--category", type=str, help="Test specific category only")
    parser.add_argument("--all", action="store_true", help="Run all tests")
    parser.add_argument("--delay", type=int, default=2, help="Delay between queries (seconds)")
    
    args = parser.parse_args()
    
    if args.quick:
        quick_connectivity_test()
    elif args.category:
        run_stress_test(categories=[args.category], delay_between_queries=args.delay)
    elif args.all:
        run_stress_test(delay_between_queries=args.delay)
    else:
        # Default: run quick test first, then quick_questions category
        if quick_connectivity_test():
            print("\n" + "=" * 80)
            run_stress_test(categories=["quick_questions"], delay_between_queries=args.delay)
