from azure.ai.projects.models import AsyncFunctionTool, AsyncToolSet, FabricTool
import os
from dotenv import load_dotenv
from services.genie_functions import user_functions

load_dotenv()

async def get_fabric_sales_agent_tool(project_client) -> FabricTool:
    fabric_sales_agent_tool = None
    try:
        fabric_connection = await project_client.connections.get(connection_name=os.getenv("FABRIC_CONNECTION_NAME"))
        conn_id = fabric_connection.id
        fabric_sales_agent_tool = FabricTool(connection_id=conn_id)
        return fabric_sales_agent_tool
    except Exception as e:
        print(f"Error creating Fabric Sales Agent Tool: {e}")

    return fabric_sales_agent_tool
    
async def get_genie_sales_agent_tool(project_client) -> AsyncFunctionTool:
    genie_sales_agent_tool = None
    try:
        genie_sales_agent_tool = AsyncFunctionTool(functions=user_functions)
        return genie_sales_agent_tool
    except Exception as e:
        print(f"Error creating Genie Sales Agent Tool: {e}")

    return genie_sales_agent_tool

async def initialize_toolset(project_client) -> AsyncToolSet:
    try:
        fabric_sales_agent_tool = await get_fabric_sales_agent_tool(project_client=project_client)
        genie_sales_agent_tool = await get_genie_sales_agent_tool(project_client=project_client)

        toolset = AsyncToolSet()
        toolset.add(genie_sales_agent_tool)
        toolset.add(fabric_sales_agent_tool)

        return toolset
           
    except Exception as e:
        print(f"Error initializing toolset: {e}")
        return None