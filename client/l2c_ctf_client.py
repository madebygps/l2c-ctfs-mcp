import asyncio
import os
from contextlib import AsyncExitStack
from typing import Optional

from dotenv import load_dotenv
from mcp.client.sse import sse_client
from mcp import ClientSession


class MCPClient:
    def __init__(self):
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        
    async def cleanup(self):
        """Clean up resources"""
        if self.exit_stack:
            await self.exit_stack.aclose()

    async def connect_to_server(self, function_url: str = None, api_key: str = None):
        """Connect to an MCP server
        
        Args:
            function_url: The Azure Function URL for the MCP server
            api_key: Optional API key for authentication
        
        Raises:
            ValueError: If the function_url is invalid or missing protocol
        """
        if not function_url:
            raise ValueError("function_url is required")
        
        headers = {}
        if api_key:
            headers["x-functions-key"] = api_key
    
        
        streams = await self.exit_stack.enter_async_context(
        sse_client(function_url, headers=headers))
    
       
        self.session = await self.exit_stack.enter_async_context(
            ClientSession(
                read_stream=streams[0],
                write_stream=streams[1]
            )
        )
        await self.session.initialize()
            
        response = await self.session.list_tools()
        tools = response.tools
        print(f"Connected to L2C MCP Server: {function_url}")            
        print("\nConnected to server with tools:", [tool.name for tool in tools])



async def main():
    load_dotenv()
    function_url = os.getenv('FUNCTION_URL')
    api_key = os.getenv('FUNCTION_KEY')
    
    client = MCPClient()
    try:
        await client.connect_to_server(function_url, api_key)
    finally:
        await client.cleanup()

if __name__ == "__main__":
    asyncio.run(main())