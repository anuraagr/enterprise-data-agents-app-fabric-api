# Enterprise Data Agents - Healthcare Edition

> **Note:** This repository is a fork of the original [mcaps-microsoft/enterprise-data-agents](https://github.com/mcaps-microsoft/enterprise-data-agents) repository with significant enhancements for healthcare data analysis using Microsoft Fabric Data Agents.

A sample application built with Azure AI Foundry and Microsoft Fabric that showcases enterprise-grade AI agents for querying healthcare data using natural language.

## 🌟 What's New in This Fork

This fork extends the original enterprise-data-agents repository with:

- **Healthcare Agent** - A specialized Streamlit-based conversational UI for querying Synthea healthcare data
- **Microsoft Fabric Data Agent Integration** - Direct integration with Fabric Data Agents for natural language SQL
- **Azure Container Apps Deployment** - One-click deployment script for Azure
- **Comprehensive Stress Testing Suite** - 50+ test queries across 8 categories
- **Enhanced Error Handling** - Retry logic, capacity detection, and user-friendly error messages

---

## 📁 Project Structure

```
enterprise-data-agents/
├── src/                              # Main application source code
│   ├── Home.py                       # Landing page with enterprise dashboard
│   ├── pages/
│   │   └── 01-Healthcare_Agent.py    # Healthcare chatbot interface
│   ├── services/
│   │   ├── agent_provider.py         # Azure AI Foundry agent management
│   │   ├── tool_provider.py          # Fabric & Genie tool initialization
│   │   └── genie_functions.py        # Databricks Genie integration
│   └── requirements.txt              # Python dependencies
├── tests/                            # Test suites
│   ├── stress_test_healthcare_agent.py  # Comprehensive stress testing
│   └── quick_test.py                 # Quick connectivity validation
├── docs/
│   └── STRESS_TEST_SUMMARY.md        # Test documentation
├── deploy-azure.ps1                  # Azure Container Apps deployment
├── Dockerfile                        # Container configuration
└── README.md                         # This file
```

---

## 🔧 Functions & Components Reference

### Core Application (`src/`)

#### `Home.py` - Enterprise Landing Page
| Function/Component | Description |
|-------------------|-------------|
| Hero Section | Professional landing page with gradient styling |
| Quick Stats | Display of data tables, patient counts, records, and security status |
| Feature Cards | Showcases AI capabilities and integrations |
| Navigation | Links to Healthcare Agent and other tools |

#### `pages/01-Healthcare_Agent.py` - Healthcare Chatbot
| Function | Description |
|----------|-------------|
| `init_session_state()` | Initialize Streamlit session with default values and welcome message |
| `get_fabric_credential()` | Get Azure credential (ClientSecret → ManagedIdentity → AzureCLI chain) |
| `get_fabric_token()` | Acquire OAuth token for Fabric API using MSAL or Azure Identity |
| `check_fabric_connection_status()` | Quick connectivity check to Fabric Data Agent |
| `call_fabric_agent(user_message, conversation_id, max_retries)` | Execute queries against Fabric Data Agent with retry logic |
| `format_response_with_sql(response)` | Extract and format SQL code blocks from responses |
| `process_uploaded_file(uploaded_file)` | Parse CSV/Excel files for context-aware queries |
| `get_file_context()` | Build context string from uploaded file summaries |
| `run_fabric_query(user_query, placeholder)` | Execute query with progress indication |

**Fabric Data Agent API Flow:**
1. Create assistant via `POST /assistants`
2. Create thread via `POST /threads`
3. Add user message via `POST /threads/{id}/messages`
4. Create run via `POST /threads/{id}/runs`
5. Poll for completion via `GET /threads/{id}/runs/{run_id}`
6. Retrieve messages via `GET /threads/{id}/messages`
7. Cleanup via `DELETE /threads/{id}`

---

### Services (`src/services/`)

#### `agent_provider.py` - Azure AI Foundry Agent Management
| Function | Description |
|----------|-------------|
| `get_project_client()` | Create AsyncAIProjectClient using DefaultAzureCredential |
| `create_agent(project_client, agent_name, prompt, deployment_name)` | Create new AI agent with Fabric+Genie toolset |
| `delete_agent_async(project_client, agent_id)` | Clean up agent resources |

#### `tool_provider.py` - Tool Initialization
| Function | Description |
|----------|-------------|
| `get_fabric_sales_agent_tool(project_client)` | Initialize FabricTool from connected resource |
| `get_genie_sales_agent_tool(project_client)` | Initialize AsyncFunctionTool for Databricks Genie |
| `initialize_toolset(project_client)` | Combine Fabric and Genie tools into AsyncToolSet |

#### `genie_functions.py` - Databricks Genie Integration
| Function | Description |
|----------|-------------|
| `genie_fetch_data(question, thread_id)` | Query Databricks Genie with natural language, returns JSON with columns, data, and query description |

---

### Testing Suite (`tests/`)

#### `stress_test_healthcare_agent.py` - Comprehensive Stress Testing
| Function | Description |
|----------|-------------|
| `get_fabric_token()` | Acquire authentication token via MSAL |
| `call_fabric_agent(user_message, max_retries)` | Execute query with retry logic and error classification |
| `run_stress_test(categories, delay_between_queries)` | Run full test suite across specified categories |
| `quick_connectivity_test()` | Verify basic connectivity to Fabric Data Agent |

**Test Categories:**
| Category | Queries | Description |
|----------|---------|-------------|
| `schema_discovery` | 4 | Table and column introspection |
| `patient_queries` | 5 | Patient demographics analysis |
| `condition_queries` | 4 | Diagnosis and condition analysis |
| `medication_queries` | 5 | Prescription cost analytics |
| `encounter_queries` | 5 | Visit and encounter analysis |
| `complex_joins` | 5 | Multi-table relationship queries |
| `aggregate_analytics` | 5 | Summary statistics and trends |
| `quick_questions` | 12 | UI quick action queries |

#### `quick_test.py` - Quick Validation
| Function | Description |
|----------|-------------|
| `get_token()` | Acquire token for testing |
| `run_query(query, timeout_secs)` | Execute single query with timeout |

---

### Deployment (`deploy-azure.ps1`)

Automated Azure Container Apps deployment script that:

| Step | Action |
|------|--------|
| 1 | Create Resource Group (`rg-synthea-agent`) |
| 2 | Create Azure Container Registry |
| 3 | Build and push Docker image using ACR Tasks |
| 4 | Create Container Apps Environment |
| 5 | Get ACR credentials |
| 6 | Deploy Container App with environment variables and secrets |
| 7 | Get application URL |
| 8 | Assign Cognitive Services OpenAI User role to Managed Identity |

---

## 🏥 Synthea Healthcare Data Schema

The Healthcare Agent queries a Fabric Lakehouse containing synthetic patient data:

| Table | Description | Key Columns |
|-------|-------------|-------------|
| `patients` | Patient demographics | Id, Gender, Race, BirthDate, DeathDate, Healthcare_Expenses |
| `conditions` | Diagnoses | Patient, Code, Description, Start, Stop |
| `medications` | Prescriptions | Patient, Description, Base_Cost, TotalCost, Dispenses |
| `encounters` | Visits | Patient, EncounterClass, Total_Claim_Cost, Organization |
| `procedures` | Medical procedures | Patient, Code, Description, Base_Cost |
| `observations` | Vitals and labs | Patient, Description, Value, Units |
| `allergies` | Patient allergies | Patient, Description, Type, Category |
| `immunizations` | Vaccines | Patient, Description, Cost |
| `careplans` | Care plans | Patient, Description, ReasonCode |
| `organizations` | Healthcare facilities | Name, City, Revenue, Utilization |
| `providers` | Clinicians | Name, Speciality, Encounters |
| `payers` | Insurance | Name, Amount_Covered, Unique_Customers |

---

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- Azure CLI installed and authenticated
- Microsoft Fabric workspace with Data Agent configured (F64+ SKU)
- Azure AI Foundry project with Fabric connected resource

### Local Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/mcaps-microsoft/enterprise-data-agents.git
   cd enterprise-data-agents
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   # or
   source .venv/bin/activate  # Linux/Mac
   ```

3. **Install dependencies:**
   ```bash
   pip install -r src/requirements.txt
   ```

4. **Configure environment variables:**
   ```bash
   cp src/env.example src/.env
   # Edit .env with your credentials
   ```

   Required variables:
   ```env
   PROJECT_CONNECTION_STRING="<AI Foundry connection string>"
   FABRIC_CONNECTION_NAME="<Fabric connected resource name>"
   FABRIC_CLIENT_ID="<App registration client ID>"
   FABRIC_CLIENT_SECRET="<App registration client secret>"
   FABRIC_TENANT_ID="<Azure tenant ID>"
   FABRIC_WORKSPACE_ID="<Fabric workspace GUID>"
   FABRIC_ARTIFACT_ID="<Data Agent artifact GUID>"
   ```

5. **Run locally:**
   ```bash
   cd src
   streamlit run Home.py
   ```

### Deploy to Azure Container Apps

```powershell
# Run the deployment script
.\deploy-azure.ps1
```

This will deploy to: `https://synthea-healthcare-agent.<env>.eastus.azurecontainerapps.io`

---

## 🧪 Testing

### Quick Connectivity Test
```bash
python tests/stress_test_healthcare_agent.py --quick
```

### Run Specific Category
```bash
python tests/stress_test_healthcare_agent.py --category quick_questions
```

### Full Stress Test
```bash
python tests/stress_test_healthcare_agent.py --all --delay 3
```

---

## 🔐 Authentication

The application supports multiple authentication methods:

| Method | Use Case |
|--------|----------|
| **Client Secret** | Production deployments with App Registration |
| **Managed Identity** | Azure Container Apps with system-assigned identity |
| **Azure CLI** | Local development |

Authentication priority: ClientSecretCredential → ManagedIdentityCredential → AzureCliCredential

---

## 📊 Sample Queries

Try these queries with the Healthcare Agent:

| Query | Description |
|-------|-------------|
| "What tables are available?" | Schema discovery |
| "Show top 10 conditions by patient count" | Condition analysis |
| "What is the total medication cost by drug?" | Cost analytics |
| "Analyze encounter types" | Visit breakdown |
| "Which providers have the most patients?" | Provider statistics |
| "Show healthcare spending by gender" | Demographic analysis |

---

## 🐛 Troubleshooting

### Fabric Capacity Not Active
The Fabric capacity may auto-pause. Resume via:
1. Go to [Fabric Admin Portal](https://app.fabric.microsoft.com/admin-portal)
2. Navigate to Capacity settings
3. Find your capacity and click **Resume**

### Authentication Errors
- Ensure Azure CLI is logged in: `az login`
- Verify `.env` file has correct credentials
- Check App Registration has Fabric API permissions

### Query Timeouts
- Complex queries may take 60-120 seconds
- The agent includes automatic retry with exponential backoff

---

## 📄 License

This project is for demonstration purposes. See the original repository for licensing information.

---

## 🙏 Acknowledgments

- Original repository: [mcaps-microsoft/enterprise-data-agents](https://github.com/mcaps-microsoft/enterprise-data-agents)
- Synthea synthetic healthcare data: [synthetichealth/synthea](https://github.com/synthetichealth/synthea)
- Microsoft Fabric Data Agent documentation
- Azure AI Foundry SDK

