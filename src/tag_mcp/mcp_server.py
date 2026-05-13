from fastmcp import FastMCP, utilities
from openai import OpenAI
from argparse import ArgumentParser
from importlib.resources import files
import os
import json
mcp = FastMCP("tag-mcp")
logger = utilities.logging.get_logger(__name__)
@mcp.tool()
async def get_face_tag(query:str) -> list[str]:
    tags: list[str] = {}
    source_tags = files("tag_mcp").joinpath("tags", "faces.txt").open('r', encoding="utf-8").read().splitlines()
    client = OpenAI(
        base_url = os.environ.get("OPENAI_BASE_URL"),
        api_key  = os.environ.get("OPENAI_API_KEY"),
        timeout = 3000
    )
    logger.info("OpenAI Client instantiated")
    with client.chat.completions.with_streaming_response.create(
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
    logger.info("output " + output)
    return [a.strip() for a in output.split(',')]

def main(host:str, port:int) -> None:
    mcp.run(transport="http", host=host, port=port)

if __name__ == "__main__":
    parser = ArgumentParser(description="Command line start for tag-mcp")
    parser.add_argument("--port", default=3000, type=int, help="Port to listen on")
    parser.add_argument("--host", default="localhost", help="Host to listen on, localhost for local communication only, 0.0.0.0 or the IP address of the computer for external communication (or running in a Docker container)")
    args = parser.parse_args()
    main(host=args.host, port=args.port)
