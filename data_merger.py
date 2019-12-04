import os
import sys
import json
from path import Path
import networkx as nx
from collections import defaultdict
import geopandas as geopd
import pandas as pd
from geopandas import GeoDataFrame
import fiona
import numpy as np
import json
import ast
from util import *
from graph_constructor import extract_graph

logger = setup_logging()


def has_node_with_title(nodes, title):
    for node in nodes:
        if node.title == title:
            return True
    return False


def add_id(json_array, nodes):
    table = dict()
    for i, attraction in enumerate(json_array, 1):
        attraction["id"] = i
        if attraction["wikipedia_page"] == 1 and has_node_with_title(nodes, attraction["wikipedia_title"]):
            table[attraction["wikipedia_title"]] = i
    
    return table


def add_places_id_encoded(places, json_array, title_to_id_table):
    # todo: implement
    pass


def add_topics_id_encoded(places, json_array, title_to_id_table):
    # todo: implement
    pass


def add_connected_places(json_array, graph, title_to_id_table):
    for attraction in json_array:
        connected_places = graph[attraction]

        attraction["links_places"] = add_places_id_encoded(connected_places, json_array, title_to_id_table)

def add_connected_topics(json_array, info, title_to_id_table):
    for attraction in json_array:
        connected_topics = None

        attraction["links_topics"] = add_topics_id_encoded(connected_topics, title_to_id_table)


if __name__ == "__main__":
    args = setup_argparser().parse_args()
    city = args.city
    logger.info(f"Got arguments: {args}")

    PATH_TO_DATA = Path(f"data/{city}")
    path_f_in = PATH_TO_DATA / "{city}-finilized.json"
    path_f_info = PATH_TO_DATA / "attractions.json"
    path_f_out = PATH_TO_DATA / "finilized.json"

    if not os.path.exists(path_f_in):
        logger.error(f"File passed as input doesn't exist: {path_f_in}")
        raise Exception()

    if not os.path.exists(path_f_info):
        logger.error(f"File passed as additional information doesn't exist: {path_f_info}")
        raise Exception()
    
    with open(path_f_in, "r") as f_in, open(path_f_out, "r") as f_info:
        in_json = json.load(f_in)
        logger.info(f"Loaded input file: {in_json}")

        info_json = json.load(f_info)
        logger.info(f"Loaded info file: {info_json}")

        nodes, edges, from_list, to_list = extract_graph(json.load(f_info))
        city_graph = nx.Graph(name=city)
        city_graph.add_nodes_from(nodes)
        city_graph.add_edges_from(edges)
        logger.info(f"Graph contains {city_graph.number_of_edges()} edges and {city_graph.number_of_nodes()} nodes")
        
        title_to_id_table = add_id(in_json, nodes)
        logger.info(f"Added id to initial json")

        add_connected_places(in_json, from_list, title_to_id_table)

        # add_connected_topics(in_json, info)
        
    logger.info(f"Done")