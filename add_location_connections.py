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

logger = setup_logging()

def has_node_with_title(nodes, title):
    for node in nodes:
        if node.title == title:
            return True
    return False


def find_node(nodes, title):
    for node in nodes:
        if node.title == title:
            return node
    return None


def add_id(attractions, nodes, title_to_nodes):
    title_to_id = dict()
    id_to_title = dict()
    for i, attraction in enumerate(attractions):
        attraction["id"] = i + 1
        title = attraction["wikipedia_title"]

        if title in title_to_nodes:
            node = nodes[title_to_nodes[title]]
            title_to_id[title] = i
            id_to_title[i] = title
            attraction["wikipedia_page_id"] = node.pageid
    
    return title_to_id, id_to_title


def add_connected_places(attractions, city_graph, title_to_id_table, attraction_to_node, nodes):
    for i, attraction in enumerate(attractions):
        title = attraction["title"]

        if title not in title_to_id_table or i not in attraction_to_node:
            continue
        
        node = nodes[attraction_to_node[i]]
        connected_topics = city_graph[node]

        links = []
        for place in connected_topics:
            title = place.title
            if title in title_to_id_table:
                    links.append(title_to_id_table[title])
        
        attraction["links_location_id"] = links
        attraction["links_from"] = len(node.links_from)
        attraction["links_to"] = node.links_to


def extract_graph(json):
    attractions = []
    table = dict()

    for obj in json:
        try:
            origin = Attraction(obj)
            table[origin.title] = origin
            attractions.append(origin)
        except Exception as e:
            pass
 
    graph = defaultdict(list)
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
                graph[attraction.title]
        
    for title, attraction in table.items():
        attraction.links_to = pagerank_table[title]
    
    return attractions, edges


def find_mapping(attractions, nodes):
    titles_attractions = set()
    title_to_index_attractions = dict()
    for i, attraction in enumerate(attractions):
        title_to_index_attractions[attraction["wikipedia_title"]] = i
        titles_attractions.add(attraction["wikipedia_title"])

    
    titles_nodes = set()
    title_to_index_nodes = dict()
    for i, node in enumerate(nodes):
        title_to_index_nodes[node.title] = i
        titles_nodes.add(node.title)

    common_titles = titles_attractions.intersection(titles_nodes)
    mapping_to_nodes = dict()
    mapping_to_attractions = dict()
    title_to_nodes = dict()
    title_to_attractions = dict()
    for title in common_titles:
        attraction_index = title_to_index_attractions[title]
        nodes_index = title_to_index_nodes[title]
        mapping_to_attractions[nodes_index] = attraction_index
        mapping_to_nodes[attraction_index] = nodes_index
        title_to_nodes[title] = nodes_index
        title_to_attractions[title] = attraction_index

    return mapping_to_attractions, mapping_to_nodes, title_to_attractions, title_to_nodes


if __name__ == "__main__":
    args = setup_argparser().parse_args()
    city = args.city
    logger = setup_logging(city)
    logger.info(f"Got arguments: {args}")

    PATH_TO_DATA = Path(f"data/{city}")
    path_f_in = PATH_TO_DATA / f"{city}-finalized.json"
    path_f_info = PATH_TO_DATA / "attractions.json"
    path_f_out = PATH_TO_DATA / "finilized.json"

    if not os.path.exists(path_f_in):
        logger.error(f"File passed as input doesn't exist: {path_f_in}")
        raise Exception()

    if not os.path.exists(path_f_info):
        logger.error(f"File passed as additional information doesn't exist: {path_f_info}")
        raise Exception()
    
    with open(path_f_in, "r") as f_in, open(path_f_info, "r") as f_info, open(path_f_out, "w") as f_out:
        json_in = json.load(f_in)
        logger.info(f"Loaded input file")

        attractions_wiki = json.load(f_info)
        logger.info(f"Loaded info file")

        nodes, edges = extract_graph(attractions_wiki)
        city_graph = nx.Graph(name=city)
        city_graph.add_nodes_from(nodes)
        city_graph.add_edges_from(edges)
        logger.info(f"Graph contains {city_graph.number_of_edges()} edges and {city_graph.number_of_nodes()} nodes")

        node_to_attractions, attraction_to_nodes, title_to_attractions, title_to_nodes = find_mapping(json_in, nodes)

        title_to_id_table, id_to_title_table = add_id(json_in, nodes, title_to_nodes)
        logger.info(f"Added id to initial json")

        add_connected_places(json_in, city_graph, title_to_id_table, attraction_to_nodes, nodes)
        logger.info(f"Added connected places")

        logger.info(f"Writing down results")
        f_out.write(json.dumps(json_in))
        
    logger.info(f"Done")