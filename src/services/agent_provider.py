import os
import asyncio
from dotenv import load_dotenv
from azure.identity.aio import DefaultAzureCredential
from azure.ai.projects.aio import AIProjectClient
from services.tool_provider import initialize_toolset

load_dotenv()

async def get_project_client() -> AIProjectClient:
    async with DefaultAzureCredential() as creds:
        project_client = AIProjectClient.from_connection_string(
            credential=creds,
            conn_str=os.environ["PROJECT_CONNECTION_STRING"],
        )

    return project_client

async def create_agent(project_client, agent_name, prompt, deployment_name="gpt-4o-2") -> None:
    try:
        if project_client is None:
            project_client = await get_project_client()
        tools = await initialize_toolset(project_client=project_client)
        agent = await project_client.agents.create_agent(
            model=deployment_name,
            name=agent_name,
            instructions=prompt,
            toolset=tools,
        )
        
        thread = await project_client.agents.create_thread()

        return agent, thread
    except Exception as e:
        print(f"Error creating agent: {e}")
        return None, None
    

async def delete_agent_async(project_client, agent_id) -> None:
    try:
        if project_client is None:
            project_client = await get_project_client()
        await project_client.agents.delete_agent(agent_id)
    except Exception as e:
        print(f"Error deleting agent: {e}")