import os
import sys
import json
import logging
from path import Path
import networkx as nx
from argparse import ArgumentParser
from collections import defaultdict
import geopandas as geopd


def setup_argparser():
    parser = ArgumentParser(description="Simple graph construction")
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


logger = setup_logging()


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


def extract_graph(json):
    attractions = []
    table = dict()

    logger.info(f"Extracting attractions and references")

    for obj in json:
        try:
            origin = Attraction(obj)
            table[origin.title] = origin
            attractions.append(origin)
        except Exception as e:
            logger.error(f"Error when parsing {obj['title']}: {e}")

    logger.info(f"Got {len(attractions)} attractions")
    
    edges = []
    pagerank_table = defaultdict(int)
    from_list = []
    to_list = []
    for attraction in attractions:
        for link in attraction.links_from:
            if link in table:
                pagerank_table[link] += 1
                reference = table[link]

                from_list.append(attraction)
                to_list.append(reference)
                edges.append((attraction, reference))
        
        logger.info(f"Processed attraction, current edges count is {len(edges)}")

    logger.info(f"Updating pagerank")
    for title, attraction in table.items():
        attraction.links_to = pagerank_table[title]
    logger.info(f"Pagerank updated")
    
    logger.info(f"Retrieval finished, got {len(attractions)} nodes and {len(edges)} edges")

    return attractions, edges, from_list, to_list

if __name__ == "__main__":
    args = setup_argparser().parse_args()
    logger.info(f"Got arguments: {args}")

    city = args.city
    PATH_TO_DATA = Path(f"data/{city}")
    path_f_in = PATH_TO_DATA / "attractions.json"
    path_f_out = PATH_TO_DATA / "geopd.csv"

    if not os.path.exists(path_f_in):
        logger.error(f"File passed as input doesn't exist: {path_f_in.f_in}")
        raise Exception()
    
    with open(path_f_in, "r") as f_in:
        nodes, edges, from_list, to_list = extract_graph(json.load(f_in))
        city_graph = nx.Graph(name=city)

        city_graph.add_nodes_from(nodes)
        city_graph.add_edges_from(edges)

        logger.info(f"Graph contains {city_graph.number_of_edges()} edges and {city_graph.number_of_nodes()} nodes")
        logger.info(f"Writing to file")

        df = geopd.GeoDataFrame(list(zip(from_list, to_list)), columns=["from", "to"])
        df.to_csv(path_f_out)
        logger.info(f"Done")