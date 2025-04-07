import asyncio
from contextlib import AsyncExitStack
from typing import Optional

from anthropic import Anthropic
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.http import http_client
from dotenv import load_dotenv

load_dotenv()  # load environment variables from .env

class MCPClient:
    def __init__(self):
        # Initialize session and client objects
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.anthropic = Anthropic()
        
    async def cleanup(self):
        """Clean up resources"""
        if self.exit_stack:
            await self.exit_stack.aclose()

    async def connect_to_server(self, function_url: str, api_key: str = None):
        """Connect to an MCP server
        
        Args:
            server_script_path: Path to the server script (.py or .js)
        """
        headers = {}
        
        if api_key:
            headers["x-functions-key"] = api_key
       
        http_transport = await self.exit_stack.enter_async_context
        (http_client(function_url, headers=headers))
        
        self.stdio, self.write = http_transport
        self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))
        
        await self.session.initialize()
        
        # List available tools
        response = await self.session.list_tools()
        tools = response.tools
        print("Connected to L2C MCP Server{function_url}")
        print("\nConnected to server with tools:", [tool.name for tool in tools])



async def main():
    if len(sys.argv) < 3:
        print("Usage: python mcp_client.py <azure_function_url> <mcp_extension_system_key>")
        print("Example: python mcp_client.py https://myfuncapp.azurewebsites.net/runtime/webhooks/mcp/sse YOUR_KEY")
        sys.exit(1)
        
    function_url = sys.argv[1]
    api_key = sys.argv[2]
    
    client = MCPClient()
    try:
        await client.connect_to_server(function_url, api_key)
        # Add your interactive code here to use the MCP server
        # For example, wait for user input or run specific commands
    finally:
        await client.cleanup()

if __name__ == "__main__":
    import sys
    asyncio.run(main())