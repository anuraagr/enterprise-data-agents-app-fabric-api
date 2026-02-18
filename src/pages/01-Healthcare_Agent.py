import os
import json
import time
import io
import requests
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI
from azure.identity import DefaultAzureCredential, ManagedIdentityCredential, AzureCliCredential, ChainedTokenCredential, ClientSecretCredential
import msal
import streamlit as st
import pandas as pd

load_dotenv()

# Fabric Data Agent Configuration — set these in your .env file (see env.example)
FABRIC_WORKSPACE_ID = os.getenv("FABRIC_WORKSPACE_ID", "")
FABRIC_ARTIFACT_ID = os.getenv("FABRIC_ARTIFACT_ID", "")

# App Registration Configuration
FABRIC_CLIENT_ID = os.getenv("FABRIC_CLIENT_ID", "")
FABRIC_CLIENT_SECRET = os.getenv("FABRIC_CLIENT_SECRET", "")
FABRIC_TENANT_ID = os.getenv("FABRIC_TENANT_ID", "")

# Fabric Data Agent API base URL - uses the aiassistant/openai endpoint with api-version
FABRIC_API_BASE = f"https://api.fabric.microsoft.com/v1/workspaces/{FABRIC_WORKSPACE_ID}/dataagents/{FABRIC_ARTIFACT_ID}/aiassistant/openai"

