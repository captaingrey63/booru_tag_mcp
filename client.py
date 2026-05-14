import asyncio
import json
from fastmcp import Client
from argparse import ArgumentParser
client = Client("http://localhost:3000/mcp", timeout=300)

async def main() :
    parser = ArgumentParser()
    parser.add_argument("--query", "-q", default="A beautiful girl in a forest")
    args = parser.parse_args()
    async with client:
        await client.ping()
        tools = await client.list_tools()
        print(tools)
        result = await client.call_tool("get_tag_groups", {"query" : args.query})
        tag_groups = json.loads(result.content[0].text)
        tags :list[str] = []
        for tag_group in tag_groups :
            print(f"Getting tags for group {tag_group}")
            result = await client.call_tool("get_tag", {"query" : args.query, "tag_group" : tag_group})
            group_tags = json.loads(result.content[0].text)
            tags.extend(group_tags)
        print(", ".join(tags))

asyncio.run(main())