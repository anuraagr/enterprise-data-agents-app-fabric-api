import json
import asyncio
from dotenv import load_dotenv
import streamlit as st
from services.agent_provider import get_project_client, create_agent, delete_agent_async

config_path = "../config.json"

st.set_page_config(page_title="Configure Agents", page_icon=":guardsman:", layout="wide")

def get_config() -> dict:
    with open(config_path, "r") as f:
        config = json.load(f)
    return config

def init_session_state() -> None:
    if "agent_list" not in st.session_state:
        st.session_state["agent_list"] = []
    if "agent" not in st.session_state:
        st.session_state["agent"] = None
    if "agent_name" not in st.session_state:
        st.session_state["agent_name"] = None
    if "thread" not in st.session_state:
        st.session_state["thread"] = None
    if "project_client" not in st.session_state:
        st.session_state["project_client"] = None
    if "initialized" not in st.session_state:
        st.session_state["initialized"] = False

async def initialize_app() -> None:
    init_session_state()
    if st.session_state["initialized"] is False or st.session_state["project_client"] is None:
        st.session_state["project_client"] = await get_project_client()
        st.session_state["initialized"] = True

# Create a reusable loop
@st.cache_resource
def get_event_loop():
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop

def run_async(coro):
    loop = get_event_loop()
    return loop.run_until_complete(coro)

if "initialized" not in st.session_state or st.session_state["initialized"] is False:
    # Replace the direct asyncio.run() calls
    run_async(initialize_app())

with st.sidebar:
    st.header("🧠 Agents")
    if st.session_state["agent_list"]:
        agent_names = [a["name"] for a in st.session_state["agent_list"]]
        selected_name = st.selectbox("Select an agent", agent_names, index=agent_names.index(st.session_state["agent_name"]))
        if selected_name != st.session_state["agent_name"]:
            selected = next(a for a in st.session_state["agent_list"] if a["name"] == selected_name)
            st.session_state["agent"] = selected["agent"]
            st.session_state["thread"] = selected["thread"]
            st.session_state["agent_name"] = selected_name
            st.session_state["messages"] = []  # Optionally clear messages when switching

        with st.expander("Agent Details"):
            st.write(f"**Name:** {selected_name}")
            st.write(f"**Deployment:** {getattr(st.session_state['agent'], 'deployment_name', 'N/A')}")

st.title("🧠 Configure Azure Agents")
st.markdown("""
Welcome to the Agent Configuration Portal. Here, you can:
- 🛠️ Create, delete, and view agents
- 📝 Provide agent-specific instructions (prompts)
- ⚙️ Choose an Azure deployment model (e.g., GPT-4o variants)

> 💡 *Use clear prompts to guide the agent’s behavior.*
""")

# Divider for visual break
st.divider()

# Configuration Inputs
with st.container():
    st.subheader("🔧 Agent Setup")

    col1, col2, col3 = st.columns(3)
    with col1:
        agent_name = st.text_input("Agent Name", value="Enterprise Data Agent", key="agent_name_entry")
    with col2:
        tool_names = st.multiselect(
            "Select the Agent Tools from List", 
            options=["Fabric Sales Data Tool", "Genie Taxi Data Tool"], 
            key="tool_name_entry"
        )
    with col3:
        deployment_name = st.selectbox(
            "Select Deployment Name", 
            options=["gpt-4o-2", "gpt-4o-3"], 
            index=0, 
            key="deployment_name_entry"
        )
    

    prompt = st.text_area(
        "📝 Agent Prompt",
        value="""You are an agent who forwards user queries to various tools to get answers.
If the message is about taxi fare data, use the genie_fetch_data function.
If the message is about sales data, use the second tool in the toolset. Do NOT use a function call. Just use the second tool.
The data that is returned from genie_fetch_data is in JSON with the following format: "columns", "data", and "query_description".
Structure this as markdown with the "query_description" at the top and the columns and data in a table.""",
        height=200,
        key="prompt_entry"
    )

    st.caption("📌 The default deployment is `gpt-4o-2`. Your agent will use the selected deployment and prompt.")

    if st.button("🚀 Create Agent", key="create_agent"):
        project_client = st.session_state["project_client"]
        agent, thread = run_async(create_agent(project_client=project_client, agent_name=agent_name, prompt=prompt))
        
        st.session_state["agent"] = agent
        st.session_state["agent_name"] = agent_name
        st.session_state["thread"] = thread

        agent_obj = {"agent": agent, "thread": thread, "name": agent_name}
        st.session_state["agent_list"].append(agent_obj)

        st.success(f"✅ Agent **{agent_name}** created successfully!")

# Divider for visual break
st.divider()

# Manage Agents
if len(st.session_state["agent_list"]) > 0:
    with st.expander("📋 Manage Existing Agents", expanded=True):
        st.write("Here are your existing agents:")

        agent_names = [a["name"] for a in st.session_state["agent_list"]]
        selected_agent_name = st.selectbox("Choose an Agent", options=agent_names, key="agent_select")
        selected_agent = next((a for a in st.session_state["agent_list"] if a["name"] == selected_agent_name), None)

        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("💬 Use Agent"):
                st.session_state["agent"] = selected_agent["agent"]
                st.session_state["thread"] = selected_agent["thread"]
                st.session_state["agent_name"] = selected_name
                st.switch_page("pages/02-Agent_Playground.py")

        with col2:
            if st.button("❌ Delete Agent", key="delete_agent"):
                if selected_agent:
                    project_client = st.session_state["project_client"]
                    delete_agent_async(project_client=project_client, agent_id=selected_agent["agent"].id)
                    st.session_state["agent_list"] = [a for a in st.session_state["agent_list"] if a["name"] != selected_agent_name]
                    st.success(f"🗑️ Agent **{selected_agent_name}** deleted successfully.")
                else:
                    st.warning("No agent selected.")
        with col3:
            if st.button("👁️ View Agent", key="view_agent"):
                if selected_agent:
                    st.code(str(selected_agent), language="json")
                else:
                    st.warning("No agent selected.")

