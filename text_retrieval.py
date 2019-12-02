import os
import sys
import json
import logging
import mediawiki
from path import Path
from datetime import date
from time import time
from argparse import ArgumentParser


def setup_argparser():
    parser = ArgumentParser(description="Simple wikipedia text retieval")
    parser.add_argument("city", type=str, help="City to work with")
    # parser.add_argument("f_in", type=str, help="File with json")
    # parser.add_argument("f_out", type=str, help="File to put json with text")

    return parser

def setup_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    logFormatter = logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s")
    consoleHandler = logging.StreamHandler()
    consoleHandler.setFormatter(logFormatter)
    
    logger.addHandler(consoleHandler)

    return logger

def setup_mediawiki():
    wikipedia = mediawiki.MediaWiki(user_agent="otaratukhin", lang="ru")
    return wikipedia

def search_by_id(attraction):
    page = None
    try: 
        page = wikipedia.page(pageid=attraction["pageid"])
    except mediawiki.MediaWikiException as e:
        logger.error(f"Searching by pageid: {e}")
    finally:
        return page

def search_by_title(attraction):
    page = None
    try: 
        page = wikipedia.page(pageid=attraction["pageid"])
    except mediawiki.MediaWikiException as e:
        logger.error(f"Searching by title: {e}")
    finally:
        return page

def search(attraction):
    search_strategies = [search_by_id, search_by_title]
    page = None

    for search_strategy in search_strategies:
        page = search_strategy(attraction)
        if page is not None:
            return page
    return None

def entity_retrieval(wiki_page):
    return {
        "links": wiki_page.links,
        "content": wiki_page.content,
        "summary": wiki_page.summary
    }

logger = setup_logging()

if __name__ == "__main__":
    args = setup_argparser().parse_args()
    logger.info(f"Got arguments: {args}")
    
    wikipedia = setup_mediawiki()
    city = args.city
    PATH_TO_DATA = Path(f"data/{city}")
    path_f_in = PATH_TO_DATA / f"{city}-wikiid.json"
    path_f_out = PATH_TO_DATA / "attractions.json"
    path_matched = PATH_TO_DATA / "unmatched.json"

    if not os.path.exists(path_f_in):
        logger.error(f"File passed as input doesn't exist: {path_f_in.f_in}")
        raise Exception()
    
    with open(path_f_in, "r") as f_in:
        with open(path_f_out, "w") as f_out:
            logger.info(f"Processing attraction is {city}")
            attractions = json.load(f_in)

            unmatched = []
            for i, attraction in enumerate(attractions):
                try:
                    logger.info(f"Processing attraction {attraction['title']}")
                    
                    page = search(attraction)
                    if page is None:
                        raise Exception(f"Page {attraction['title']} cannot be identified")

                    entities = entity_retrieval(page)

                    attractions[i]["links"] = entities["links"]
                    attractions[i]["content"] = entities["content"]
                    
                except Exception as e:
                    logger.error(f"Error: {e}")
                    unmatched.append(attraction)

            len_unmatched = len(unmatched)
            if len_unmatched > 0:
                logger.info(f"Found {len_unmatched} unmatched attractions")
                with open(path_matched, "w") as errors_file:
                    errors_file.write(json.dumps(unmatched))

            f_out.write(json.dumps(attractions))
            logger.info("Done")
