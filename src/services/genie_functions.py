import os
import json
from typing import Any, Callable, Set, Dict, Optional
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.dashboards import GenieAPI
import asyncio

# this code is based on https://github.com/carrossoni/DatabricksGenieBOT

async def genie_fetch_data(question: str, thread_id: Optional[str] = None) -> str:
    """
    Fetch data from Genie using the provided question and workspace_id.

    :param question: The question to ask Genie.
    :param workspace_id: The ID of the workspace.
    :param thread_id: The ID of the conversation thread (optional).
    :return: A tuple containing the JSON response and the conversation ID.
    """

    print (f"Calling genie_fetch_data with question: {question}")

    conversation_id = thread_id
    workspace_id = os.getenv("DATABRICKS_WORKSPACE_ID")

    workspace_client = WorkspaceClient(
        host = os.getenv("DATABRICKS_HOST"),
        # token not required. WorkspaceClient will use the default token from Azure CLI
        # See: https://databricks-sdk-py.readthedocs.io/en/stable/oauth.html#azure-cli-authentication
        # token = os.getenv("DATABRICKS_TOKEN"),
    )

    genie_api = GenieAPI(workspace_client.api_client)

    try:
        loop = asyncio.get_running_loop()
        if conversation_id is None:
            initial_message = await loop.run_in_executor(None, genie_api.start_conversation_and_wait, workspace_id, question)
            conversation_id = initial_message.conversation_id
        else:
            initial_message = await loop.run_in_executor(None, genie_api.create_message_and_wait, workspace_id, conversation_id, question)

        query_result = None
        if initial_message.query_result is not None:
            query_result = await loop.run_in_executor(None, genie_api.get_message_query_result,
                workspace_id, initial_message.conversation_id, initial_message.id)

        message_content = await loop.run_in_executor(None, genie_api.get_message,
            workspace_id, initial_message.conversation_id, initial_message.id)

        if query_result and query_result.statement_response:
            results = await loop.run_in_executor(None, workspace_client.statement_execution.get_statement,
                query_result.statement_response.statement_id)

            query_description = ""
            for attachment in message_content.attachments:
                if attachment.query and attachment.query.description:
                    query_description = attachment.query.description
                    break

            return json.dumps({
                "columns": results.manifest.schema.as_dict(),
                "data": results.result.as_dict(),
                "query_description": query_description
            })

        if message_content.attachments:
            for attachment in message_content.attachments:
                if attachment.text and attachment.text.content:
                    return json.dumps({"message": attachment.text.content}), conversation_id

        return json.dumps({"message": message_content.content}), conversation_id
    
    except Exception as e:
        # logger.error(f"Error in ask_genie: {str(e)}")
        return json.dumps({"error": "An error occurred while processing your request."}), conversation_id

# Example user input for each function
#1. Fecth Data
# user_input: "What is the average fare price for a taxi ride in New York City?"


user_functions: Set[Callable[..., Any]] = {
    genie_fetch_data
}