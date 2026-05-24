from fastmcp import FastMCP, utilities
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from openai import OpenAI
from argparse import ArgumentParser
from importlib.resources import files
import os
import json

# Configure CORS for browser-based clients
middleware = [
    Middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Allow all origins; use specific origins for security
        allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
        allow_headers=[
            "mcp-protocol-version",
            "mcp-session-id",
            "Authorization",
            "Content-Type",
        ],
        expose_headers=["mcp-session-id"],
    )
]

mcp = FastMCP("booru-tag-mcp")
logger = utilities.logging.get_logger(__name__)

@mcp.tool()
async def get_tag_groups(query:str) -> list[str] :
    tag_groups: list[str] = {}
    tag_group_dir = files("booru_tag_mcp").joinpath("tags")
    all_tag_groups = [t.stem for t in tag_group_dir.rglob("*.txt")]
    logger.info(f"Trying host {os.environ.get('OPENAI_BASE_URL')} and key {os.environ.get('OPENAI_API_KEY')}")
    client = OpenAI(
        base_url = os.environ.get("OPENAI_BASE_URL"),
        api_key  = os.environ.get("OPENAI_API_KEY"),
        timeout = 3000
    )
    logger.info("OpenAI Client instantiated")
    with client.chat.completions.with_streaming_response.create(
        extra_headers={"reasoning": json.dumps({"effort": "low"})},
        messages=[{"role": "system", 
                   "content": "You are an expert at choosing tag groups for image creation. " + \
                    "From the following list, choose 3-5 selections that could provide " + \
                    "descriptions for the user prompt and return them as a comma separated list:\n" + 
                    json.dumps(all_tag_groups) + "\n" +
                    "Only return items from the list, doublecheck your suggestions are in the list before you answer"},
                  {"role": "user",
                   "content": query}], 
        model="Huihui-gemma-4-E4B-it-abliterated.i1-Q4_K_M"
    ) as response:
        completion = ""
        print(response.headers.get("X-My-Header"))

        for line in response.iter_lines():
            print(line)
            completion += line
    output = json.loads(completion)["choices"][0]["message"]["content"]
    logger.info("tag group output " + output)
    possible_tags = [a.strip() for a in output.split(',')]
    tag_groups = []
    # Filter out hallucinations
    for tag_group in possible_tags :
        source_tags_file = files("booru_tag_mcp").joinpath("tags", tag_group + ".txt")
        if source_tags_file.is_file() :
            tag_groups.append(tag_group)
        else :
            logger.info(f"Filtered out hallucination for tag group {tag_group}")
    return tag_groups

@mcp.tool()
async def get_tag(query:str, tag_group:str) -> list[str]:
    tags: list[str] = []
    source_tags_file = files("booru_tag_mcp").joinpath("tags", tag_group + ".txt")
    if not source_tags_file.is_file() :
        logger.error(f"Tag file for {tag_group} ({source_tags}) does not exist")
        return []
    source_tags = source_tags_file.open('r', encoding="utf-8").read().splitlines()
    client = OpenAI(
        base_url = os.environ.get("OPENAI_BASE_URL"),
        api_key  = os.environ.get("OPENAI_API_KEY"),
        timeout = 3000
    )
    logger.info("OpenAI Client instantiated")
    with client.chat.completions.with_streaming_response.create(
        extra_headers={"reasoning": json.dumps({"effort": "high"})},
        messages=[{"role": "system", 
                   "content": "You are an expert at choosing tags for image creation from the " + \
                    "following list, choose 3-5 selections that match the user prompt and " + \
                    "return them as a comma separated list:\n" + str(source_tags)},
                  {"role": "user",
                   "content": query}], 
        model="Huihui-gemma-4-E4B-it-abliterated.i1-Q4_K_M"
    ) as response:
        completion = ""
        print(response.headers.get("X-My-Header"))

        for line in response.iter_lines():
            print(line)
            completion += line
    output = json.loads(completion)["choices"][0]["message"]["content"]
    logger.info("tag output " + output)
    return [a.strip() for a in output.split(',')]

def main():
    parser = ArgumentParser(description="Command line start for booru-tag-mcp")
    parser.add_argument("--port", default=3000, type=int, help="Port to listen on")
    parser.add_argument("--host", default="localhost", help="Host to listen on, localhost for local communication only, 0.0.0.0 or the IP address of the computer for external communication (or running in a Docker container)")
    args = parser.parse_args()
    load_dotenv()
    mcp.run(transport="http", host=args.host, port=args.port, middleware=middleware)


if __name__ == "__main__":
    main()