# Page configuration
st.set_page_config(
    page_title="Healthcare Agent | Synthea", 
    page_icon="🏥", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Professional CSS styling
st.markdown("""
<style>
    /* Hide default Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Main container styling */
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
    }
    
    /* Force light mode for chat area */
    [data-testid="stChatMessageContent"] {
        color: #1a1a2e !important;
    }
    
    [data-testid="stChatMessageContent"] p,
    [data-testid="stChatMessageContent"] span,
    [data-testid="stChatMessageContent"] li,
    [data-testid="stChatMessageContent"] div {
        color: #1a1a2e !important;
    }
    
    /* Chat container styling */
    .chat-container {
        background: linear-gradient(180deg, #f8f9fa 0%, #ffffff 100%);
        border-radius: 16px;
        padding: 1rem;
        border: 1px solid #e9ecef;
        box-shadow: 0 4px 20px rgba(0,0,0,0.05);
        color: #1a1a2e;
    }
    
    /* Header styling */
    .agent-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem 2rem;
        border-radius: 16px;
        margin-bottom: 1.5rem;
        box-shadow: 0 8px 30px rgba(102, 126, 234, 0.3);
    }
    
    .agent-title {
        font-size: 2rem;
        font-weight: 700;
        color: white;
        margin: 0;
        display: flex;
        align-items: center;
        gap: 0.75rem;
    }
    
    .agent-subtitle {
        color: rgba(255,255,255,0.85);
        font-size: 1rem;
        margin-top: 0.5rem;
    }
    
    .status-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        background: rgba(255,255,255,0.2);
        padding: 0.4rem 1rem;
        border-radius: 20px;
        font-size: 0.85rem;
        color: white;
        margin-top: 0.75rem;
    }
    
    .status-dot {
        width: 8px;
        height: 8px;
        background: #00ff88;
        border-radius: 50%;
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    
    /* Message styling */
    .stChatMessage {
        background: white !important;
        border-radius: 12px;
        margin-bottom: 0.75rem;
        border: 1px solid #e9ecef;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    }
    
    .stChatMessage p, 
    .stChatMessage span,
    .stChatMessage li,
    .stChatMessage div,
    .stChatMessage h1,
    .stChatMessage h2,
    .stChatMessage h3,
    .stChatMessage h4,
    .stChatMessage h5,
    .stChatMessage h6 {
        color: #1a1a2e !important;
    }
    
    .stChatMessage code {
        background: #f1f3f5 !important;
        color: #1a1a2e !important;
    }
    
    .stChatMessage pre {
        background: #1a1a2e !important;
        color: #e9ecef !important;
    }
    
    .stChatMessage pre code {
        color: #e9ecef !important;
    }
    
    /* Input styling */
    .stChatInput {
        border-radius: 30px !important;
    }
    
    .stChatInput > div {
        border-radius: 30px !important;
        border: 2px solid #667eea !important;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.2) !important;
    }
    
    /* Sidebar styling */
    .css-1d391kg, [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
    }
    
    [data-testid="stSidebar"] .stMarkdown {
        color: rgba(255,255,255,0.9);
    }
    
    [data-testid="stSidebar"] h1, 
    [data-testid="stSidebar"] h2, 
    [data-testid="stSidebar"] h3 {
        color: white !important;
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        background: transparent;
        gap: 0.5rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: #f8f9fa;
        border-radius: 10px;
        padding: 0.75rem 1.5rem;
        border: 1px solid #e9ecef;
        font-weight: 500;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        border: none !important;
    }
    
    /* Quick action buttons */
    .quick-action {
        background: linear-gradient(145deg, #ffffff 0%, #f8f9fa 100%);
        border: 1px solid #e9ecef;
        border-radius: 12px;
        padding: 0.75rem 1rem;
        margin-bottom: 0.5rem;
        cursor: pointer;
        transition: all 0.2s ease;
        font-size: 0.9rem;
    }
    
    .quick-action:hover {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        transform: translateX(5px);
    }
    
    /* Metric cards */
    .metric-card {
        background: linear-gradient(145deg, #ffffff 0%, #f8f9fa 100%);
        border-radius: 12px;
        padding: 1.25rem;
        border: 1px solid #e9ecef;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    .metric-label {
        color: #6c757d;
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-top: 0.25rem;
    }
    
    /* File upload styling */
    .uploadedFile {
        background: linear-gradient(145deg, #d4edda 0%, #c3e6cb 100%);
        border-radius: 12px;
        padding: 1rem;
        border: 1px solid #28a745;
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.6rem 1.5rem;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
    }
    
    /* History panel */
    .history-item {
        background: rgba(255,255,255,0.1);
        border-radius: 8px;
        padding: 0.75rem;
        margin-bottom: 0.5rem;
        border-left: 3px solid #667eea;
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        background: #f8f9fa;
        border-radius: 10px;
    }
    
    /* DataFrame styling */
    .stDataFrame {
        border-radius: 12px;
        overflow: hidden;
    }
    
    /* Connection status banner */
    .connection-warning {
        background: linear-gradient(135deg, #ff6b6b 0%, #ee5a5a 100%);
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 12px;
        margin-bottom: 1rem;
        box-shadow: 0 4px 15px rgba(238, 90, 90, 0.3);
    }
    
    .connection-success {
        background: linear-gradient(135deg, #51cf66 0%, #40c057 100%);
        color: white;
        padding: 0.75rem 1.25rem;
        border-radius: 10px;
        margin-bottom: 0.5rem;
        font-size: 0.9rem;
    }
    
    /* SQL code block styling */
    .sql-block {
        background: #1a1a2e;
        border-radius: 8px;
        padding: 1rem;
        font-family: 'Monaco', 'Menlo', monospace;
        font-size: 0.85rem;
        overflow-x: auto;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)


def check_fabric_connection_status():
    """Quick check to see if Fabric Data Agent is accessible."""
    try:
        token = get_fabric_token()
        
        # Make a simple API call to check connectivity
        base_url = FABRIC_API_BASE
        api_version = "2024-07-01-preview"
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        
        # Try to create an assistant (quick connectivity check)
        resp = requests.post(
            f"{base_url}/assistants?api-version={api_version}",
            headers=headers,
            json={"model": "not used"},
            timeout=15
        )
        
        if resp.status_code == 200:
            return {"status": "connected", "message": "Connected to Fabric Data Agent"}
        elif resp.status_code == 404:
            resp_json = resp.json() if resp.text else {}
            if resp_json.get("errorCode") == "CapacityNotActive":
                return {"status": "capacity_paused", "message": "Fabric capacity is paused"}
            return {"status": "not_found", "message": "Data Agent not found"}
        else:
            return {"status": "error", "message": f"HTTP {resp.status_code}"}
            
    except requests.exceptions.Timeout:
        return {"status": "timeout", "message": "Connection timed out"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def format_response_with_sql(response):
    """Extract and format SQL from response for better display.
    
    Returns the response with SQL blocks highlighted and potentially
    extracted into separate code blocks.
    """
    import re
    
    # Check if response contains SQL
    if not response:
        return response
    
    # Common SQL keywords that indicate a SQL block
    sql_indicators = ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'ALTER', 'DROP', 'WITH', 'FROM', 'WHERE']
    
    # Look for code blocks with SQL
    sql_pattern = r'```sql\n(.*?)\n```'
    matches = re.findall(sql_pattern, response, re.IGNORECASE | re.DOTALL)
    
    if matches:
        # Response already has SQL code blocks - leave as is
        return response
    
    # Look for inline SQL that might not be in code blocks
    # This is a simple heuristic - look for SELECT...FROM patterns
    inline_sql_pattern = r'(SELECT\s+.+?\s+FROM\s+.+?)(?:\n\n|\Z)'
    
    formatted = response
    for match in re.finditer(inline_sql_pattern, response, re.IGNORECASE | re.DOTALL):
        sql = match.group(1).strip()
        if len(sql) > 50:  # Only format substantial SQL
            formatted = formatted.replace(sql, f"\n```sql\n{sql}\n```\n")
    
    return formatted


def init_session_state():
    defaults = {
        "credential": None,
        "conversation_id": None,
        "initialized": False,
        "messages": [{
            "role": "assistant", 
            "content": """👋 Hello! I'm your **Synthea Healthcare Agent**.

I'm connected to **Microsoft Fabric Data Agent** with access to your Synthea healthcare lakehouse containing **synthetic patient records** across 16+ tables:

**👤 Patient Data:**
- `patients` - Demographics (Id, BirthDate, DeathDate, Gender, Race, Ethnicity, Income, Healthcare_Expenses)
- `allergies` - Patient allergies (Patient, Code, Description, Type, Category)
- `careplans` - Care plans (Id, Patient, Code, Description, ReasonCode)
- `immunizations` - Vaccines (Patient, Code, Description, Cost)

**🏥 Clinical Data:**
- `conditions` - Diagnoses (Patient, Code, Description, Start, Stop)
- `medications` - Prescriptions (Patient, Code, Description, Base_Cost, TotalCost, Dispenses)
- `procedures` - Medical procedures (Patient, Code, Description, Base_Cost)
- `observations` - Vitals & labs (Patient, Code, Description, Value, Units)

**🏢 Administrative:**
- `encounters` - Visits (Id, Patient, EncounterClass, Code, Total_Claim_Cost)
- `organizations` - Facilities (Id, Name, City, State, Revenue, Utilization)
- `providers` - Clinicians (Id, Name, Speciality, Encounters, Procedures)
- `payers` - Insurance (Id, Name, Amount_Covered, Unique_Customers)

**🎯 Use the Quick Actions on the right, or try questions like:**
- "Show me the top 10 conditions by patient count"
- "What is the total medication cost by drug?"
- "Analyze encounter types - how many ambulatory vs emergency vs inpatient?"
- "Which organizations have the highest revenue?"

I can query your Fabric lakehouse directly and provide data-driven insights!""", 
            "timestamp": datetime.now().isoformat()
        }],
        "query_history": [], 
        "uploaded_files": [], 
        "file_summaries": {}
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def get_fabric_credential():
    """Get Azure credential for Fabric API authentication.
    
    Uses this priority:
    1. Client Secret (if FABRIC_CLIENT_SECRET is set) - for App Registration auth
    2. Managed Identity (in Azure Container Apps)
    3. Azure CLI (for local development)
    """
    try:
        # If client secret is configured, use App Registration auth
        if FABRIC_CLIENT_SECRET:
            credential = ClientSecretCredential(
                tenant_id=FABRIC_TENANT_ID,
                client_id=FABRIC_CLIENT_ID,
                client_secret=FABRIC_CLIENT_SECRET
            )
            return credential
        
        # Fall back to Managed Identity / Azure CLI chain
        credential = ChainedTokenCredential(
            ManagedIdentityCredential(),
            AzureCliCredential()
        )
        return credential
    except Exception as e:
        st.error(f"❌ Failed to get Azure credential: {e}")
        raise


def get_fabric_token():
    """Get access token for Fabric API using MSAL or Azure Identity."""
    # If client secret is set, use MSAL for token acquisition
    if FABRIC_CLIENT_SECRET:
        try:
            authority = f"https://login.microsoftonline.com/{FABRIC_TENANT_ID}"
            app = msal.ConfidentialClientApplication(
                FABRIC_CLIENT_ID,
                authority=authority,
                client_credential=FABRIC_CLIENT_SECRET
            )
            
            # Get token for Fabric API
            scopes = ["https://api.fabric.microsoft.com/.default"]
            result = app.acquire_token_for_client(scopes=scopes)
            
            if "access_token" in result:
                return result["access_token"]
            else:
                error_msg = result.get("error_description", result.get("error", "Unknown error"))
                st.error(f"❌ MSAL token acquisition failed: {error_msg}")
                raise Exception(f"MSAL error: {error_msg}")
                
        except Exception as e:
            st.error(f"❌ Failed to get MSAL token: {e}")
            raise
    
    # Fall back to Azure Identity credential
    credential = st.session_state.get("credential")
    if not credential:
        credential = get_fabric_credential()
        st.session_state["credential"] = credential
    token = credential.get_token("https://api.fabric.microsoft.com/.default")
    return token.token


def call_fabric_agent(user_message, conversation_id=None, max_retries=3):
    """Call the Fabric Data Agent API using the documented pattern.
    
    According to Microsoft docs, the correct flow is:
    1. Create an assistant via assistants.create() - this returns an internal assistant ID
    2. Create a thread
    3. Add message to thread
    4. Create a run using the assistant ID from step 1 (NOT the Data Agent artifact ID)
    5. Poll for completion
    6. Get messages
    7. Delete thread (cleanup)
    
    Includes retry logic with exponential backoff for transient errors.
    """
    import time as time_module
    
    for attempt in range(max_retries):
        try:
            token = get_fabric_token()
            
            # Use the API base URL with api-version parameter
            base_url = FABRIC_API_BASE
            api_version = "2024-07-01-preview"
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            
            thread_id = None
            assistant_id = None
            
            try:
                # Step 1: Create an assistant (this is KEY - returns the proper internal assistant ID)
                # Per docs: assistant = fabric_client.beta.assistants.create(model="not used")
                assistant_resp = requests.post(
                    f"{base_url}/assistants?api-version={api_version}",
                    headers=headers,
                    json={"model": "not used"},  # Model is managed by Fabric
                    timeout=60
                )
                
                # Check for Capacity Not Active error
                if assistant_resp.status_code == 404:
                    resp_json = assistant_resp.json() if assistant_resp.text else {}
                    if resp_json.get("errorCode") == "CapacityNotActive":
                        return """⚠️ **Fabric Capacity Not Active**

The Microsoft Fabric capacity is currently paused or not running.

**To fix this:**
1. Go to [Microsoft Fabric Admin Portal](https://app.fabric.microsoft.com/admin-portal)
2. Navigate to **Capacity settings**
3. Find your capacity and click **Resume** or **Start**
4. Wait 1-2 minutes for the capacity to become active
5. Try your query again

**Note:** Fabric capacities auto-pause after inactivity to save costs. This is normal behavior.""", conversation_id
                
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
                
                # Step 4: Create a run using the ASSISTANT ID (not the Data Agent artifact ID!)
                run_resp = requests.post(
                    f"{base_url}/threads/{thread_id}/runs?api-version={api_version}",
                    headers=headers,
                    json={"assistant_id": assistant_id},  # Use the assistant ID from step 1!
                    timeout=30
                )
                run_resp.raise_for_status()
                run = run_resp.json()
                run_id = run.get("id")
                run_status = run.get("status")
                
                # Step 5: Poll for completion (with timeout)
                max_wait = 300  # 5 minutes max for complex queries
                poll_interval = 2
                start_time = time_module.time()
                
                while run_status in ['queued', 'in_progress']:
                    if time_module.time() - start_time > max_wait:
                        return "⏱️ Request timed out. The query is taking too long.", thread_id
                    time_module.sleep(poll_interval)
                    
                    # Check run status
                    status_resp = requests.get(
                        f"{base_url}/threads/{thread_id}/runs/{run_id}?api-version={api_version}",
                        headers=headers,
                        timeout=30
                    )
                    status_resp.raise_for_status()
                    run = status_resp.json()
                    run_status = run.get("status")
                
                if run_status == 'completed':
                    # Step 6: Get messages from thread
                    msgs_resp = requests.get(
                        f"{base_url}/threads/{thread_id}/messages?api-version={api_version}&order=asc",
                        headers=headers,
                        timeout=30
                    )
                    msgs_resp.raise_for_status()
                    messages = msgs_resp.json()
                    
                    # Find assistant's response (last message from assistant)
                    assistant_response = ""
                    for msg in messages.get("data", []):
                        if msg.get("role") == "assistant":
                            for content in msg.get("content", []):
                                if content.get("type") == "text":
                                    assistant_response = content.get("text", {}).get("value", "")
                    
                    # Step 7: Cleanup - delete thread
                    try:
                        requests.delete(
                            f"{base_url}/threads/{thread_id}?api-version={api_version}",
                            headers=headers,
                            timeout=10
                        )
                    except:
                        pass  # Don't fail if cleanup fails
                    
                    if assistant_response:
                        return assistant_response, thread_id
                    return "No response received from agent.", thread_id
                else:
                    # Handle failed runs with specific error guidance
                    last_error = run.get("last_error", {})
                error_code = last_error.get("code", "") if isinstance(last_error, dict) else ""
                error_msg = last_error.get("message", str(last_error)) if isinstance(last_error, dict) else str(last_error)
                
                if error_code == "server_error" and "OpenAI request" in error_msg:
                    return f"""⚠️ **Fabric Data Agent Internal Error**

The query was submitted but Fabric's AI backend failed to process it.

**This is a known intermittent issue with Fabric Data Agents in preview.**

**Troubleshooting Steps:**
1. **Try the same query in Fabric Portal** - Open [synthea_da in Fabric](https://app.fabric.microsoft.com) and test directly
2. **Wait a few minutes and retry** - The service may be temporarily overloaded
3. **Try rephrasing your question** - Some queries work better than others
4. **Check Fabric capacity** - Ensure your capacity has AI workloads enabled

**Technical Details:**
- Error: `{error_code}`
- Message: `{error_msg[:200]}`
- Thread ID: `{thread_id}`
- Assistant ID: `{assistant_id}`""", thread_id
                
                return f"❌ Query failed with status: {run_status}\nError: {error_msg}", thread_id
                
            except requests.exceptions.HTTPError as http_err:
                error_str = str(http_err)
                status_code = http_err.response.status_code if http_err.response else "unknown"
                response_text = http_err.response.text if http_err.response else ""
                
                # Check for Capacity Not Active in HTTP error
                if "CapacityNotActive" in response_text:
                    return """⚠️ **Fabric Capacity Not Active**

The Microsoft Fabric capacity is currently paused or not running.

**To fix this:**
1. Go to [Microsoft Fabric Admin Portal](https://app.fabric.microsoft.com/admin-portal)
2. Navigate to **Capacity settings**
3. Find your capacity and click **Resume** or **Start**
4. Wait 1-2 minutes for the capacity to become active
5. Try your query again

**Note:** Fabric capacities auto-pause after inactivity to save costs.""", conversation_id
                
                # Check if it's a retryable error (5xx or connection issues)
                if status_code >= 500 and attempt < max_retries - 1:
                    wait_time = (2 ** attempt) * 2  # Exponential backoff: 2, 4, 8 seconds
                    time_module.sleep(wait_time)
                    continue  # Retry
                
                # Check if it's a 404 error - Data Agent not found
                if status_code == 404:
                    error_msg = f"""⚠️ **Data Agent Not Found (404)**

The API endpoint returned a 404 error.

**Possible Causes:**
1. The Data Agent ID may be incorrect
2. The Workspace ID may be incorrect
3. The Data Agent may have been deleted
4. The Fabric capacity may be paused

**Current Configuration:**
- API Base: `{FABRIC_API_BASE}`
- Workspace ID: `{FABRIC_WORKSPACE_ID}`
- Data Agent ID: `{FABRIC_ARTIFACT_ID}`

**Debug Info:** {response_text[:300]}"""
                    return error_msg, conversation_id
                
                return f"❌ HTTP Error {status_code}: {response_text[:300]}", conversation_id
                
            except Exception as api_error:
                # Retry on transient errors
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) * 2
                    time_module.sleep(wait_time)
                    continue
                return f"❌ Error calling Data Agent API: {str(api_error)}", conversation_id
                
        except requests.exceptions.Timeout:
            if attempt < max_retries - 1:
                continue  # Retry on timeout
            return "❌ Request timed out after multiple attempts. Please try again later.", conversation_id
        except Exception as e:
            if attempt < max_retries - 1:
                continue
            return f"❌ Error calling Fabric Agent: {str(e)}", conversation_id
    
    return "❌ Failed after multiple retry attempts. Please try again later.", conversation_id


def get_file_context():
    if not st.session_state["file_summaries"]:
        return ""
    context = "\n\n**UPLOADED FILES FOR ANALYSIS:**\n"
    for filename, summary in st.session_state["file_summaries"].items():
        context += f"\n### File: {filename}\n{summary}\n"
    return context


def process_uploaded_file(uploaded_file):
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        elif uploaded_file.name.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(uploaded_file)
        else:
            return None, "Unsupported file format."
        summary = f"Shape: {df.shape[0]} rows x {df.shape[1]} columns\nColumns: {', '.join(df.columns.tolist())}\nSample:\n{df.head(3).to_string()}"
        return df, summary
    except Exception as e:
        return None, f"Error: {str(e)}"


def run_fabric_query(user_query, placeholder):
    """Run a query through the Fabric Data Agent with progress indication."""
    dots = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    
    # Show initial progress
    placeholder.markdown(f"**{dots[0]} Connecting to Fabric Data Agent...**")
    
    # Add file context if available
    file_context = get_file_context()
    if file_context:
        user_query = f"{user_query}\n\n{file_context}"
    
    # Call the Fabric Data Agent
    response, new_conv_id = call_fabric_agent(
        user_query, 
        st.session_state.get("conversation_id")
    )
    
    # Update conversation ID for continuity
    st.session_state["conversation_id"] = new_conv_id
    
    return response


def export_chat():
    export = f"""# 🏥 Synthea Healthcare Agent - Chat Export
**Exported:** {datetime.now().strftime('%B %d, %Y at %I:%M %p')}
**Connected to:** Microsoft Fabric Data Agent

---

"""
    for msg in st.session_state["messages"]:
        role = "👤 **User**" if msg["role"] == "user" else "🤖 **Assistant**"
        export += f"{role}\n\n{msg['content']}\n\n---\n\n"
    return export


# Initialize session state
init_session_state()

# Initialize Fabric credential on first load
if not st.session_state["initialized"]:
    with st.spinner("🔄 Connecting to Fabric Data Agent..."):
        try:
            st.session_state["credential"] = get_fabric_credential()
            # Test the connection by getting a token
            get_fabric_token()
            st.session_state["initialized"] = True
        except Exception as e:
            st.error(f"❌ Failed to connect to Fabric: {e}")

# Header
st.markdown("""
<div class="agent-header">
    <div class="agent-title">🏥 Synthea Healthcare Agent</div>
    <div class="agent-subtitle">AI-powered healthcare data analysis with Microsoft Fabric</div>
    <div class="status-badge">
        <div class="status-dot"></div>
        <span>Connected to Fabric Data Agent • Synthea Lakehouse</span>
    </div>
</div>
""", unsafe_allow_html=True)

# Main tabs
tab1, tab2, tab3 = st.tabs(["💬 Chat", "📁 Upload Data", "📊 Analytics"])

with tab1:
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Check for pending quick question BEFORE rendering
        pending_query = None
        if "pq" in st.session_state and st.session_state["pq"]:
            pending_query = st.session_state["pq"]
            st.session_state["pq"] = None
        
        # Chat container
        chat_box = st.container(height=480)
        with chat_box:
            for msg in st.session_state["messages"]:
                with st.chat_message(msg["role"], avatar="🤖" if msg["role"] == "assistant" else "👤"):
                    st.markdown(msg["content"])
            
            # Process pending quick question inside the chat display
            if pending_query:
                ts = datetime.now().isoformat()
                st.session_state["messages"].append({"role": "user", "content": pending_query, "timestamp": ts})
                st.session_state["query_history"].append({"query": pending_query, "timestamp": ts})
                
                with st.chat_message("user", avatar="👤"):
                    st.markdown(pending_query)
                with st.chat_message("assistant", avatar="🤖"):
                    ph = st.empty()
                    ph.markdown("**⏳ Querying Fabric Data Agent...**")
                    try:
                        response = run_fabric_query(pending_query, ph)
                        formatted_response = format_response_with_sql(response)
                        st.session_state["messages"].append({
                            "role": "assistant", 
                            "content": formatted_response, 
                            "timestamp": datetime.now().isoformat()
                        })
                        # Rerun to display the response properly in the chat history
                        st.rerun()
                    except Exception as e:
                        ph.error(f"❌ Error: {e}")
        
        # Chat input
        if user_input := st.chat_input("Ask about patient data, conditions, medications..."):
            ts = datetime.now().isoformat()
            st.session_state["messages"].append({"role": "user", "content": user_input, "timestamp": ts})
            st.session_state["query_history"].append({"query": user_input, "timestamp": ts})
            
            with chat_box:
                with st.chat_message("user", avatar="👤"):
                    st.markdown(user_input)
                with st.chat_message("assistant", avatar="🤖"):
                    ph = st.empty()
                    ph.markdown("**⏳ Querying Fabric Data Agent...**")
                    try:
                        response = run_fabric_query(user_input, ph)
                        formatted_response = format_response_with_sql(response)
                        ph.markdown(formatted_response)
                        st.session_state["messages"].append({
                            "role": "assistant", 
                            "content": formatted_response, 
                            "timestamp": datetime.now().isoformat()
                        })
                    except Exception as e:
                        ph.error(f"❌ Error: {e}")
    
    with col2:
        st.markdown("### ⚡ Quick Actions")
        
        # Demo-friendly quick questions - natural language for Fabric Data Agent NL-to-SQL
        quick_questions = [
            ("📊 Database Overview", "Show me a summary of all tables in the database with their record counts."),
            ("🩺 Top 10 Conditions", "What are the top 10 most common medical conditions? Show the condition name and how many patients have each."),
            ("💊 Medication Analysis", "What are the top 10 medications by total cost? Show the medication name, total cost, and number of prescriptions."),
            ("🏥 Encounter Types", "Break down all patient encounters by type. Show the encounter class, count, and total costs."),
            ("👥 Patient Demographics", "Show patient demographics: total count, gender breakdown, average age, and counts by race."),
            ("🤧 Common Allergies", "What are the most common allergies? Show top 10 by number of patients affected."),
            ("🏢 Healthcare Facilities", "List the top 10 healthcare organizations by number of patient encounters."),
            ("👨‍⚕️ Provider Statistics", "Show the top 10 healthcare providers with the most patient encounters."),
            ("💉 Vaccinations", "What are the top 10 most administered vaccines? Show vaccine name and patient count."),
            ("💰 Cost Analysis", "What is the average healthcare expense and coverage per patient? Show a breakdown."),
            ("📋 Care Plans", "Show active care plans (where stop date is null) grouped by description."),
            ("🔬 Vital Signs", "Show average vital sign values grouped by observation type (like blood pressure, heart rate, BMI)."),
        ]
        
        for label, query in quick_questions:
            if st.button(label, key=f"quick_{label}", use_container_width=True):
                st.session_state["pq"] = query
                st.rerun()
        
        st.markdown("---")
        st.markdown("### 📜 Recent Queries")
        
        for i, item in enumerate(reversed(st.session_state["query_history"][-5:])):
            with st.expander(f"Q{len(st.session_state['query_history'])-i}", expanded=False):
                st.caption(item["query"][:80] + "..." if len(item["query"]) > 80 else item["query"])

with tab2:
    st.markdown("### 📁 Upload Files for Analysis")
    st.markdown("Upload CSV or Excel files to include in your analysis context.")
    
    upload_col1, upload_col2 = st.columns([2, 1])
    
    with upload_col1:
        uploaded = st.file_uploader(
            "Drag and drop or click to upload",
            type=['csv', 'xlsx', 'xls'],
            help="Supported formats: CSV, Excel (.xlsx, .xls)"
        )
        
        if uploaded and uploaded.name not in st.session_state["uploaded_files"]:
            with st.spinner("📊 Analyzing file..."):
                df, summary = process_uploaded_file(uploaded)
                if df is not None:
                    st.session_state["uploaded_files"].append(uploaded.name)
                    st.session_state["file_summaries"][uploaded.name] = summary
                    
                    st.success(f"✅ **{uploaded.name}** uploaded successfully!")
                    
                    # File stats
                    stat_cols = st.columns(4)
                    stat_cols[0].metric("📊 Rows", f"{df.shape[0]:,}")
                    stat_cols[1].metric("📋 Columns", df.shape[1])
                    stat_cols[2].metric("⚠️ Missing Values", f"{df.isnull().sum().sum():,}")
                    stat_cols[3].metric("💾 Size", f"{uploaded.size / 1024:.1f} KB")
                    
                    # Data preview
                    st.markdown("**📋 Data Preview:**")
                    st.dataframe(df.head(10), use_container_width=True)
                else:
                    st.error(f"❌ {summary}")
    
    with upload_col2:
        st.markdown("**📂 Uploaded Files:**")
        if st.session_state["uploaded_files"]:
            for fname in st.session_state["uploaded_files"]:
                st.markdown(f"✅ `{fname}`")
            
            st.markdown("---")
            if st.button("🗑️ Clear All Files", use_container_width=True):
                st.session_state["uploaded_files"] = []
                st.session_state["file_summaries"] = {}
                st.rerun()
        else:
            st.info("No files uploaded yet")

with tab3:
    st.markdown("### 📊 Session Analytics")
    
    # Metrics row
    metrics_cols = st.columns(4)
    
    user_msgs = len([m for m in st.session_state["messages"] if m["role"] == "user"])
    assistant_msgs = len([m for m in st.session_state["messages"] if m["role"] == "assistant"])
    
    metrics_cols[0].metric("💬 Questions Asked", user_msgs, delta=f"+{user_msgs}" if user_msgs > 0 else None)
    metrics_cols[1].metric("🤖 Responses", assistant_msgs)
    metrics_cols[2].metric("📁 Files Uploaded", len(st.session_state["uploaded_files"]))
    metrics_cols[3].metric("🟢 Agent Status", "Active")
    
    st.markdown("---")
    
    # Export options
    export_col1, export_col2 = st.columns(2)
    
    with export_col1:
        st.markdown("**📥 Export Chat History**")
        st.download_button(
            "📄 Download as Markdown",
            export_chat(),
            f"healthcare_chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
            "text/markdown",
            use_container_width=True
        )
    
    with export_col2:
        st.markdown("**📥 Export Query Log**")
        if st.session_state["query_history"]:
            st.download_button(
                "📊 Download as CSV",
                pd.DataFrame(st.session_state["query_history"]).to_csv(index=False),
                "query_history.csv",
                "text/csv",
                use_container_width=True
            )
        else:
            st.info("No queries to export yet")

# Sidebar
with st.sidebar:
    st.markdown("""
    <div style="text-align: center; padding: 1rem 0;">
        <div style="font-size: 3rem;">🏥</div>
        <div style="font-size: 1.2rem; font-weight: 600; color: white; margin-top: 0.5rem;">Healthcare Agent</div>
        <div style="font-size: 0.85rem; color: rgba(255,255,255,0.7);">Powered by Microsoft Fabric</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    st.markdown("### ⚙️ Configuration")
    st.markdown(f"""
    - **Backend:** Fabric Data Agent
    - **Lakehouse:** Synthea Graph
    - **Auth:** Azure AD / MI
    """)
    
    st.markdown("---")
    
    if st.button("🔄 New Conversation", use_container_width=True):
        st.session_state["messages"] = [{
            "role": "assistant", 
            "content": "👋 New conversation started! How can I help you with healthcare data today?",
            "timestamp": datetime.now().isoformat()
        }]
        st.session_state["query_history"] = []
        st.session_state.pop("conversation_id", None)
        st.rerun()
    
    st.markdown("---")
    
    st.markdown("### 📊 Database Schema")
    with st.expander("Patient Tables"):
        st.markdown("- `patients`\n- `allergies`\n- `careplans`\n- `immunizations`")
    
    with st.expander("Clinical Tables"):
        st.markdown("- `conditions`\n- `medications`\n- `procedures`\n- `observations`")
    
    with st.expander("Admin Tables"):
        st.markdown("- `encounters`\n- `organizations`\n- `providers`\n- `payers`")
    
    st.markdown("---")
    st.caption("🏥 Microsoft Healthcare AI © 2026")
