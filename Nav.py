import networkx as nx
import pylab
import sys 
try:
    import regex as re
except:
    import re

from bs4 import BeautifulSoup
from pathlib import Path
import requests
import random
import pickle
import dijkstar
import time

def main():
    doDraw = input("Draw map? Warning, will be pretty incomprehensible. (y/n): ").lower() == 'y'
    if Path("map").is_file():
        graph = get_graph()
        print(f"Loaded database map successfully with {len(graph.edges())} connections!")
    else:
        print("No map detected. Generating one now from https://b3313official.miraheze.org/wiki/List_of_Areas")
        graph = make_graph()
        save_graph(graph)

    if doDraw:
        draw_graph(graph)

    while True:
        startingPoint = input("\nStart Stage (Case sensitive! e.g., 'Castle Grounds'): ").strip()
        endingPoint = input("Goal Stage (Case sensitive! e.g., 'Vanilla Lobby'): ").strip()
        
        if startingPoint not in graph:
            print(f"Error: '{startingPoint}' is not recognized in the database.")
            continue
        if endingPoint not in graph:
            print(f"Error: '{endingPoint}' is not recognized in the database.")
            continue
            
        avoidRNG = input("avoid RNG?(y/n): ").lower() == 'y'
        avoidDeaths = input("avoid necessary deaths?(y/n): ").lower() == 'y'
        avoidCaps = input("avoid Caps?(y/n): ").lower() == 'y'
        print("Finding path...")

        try:
            path = navigate_forward_path(graph, startPoint=startingPoint, endPoint=endingPoint, avoidRNG=avoidRNG, avoidCaps=avoidCaps, avoidDeaths=avoidDeaths)
            print("\nDone! Follow the path below chronologically:")
            print("\n".join(path))
        except dijkstar.algorithm.NoPathError:
            print("Unable to find path.")

        print("\npress Ctrl C or close the window to exit. Otherwise, the program will now loop.")

def make_graph():
    stageExceptions = []
    stages = {}
    graph = nx.DiGraph()

    with requests.Session() as sess:
        sess.headers.update({'User-Agent': 'B3313 Mapper'})
        
        print("Connecting to layout index page...")
        r1 = sess.get("https://b3313official.miraheze.org/wiki/List_of_Areas")
        tablesoup = BeautifulSoup(r1.content, 'html.parser')
        
        # FIXED INDEX READ LOGIC: Pulls textual data securely from tables using fallback evaluation
        for table in tablesoup.find_all("table"):
            for anchor in table.find_all('a'):
                href = anchor.get('href')
                if href and href.startswith("/wiki/") and ":" not in href:
                    if "List_of_Areas" in href or "Main_Page" in href:
                        continue
                    
                    # Uses text reading methods to ensure it doesn't fail on complex table chains
                    name = anchor.string or anchor.get_text() or anchor.get('title') or ''
                    name = str(name).strip()
                    
                    if name and name not in stages:
                        stages[name] = str(href)
        
        total_stages = len(stages)
        if total_stages == 0:
            print("Error: Still unable to read index formatting via session tables.")
            return graph
            
        print(f"Found {total_stages} areas to scan. Parsing individual warp routes...")
        
        for idx, stage in enumerate(list(stages.keys())):
            if str(stage) in stageExceptions:
                continue

            current_index = idx + 1
            percent = (current_index / total_stages) * 100
            bar_length = 20
            filled_length = int(round(bar_length * current_index / float(total_stages)))
            bar = '█' * filled_length + '░' * (bar_length - filled_length)
            
            display_name = stage if len(stage) <= 25 else stage[:22] + "..."
            sys.stdout.write(f"\rScanning: [{bar}] {percent:.1f}% Complete ({display_name:<25})")
            sys.stdout.flush()

            href_path = stages[stage]
            if href_path.startswith("http"):
                stage_url = href_path
            else:
                stage_url = f"https://b3313official.miraheze.org{href_path}"

            try:
                time.sleep(0.04)
                r2 = sess.get(stage_url)
                if r2.status_code != 200:
                    continue
                warpsoup = BeautifulSoup(r2.content, 'html.parser')
            except Exception:
                continue

            for heading in warpsoup.find_all(["span", "h2", "h3"]):
                heading_id = heading.get('id', '').lower()
                heading_text = heading.get_text().lower()
                
                is_two_way = "two-way" in heading_id or "two-way" in heading_text
                is_lead_here = "here" in heading_id or "here" in heading_text
                is_lead_away = "away" in heading_id or "away" in heading_text or "connections" in heading_text or "warps" in heading_text

                if not (is_two_way or is_lead_here or is_lead_away):
                    continue

                sibling = heading.find_parent() if heading.name == "span" else heading
                container = sibling.find_next(["ul", "ol", "table"])
                if not container:
                    continue

                for item in container.find_all(["li", "tr"]):
                    text = item.get_text()
                    if ":" not in text:
                        continue
                    
                    try:
                        name_part, desc_part = text.split(":", 1)
                        name_part = name_part.strip()
                        desc_part = desc_part.strip()
                    except ValueError:
                        continue

                    def valid_edge(s_node, t_node):
                        if s_node == t_node:
                            return False
                        if s_node == "Sunken Castle" and "castle grounds" in t_node.lower():
                            return False
                        return True

                    if is_two_way:
                        for sub_name in name_part.split('/'):
                            sub_name = sub_name.strip()
                            if valid_edge(stage, sub_name) and valid_edge(sub_name, stage):
                                graph.add_edge(stage, sub_name, weight=1, desc=desc_part)
                                graph.add_edge(sub_name, stage, weight=1, desc=desc_part)
                    elif is_lead_here:
                        for sub_name in name_part.split('/'):
                            sub_name = sub_name.strip()
                            if valid_edge(sub_name, stage):
                                graph.add_edge(sub_name, stage, weight=1, desc=desc_part)
                    elif is_lead_away:
                        for sub_name in name_part.split('/'):
                            sub_name = sub_name.strip()
                            if valid_edge(stage, sub_name):
                                graph.add_edge(stage, sub_name, weight=1, desc=desc_part)

        sys.stdout.write("\n")
        return graph

