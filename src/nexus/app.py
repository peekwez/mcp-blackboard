# from contextlib import AsyncExitStack, asynccontextmanager

# from fastapi import FastAPI
# from nexus.models import ActionStream, ContextData
# from nexus.server import mcp
# from nexus.tools.context import save_context
# from nexus.tools.memory import add_to_stream


# @asynccontextmanager
# async def lifespan(app: FastAPI):  # type: ignore
#     async with AsyncExitStack() as stack:
#         await stack.enter_async_context(mcp.session_manager.run())
#         yield


# app = FastAPI(
#     title="Blackboard MCP Server",
#     description=(
#         "A blackboard server for storing and retrieving static "
#         "and dynamic data for an agent task"
#     ),
#     version="1.0.0",
#     lifespan=lifespan,
# )


# @app.get("/health")
# async def health_check() -> dict[str, str]:
#     """
#     Health check endpoint to verify the server is running.

#     Returns:
#         dict: A dictionary indicating the server is healthy.
#     """
#     return {"status": "healthy"}


# @app.put("/save-file")
# async def save_file(context: ContextData) -> dict[str, str]:
#     """
#     Save context data to the blackboard.

#     Args:
#         context (ContextData): The context data to save.

#     Returns:
#         dict: A confirmation message.
#     """
#     file_url = save_context(context.data, context.file_path)
#     return {"file_url": file_url}


# @app.put("/send-update")
# async def send_update(stream: ActionStream) -> dict[str, str]:
#     """
#     Send an action update to the blackboard.

#     Args:
#         action (ActionStream): The action stream containing the plan ID,
#             action, and data.

#     Returns:
#         dict: A confirmation message.
#     """
#     add_to_stream(stream)
#     return {"message": "Action update sent successfully."}
