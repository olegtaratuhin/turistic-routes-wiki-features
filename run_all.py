import shutil
import os
from argparse import ArgumentParser
import subprocess
import asyncio

cities = [
    "Kaliningrad",
    "Kazan",
    "Moscow",
    "Nizhniy_Novgorod",
    "Rostov_On_Don",
    "Saint_Petersburg",
    "Samara",
    "Saransk",
    "Sochi",
    "Volgograd",
    "Yekaterinburg"
]

async def run_on_single_city(city, command):
    subprocess.run(f"python {command} {city}")

async def run_on_every_city(command):
    tasks = (run_on_single_city(city, command) for city in cities)
    asyncio.gather(*tasks)

if __name__ == "__main__":
    parser = ArgumentParser(description="Launch given command for all cities")
    parser.add_argument("command", type=str, help="Path to clu")
    
    args = parser.parse_args()
    command = args.command

    asyncio.run(run_on_every_city(command))
