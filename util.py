import logging
import json
from argparse import ArgumentParser

def setup_argparser():
    parser = ArgumentParser(description="Enrich initial structure with links to other places")
    parser.add_argument("city", type=str, help="City to work with")
    
    return parser


def setup_logging(city=None):
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    logFormatter = None
    if city is not None:
        logFormatter = logging.Formatter("%(asctime)s %(message)s")
    else:
        logFormatter = logging.Formatter(f"%(asctime)s {city} %(message)s")
    
    consoleHandler = logging.StreamHandler()
    consoleHandler.setFormatter(logFormatter)
    
    logger.addHandler(consoleHandler)

    return logger


class Attraction:
    __slots__ = ("pageid", "title", "lat", "lon", "links_from", "links_to")

    def __init__(self, json_obj):
        self.pageid = json_obj["pageid"]
        self.title = json_obj["title"]
        self.lat = json_obj["lat"]
        self.lon = json_obj["lon"]
        self.links_from = json_obj["links"]
        self.links_to = 0

    def __repr__(self):
        return json.dumps({
            'title': self.title,
            'coordinates': f"[{self.lon}, {self.lat}]",
            'pageid': self.pageid,
            'links_to': self.links_to,
            'links_from': len(self.links_from)
        })

class Link:
    __slots__ = "location_id", "links_from", "links_to"

    def __init__(self, location_id, links_from, links_to):
        self.location_id = location_id
        self.links_from = links_from
        self.links_to = links_to

    def to_serializable(self):
        return {
            "id": self.location_id,
            "links_from": self.links_from,
            "links_to": self.links_to
        }