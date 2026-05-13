import asyncio
from fastmcp import Client

client = Client("http://localhost:3000/mcp", timeout=300)

async def main() :
    async with client:
        await client.ping()
        tools = await client.list_tools()
        print(tools)
        result = await client.call_tool("get_face_tag", {"query" : "A beautiful girl"})
        print(result)

asyncio.run(main())