import os
import asyncio
from dotenv import load_dotenv
from azure.ai.projects.aio import AIProjectClient
from azure.ai.projects.models import AsyncFunctionTool, AsyncToolSet, FabricTool
from azure.identity.aio import DefaultAzureCredential
from services.genie_functions import user_functions

import streamlit as st

load_dotenv()

def init_session_state() -> None:
    if "agent_list" not in st.session_state:
        st.session_state["agent_list"] = []
    if "agent" not in st.session_state:
        st.session_state["agent"] = None
    if "thread" not in st.session_state:
        st.session_state["thread"] = None
    if "project_client" not in st.session_state:
        st.session_state["project_client"] = None
    if "initialized" not in st.session_state:
        st.session_state["initialized"] = False
    if "messages" not in st.session_state:
        st.session_state["messages"] = [
            {"role": "assistant", "content": "Hello! How can I assist you today?"}
        ]

async def get_project_client() -> AIProjectClient:
    async with DefaultAzureCredential() as creds:
        project_client = AIProjectClient.from_connection_string(
            credential=creds,
            conn_str=os.environ["PROJECT_CONNECTION_STRING"],
        )

    return project_client

async def create_agent(project_client) -> None:
    # Creating the agent and thread - need to save this to session state in streamlit
    # Create the Fabric Data Agent Tool 
    project_client = st.session_state["project_client"]
    fabric_connection = await project_client.connections.get(connection_name=os.getenv("FABRIC_CONNECTION_NAME"))
    conn_id = fabric_connection.id
    fabric = FabricTool(connection_id=conn_id)

    # Create the Genie tool, which is coded as a local function
    genie = AsyncFunctionTool(functions=user_functions)

    # Create the toolset with the Genie and Fabric tools
    toolset = AsyncToolSet()
    toolset.add(genie)
    toolset.add(fabric)

    agent = await project_client.agents.create_agent(
        model="gpt-4o-2",
        name="Business Data Agent",
        instructions=
        """
        You are an agent who forwards user queries to various tools to get answers.
        If the message is about taxi fare data, use the genie_fetch_data function.
        If the message is about sales data, use the second tool in the toolset. Do NOT use a function call. Just use the second tool.
        The data that is returned from genie_fetch_data is in json with the following format: ""columns"", ""data"", and ""query_description"".
        Struture this as markdown with the ""query_description"" at the top and the columns and data in a table.
        """,
        toolset=toolset,
    )
    
    thread = await project_client.agents.create_thread()

    return agent, thread

async def delete_agent_async(project_client, agent_id) -> None:
    # Delete the agent when complete - not sure why I'm creating another function for this it's really not needed
    # but I guess it's a good practice to have it in case you want to delete an agent at any time.
    await project_client.agents.delete_agent(agent_id)
    

async def post_message_async(user_input: str) -> None:
    project_client = st.session_state["project_client"]
    agent = st.session_state["agent"]
    thread = st.session_state["thread"]
    # Check if agent and thread are initialized
    # Create message to thread
    message = await project_client.agents.create_message(
        thread_id=thread.id,
        role="user",
        #content="What percentage of trips were paid with cash",
        #content="What is the best selling product?",
        content=user_input,
    )
    print(f"Created message, ID: {message.id}")

    # Create and process agent run in thread with tools
    with st.spinner("Retrieving response from agent..."):
        # This is where the agent will process the message and return a response
        # This is an async function so it will run in the background while the rest of the code continues to run
        run = await project_client.agents.create_and_process_run(thread_id=thread.id, agent_id=agent.id)
        print(f"Run finished with status: {run.status}")

    # print the response
    if run.status == "completed":
        text = await get_latest_messages_async(project_client, thread, agent)
        with st.container(border=True):
            with st.chat_message("assistant"):
                st.write(text)

    if run.status == "failed":
        # Check if you got "Rate limit is exceeded.", then you want to get more quota
        print(f"Run failed: {run.last_error}")
        await delete_agent_async(project_client, agent.id)

async def get_latest_message_async(project_client, thread, agent) -> str:
    try:
        messages = await project_client.agents.list_messages(thread_id=thread.id)
        last_message_content = messages.data[0].text_messages[0]
        if last_message_content.text:
            print(f"Agent Response: {last_message_content.text.value}")
            return last_message_content.text.value
    except Exception as e:
        print(f"Error fetching messages: {e}")
        await delete_agent_async(project_client, agent.id)

async def get_latest_messages_async(project_client, thread, agent):
    try:
        messages_response = await project_client.agents.list_messages(thread_id=thread.id)
        messages = messages_response.data  # newest to oldest

        assistant_chunks = []
        found_latest_user = False

        for msg in messages:
            if msg.role == "user":
                # Stop at the *first* user message we find (newest user input)
                found_latest_user = True
                break
            elif msg.role == "assistant":
                for part in msg.text_messages:
                    if part.text and part.text.value:
                        assistant_chunks.insert(0, part.text.value)  # keep in order

        if not found_latest_user:
            print("⚠️ Did not find a user message in the thread")
            return ["⚠️ No agent response found."]
        
        return assistant_chunks if assistant_chunks else ["⚠️ No agent response found."]
    
    except Exception as e:
        print(f"Error fetching messages: {e}")
        await delete_agent_async(project_client, agent.id)
        return ["❌ Failed to fetch agent response."]



def configure_streamlit() -> None:
    st.set_page_config(page_title="Enterprise Data Agent", page_icon="🤖")
    st.title("🤖 Enterprise Data Agent")
    st.markdown("Ask anything about your **sales** and **taxi fare data** below.")
    st.caption("Powered by Azure AI Foundry & Streamlit")

async def initialize_app() -> None:
    init_session_state()
    if st.session_state["initialized"] is False or st.session_state["project_client"] is None:
        st.session_state["project_client"] = await get_project_client()
        st.session_state["agent"], st.session_state["thread"] = await create_agent(st.session_state["project_client"])
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

configure_streamlit()
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

# Chat UI
for msg in st.session_state["messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if user_input := st.chat_input("Type your message here..."):
    # Save user message
    st.session_state["messages"].append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                project_client = st.session_state["project_client"]
                agent = st.session_state["agent"]
                thread = st.session_state["thread"]

                run_async(project_client.agents.create_message(
                    thread_id=thread.id,
                    role="user",
                    content=user_input
                ))

                run = run_async(project_client.agents.create_and_process_run(
                    thread_id=thread.id,
                    agent_id=agent.id
                ))

                if run.status == "completed":
                    responses = run_async(get_latest_messages_async(project_client, thread, agent))
                    for i, text in enumerate(responses):
                        st.markdown(text)
                        # Add thumbs for each response
                        msg_index = len(st.session_state["messages"])
                        col1, col2, _ = st.columns([1, 1, 8])
                        with col1:
                            if st.button("👍", key=f"thumbs_up_{msg_index}_{i}"):
                                st.toast("You liked this response! 👍")
                        with col2:
                            if st.button("👎", key=f"thumbs_down_{msg_index}_{i}"):
                                st.toast("Sorry this wasn't helpful. 👎")
                        st.session_state["messages"].append({"role": "assistant", "content": text})
                else:
                    err_msg = f"❌ Agent failed: {run.last_error.get('message', 'Unknown error')}"
                    st.error(err_msg)
                    st.session_state["messages"].append({"role": "assistant", "content": err_msg})

            except Exception as e:
                st.error(f"💥 Unexpected error: {str(e)}")