def save_graph(graph:nx.DiGraph):
    with open("map", 'wb') as graphFile:
        pickle.dump(graph, graphFile)
    print(f"Success! Built database with {len(graph.edges())} total connections.")

def get_graph():
    with open("map", 'rb') as graphFile:
        return pickle.load(graphFile)

def draw_graph(graph:nx.DiGraph):
    pos = {}
    colors = []
    cnt = 0
    for n in graph:
        pos[n] = ((cnt / 10) * 100,(cnt % 10) * 5)
        colors.append(random.choice('rgbywkc'))
        cnt += 1
    nx.draw(graph,with_labels=True,pos=nx.draw_shell(graph),width=1,edge_color=colors,node_size=100,font_size=10)
    pylab.show()

def navigate_forward_path(drawGraph:nx.DiGraph, startPoint:str, endPoint:str, avoidRNG=False, avoidCaps=False, avoidDeaths=False):
    navgraph = dijkstar.Graph(undirected=False)

    for edge in drawGraph.edges():
        u, v = edge
        edge_data = drawGraph.get_edge_data(u, v)
        desc = edge_data.get('desc', '').lower()
        
        skip = False
        if avoidRNG and "random" in desc:
            skip = True
        if avoidCaps and any(cap in desc for cap in ["vanish cap", "metal cap", "wing cap", "fly"]):
            skip = True
        if avoidDeaths and "die" in desc:
            skip = True
            
        if not skip:
            navgraph.add_edge(u, v, edge_data['desc'])

    raw_path = dijkstar.find_path(navgraph, startPoint, endPoint, cost_func=lambda u,v,e,p: 1)
    
    forward_instructions = []
    node_sequence = raw_path.nodes
    
    for i in range(len(node_sequence) - 1):
        current_node = node_sequence[i]
        next_node = node_sequence[i+1]
        
        warp_description = drawGraph.get_edge_data(current_node, next_node)['desc']
        forward_instructions.append(f"From [{current_node}] to [{next_node}]: {warp_description}")
        
    return forward_instructions

if __name__ == "__main__":
    main()
