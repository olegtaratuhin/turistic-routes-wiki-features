import pandas as pd
from geopandas import GeoDataFrame
from shapely.geometry import Point, LineString
import fiona
import numpy as np
import json
import ast
from matplotlib import pyplot as plt
import folium
from folium import Marker, Map, PolyLine
import osmnx as ox
import os
import sys
from path import Path
from collections import defaultdict
from util import *

cities_locations = {
    "Kaliningrad": {
        "center": [54.7101280, 20.5105838],
        "zoom": 11
    },
    "Kazan": {
        "center": [55.87, 48.59],
        "zoom": 10
    },
    "Moscow": {
        "center": [55.75, 37.61],
        "zoom": 9
    },
    "Nizhniy_Novgorod": {
        "center": [56.29, 44.93],
        "zoom": 10
    },
    "Rostov_On_Don": {
        "center": [47.23, 39.70],
        "zoom": 10
    },
    "Saint_Petersburg": {
        "center": [59.93, 30.33],
        "zoom": 9
    },
    "Samara": {
        "center": [53.24, 50.22],
        "zoom": 10
    },
    "Saransk": {
        "center": [54.20, 45.17],
        "zoom": 10
    },
    "Sochi": {
        "center": [43.60, 39.73],
        "zoom": 10
    },
    "Volgograd": {
        "center": [48.70, 44.51],
        "zoom": 10
    },
    "Yekaterinburg": {
        "center": [56.83, 60.60],
        "zoom": 10
    }
}


logger = setup_logging()

def transform_from_json(row):
    obj = json.loads(row)
    coord = ast.literal_eval(obj["coordinates"])
    
    return pd.Series((obj["title"], coord, obj["links_to"]))

def transform_df(df):
    df[["from_title", "from_point", "from_weight"]] = df["from"].apply(transform_from_json)
    df[["to_title", "to_point", "to_weight"]] = df["to"].apply(transform_from_json)
    df.drop(columns=["from", "to"], inplace=True)

    return df

def conscruct_initial_map(city: str) -> Map:
    return Map(location=cities_locations[city]["center"],
        zoom_start=cities_locations[city]["zoom"],
        control_scale=True)

def cache_locations(df):
    colors = [
            'red', 'blue', 'green', 'purple', 'orange', 'darkred', 'lightred',
            'beige', 'darkblue', 'darkgreen', 'cadetblue', 'darkpurple', 'white',
            'pink', 'lightblue', 'lightgreen', 'gray', 'black', 'lightgray']
    modulo = len(colors)

    locations_table = {}
    for i, location in df[["from_title", "from_point"]].iterrows():
        
        if location.from_title in locations_table:
            continue

        locations_table[location.from_title] = {
            "color": colors[i % modulo],
            "coord": location.from_point[::-1]
        }
    return locations_table

def add_lines(df, map, locations_table):
    sorted_by_pagerank = df.sort_values(by=["to_weight"], ascending=False)

    max_lines = 1.0 * len(df)
    normalizing_coef = df["to_weight"].values.max()
    opacity = 0.75

    for i, row in sorted_by_pagerank.iterrows():
        start = row.from_point[::-1]
        finish = row.to_point[::-1]
        weight = abs(0.5 - row.to_weight / normalizing_coef)
        title = row.from_title
        
        if i == max_lines:
            break
            
        line = PolyLine((start, finish),
                        opacity=opacity,
                        weight=weight,
                        color=locations_table[title]["color"]).add_to(map)

def add_markers(df, map, locations_table):
    for title, loc in locations_table.items():
        Marker(location=loc["coord"],
               popup=title,
               icon=folium.Icon(color=loc["color"])).add_to(m)

if __name__ == "__main__":
    args = setup_argparser().parse_args()
    city = args.city
    logger.info(f"Got arguments: {args}")

    PATH_TO_DATA = Path(f"data/{city}")
    path_f_in = PATH_TO_DATA / "geopd.csv"
    path_f_out = PATH_TO_DATA / "map.html"

    if not os.path.exists(path_f_in):
        logger.error(f"File passed as input doesn't exist: {path_f_in}")
        raise Exception()
    
    with open(path_f_in, "r") as f_in:
        df = transform_df(pd.read_csv(path_f_in, index_col=0))

        m = conscruct_initial_map(city)
        logger.info(f"Initial map is constructed")

        locations_table = cache_locations(df)
        logger.info(f"Locations are cached, cache size: {len(locations_table)}")
        
        add_lines(df, m, locations_table)
        logger.info(f"Added lines to map")
        
        add_markers(df, m, locations_table)
        logger.info(f"Added markers to map")
        
        m.save(path_f_out)
        
        logger.info(f"Done")