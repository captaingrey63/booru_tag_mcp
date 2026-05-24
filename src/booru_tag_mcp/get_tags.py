import time
from pathlib import Path
from argparse import ArgumentParser
import subprocess
from html.parser import HTMLParser
from urllib.parse import unquote
from tqdm import tqdm
SERVER = "https://danbooru.donmai.us"
translation_table = str.maketrans('_', ' ')

class TagGroupParser(HTMLParser):
    """
    Parses the tag group page to get the individual tag group URLs
    """
    tag_groups: list[str] = []
    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            for attr in attrs:
                if attr[0] == 'href':
                    if attr[1].startswith("/wiki_pages/tag_group"):
                        self.tag_groups.append(SERVER + attr[1])

class TagParser(HTMLParser):
    """
    Parses the individual Tag Group pages to get a list of tags
    """
    add_tags: bool = False
    tags: list[str] = []
    def reset_tags(self):
        self.tags = []
    def handle_starttag(self, tag, attrs):
        tag_type : str | None = None
        if tag == "a" :
            for attr in attrs :
                if attr[0] == "class" and \
                  attr[1].find("tag-type") > 0 :
                    try :
                        tag_type = next(tag for tag in attr[1].split(' ') if tag.startswith("tag-type"))
                    except StopIteration :
                        pass
                elif attr[0] == "href" and \
                  attr[1].startswith("/wiki_pages/") and \
                  attr[1] != "/wiki_pages/tag_groups" and \
                  tag_type != None and tag_type == "tag-type-0":
                    self.tags.append(unquote(attr[1].split('/')[-1]).translate(translation_table))

def main():
    parser = ArgumentParser()
    parser.add_argument("--rate-limit", "-l", help="Change the rate limiting for fetching booru pages, specifying delay in seconds", type=float, default=5)
    args = parser.parse_args()
    booru_delay:float = args.rate_limit
    page_base = Path("tag_pages")
    page_base.mkdir(exist_ok=True)
    tag_base = Path("tags")
    tag_base.mkdir(exist_ok=True)
    filename = "tag_groups.html"
    if not (page_base / filename).is_file():
        subprocess.run(["curl", "--output", page_base / filename, "--silent", SERVER + "/wiki_pages/tag_groups"])
        time.sleep(booru_delay)

    parser = TagGroupParser()
    with open(page_base / filename, "r", encoding="utf-8") as tag_groups:
        parser.feed(tag_groups.read())
    t= tqdm(total=len(parser.tag_groups))
    for i, tag_group in enumerate(parser.tag_groups):
        t.update(1)
        split = tag_group.find("%3A")
        t.set_postfix_str(tag_group[split+3:])
        html_filename = page_base / (tag_group[split+3:] + ".html")
        text_filename = tag_base / (tag_group[split+3:] + ".txt")
        if not (html_filename).is_file():
            subprocess.run(["curl", "--output", html_filename, "--silent", tag_group])
            time.sleep(booru_delay)
        parser = TagParser()
        parser.reset_tags()
        with open(html_filename, "r", encoding="utf-8") as tag_group :
            parser.feed(tag_group.read())
        with open(text_filename, "w", encoding="utf-8") as tag_file:
            tag_file.write('\n'.join(parser.tags))

if __name__ == "__main__":
    main()