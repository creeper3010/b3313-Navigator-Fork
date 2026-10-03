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
            path = navigate_forward_path(
                graph,
                startPoint=startingPoint,
                endPoint=endingPoint,
                avoidRNG=avoidRNG,
                avoidCaps=avoidCaps,
                avoidDeaths=avoidDeaths
            )
            print("\nDone! Follow the path below chronologically:")
            print("\n".join(path))
        except dijkstar.algorithm.NoPathError:
            print("Unable to find path.")

        print("\npress Ctrl C or close the window to exit. Otherwise, the program will now loop.")

def record_edge_candidate(edge_candidates, source, target, description, kind):

    if source == target:
        return

    key = (source, target)

    if key not in edge_candidates:
        edge_candidates[key] = {
            "two_way": None,
            "two_way_reverse": None,
            "leading_away": None,
            "leading_here": None,
        }

    if description and edge_candidates[key][kind] is None:
        edge_candidates[key][kind] = description


def resolve_edge_description(candidates):

    if candidates.get("leading_here"):
        return candidates["leading_here"]

    if candidates.get("leading_away"):
        return candidates["leading_away"]

    if candidates.get("two_way"):
        return candidates["two_way"]

    return candidates.get("two_way_reverse", "")


def _is_area_href(href):
    if not href or not href.startswith("/wiki/"):
        return False
    path_part = href[len("/wiki/"):]
    if ":" in path_part:
        return False
    skip_pages = {"List_of_Areas", "Main_Page", "Game_Features"}
    if any(path_part == s or path_part.startswith(s + "/") for s in skip_pages):
        return False
    return True


def _extract_name_links(item):
 
    text = item.get_text(" ", strip=True)
    if ":" not in text:
        return []

    name_part_text = text.split(":", 1)[0].strip()
    if not name_part_text:
        return []

    discovered = []
    for anchor in item.find_all("a"):
        a_href = anchor.get("href", "")
        a_text = (anchor.string or anchor.get_text() or anchor.get("title") or "").strip()
        if not a_text:
            continue

        if a_text not in name_part_text:
            continue

        if _is_area_href(a_href):
            canonical_title = anchor.get("title") or a_href[len("/wiki/"):].replace("_", " ")
            discovered.append((a_text, a_href, canonical_title))

    return discovered


def _valid_edge(s_node, t_node):
    if s_node == t_node:
        return False
    if s_node == "Sunken Castle" and "castle grounds" in t_node.lower():
        return False
    return True


def make_graph():
    stageExceptions = []
    stages = {}          
    scanned = set()      
    graph = nx.DiGraph()

    edge_candidates = {}

    with requests.Session() as sess:
        sess.headers.update({'User-Agent': 'B3313 Mapper'})

        print("Connecting to layout index page...")
        r1 = sess.get("https://b3313official.miraheze.org/wiki/List_of_Areas")
        tablesoup = BeautifulSoup(r1.content, 'html.parser')

        content_div = tablesoup.find("div", class_="mw-parser-output")
        search_root = content_div if content_div else tablesoup
        for anchor in search_root.find_all('a'):
            href = anchor.get('href')
            if not _is_area_href(href):
                continue

            name = anchor.string or anchor.get_text() or anchor.get('title') or ''
            name = str(name).strip()

            if name and name not in stages:
                stages[name] = str(href)

        if len(stages) == 0:
            print("Error: Unable to read any area links from the index page.")
            return graph

        print(f"Found {len(stages)} areas from index. Scanning warp pages (may discover more)...")

        scan_queue = list(stages.keys())
        scan_index = 0

        while scan_index < len(scan_queue):
            stage = scan_queue[scan_index]
            scan_index += 1

            if stage in scanned or str(stage) in stageExceptions:
                continue
            scanned.add(stage)

            # Progress display.
            total_so_far = len(scan_queue)
            current_index = scan_index
            percent = (current_index / total_so_far) * 100
            bar_length = 20
            filled_length = int(round(bar_length * current_index / float(total_so_far)))
            bar = '█' * filled_length + '░' * (bar_length - filled_length)

            display_name = stage if len(stage) <= 25 else stage[:22] + "..."
            sys.stdout.write(f"\rScanning: [{bar}] {percent:.1f}% ({current_index}/{total_so_far}) ({display_name:<25})")
            sys.stdout.flush()

            href_path = stages.get(stage)
            if not href_path:
                continue
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

            first_heading = warpsoup.find('h1', id='firstHeading')
            if first_heading:
                canonical_stage = first_heading.get_text(' ', strip=True)
            else:
                canonical_stage = stage

            for heading in warpsoup.find_all(["h2", "h3", "h4", "h5", "h6"]):
                headline = heading.find(class_="mw-headline")

                if headline:
                    heading_text = headline.get_text(" ", strip=True).lower()
                    heading_id = str(headline.get("id", "")).replace("_", " ").lower().strip()
                else:
                    heading_text = heading.get_text(" ", strip=True).lower()
                    heading_id = str(heading.get("id", "")).replace("_", " ").lower().strip()

                section = None

                if heading_text == "two-way" or heading_id == "two-way":
                    section = "two-way"
                elif heading_text == "leading here" or heading_id == "leading here":
                    section = "leading here"
                elif heading_text == "leading away" or heading_id == "leading away":
                    section = "leading away"

                if section is None:
                    continue

                container = None
                for next_element in heading.find_all_next():
                    if next_element.name in ["h2", "h3", "h4", "h5", "h6"]:
                        break
                    if next_element.name in ["ul", "ol", "table"]:
                        container = next_element
                        break

                if not container:
                    continue

                for item in container.find_all(["li", "tr"]):
                    text = item.get_text(" ", strip=True)
                    if ":" not in text:
                        continue

                    try:
                        name_part, desc_part = text.split(":", 1)
                        name_part = name_part.strip()
                        desc_part = desc_part.strip()
                    except ValueError:
                        continue

                    for discovered_name, discovered_href, canonical_title in _extract_name_links(item):
                        if discovered_name and discovered_name not in stages:
                            stages[discovered_name] = discovered_href
                            scan_queue.append(discovered_name)
                        if canonical_title and canonical_title not in stages:
                            stages[canonical_title] = discovered_href
                            scan_queue.append(canonical_title)

                    if section == "two-way":
                        for sub_name in name_part.split('/'):
                            sub_name = sub_name.strip()

                            if not _valid_edge(canonical_stage, sub_name):
                                continue

                            record_edge_candidate(
                                edge_candidates,
                                canonical_stage,
                                sub_name,
                                desc_part,
                                "two_way"
                            )

                            if _valid_edge(sub_name, canonical_stage):
                                record_edge_candidate(
                                    edge_candidates,
                                    sub_name,
                                    canonical_stage,
                                    desc_part,
                                    "two_way_reverse"
                                )

                    elif section == "leading here":
                        for sub_name in name_part.split('/'):
                            sub_name = sub_name.strip()

                            if _valid_edge(sub_name, canonical_stage):
                                
                                record_edge_candidate(
                                    edge_candidates,
                                    sub_name,
                                    canonical_stage,
                                    desc_part,
                                    "leading_here"
                                )

                    elif section == "leading away":
                        for sub_name in name_part.split('/'):
                            sub_name = sub_name.strip()

                            if _valid_edge(canonical_stage, sub_name):
                               
                                record_edge_candidate(
                                    edge_candidates,
                                    canonical_stage,
                                    sub_name,
                                    desc_part,
                                    "leading_away"
                                )

        for (source, target), candidates in edge_candidates.items():
            description = resolve_edge_description(candidates)

            graph.add_edge(
                source,
                target,
                weight=1,
                desc=description
            )

        sys.stdout.write("\n")
        print(f"Discovery complete. Scanned {len(scanned)} pages total.")
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

    raw_path = dijkstar.find_path(
        navgraph,
        startPoint,
        endPoint,
        cost_func=lambda u,v,e,p: 1
    )

    forward_instructions = []
    node_sequence = raw_path.nodes

    for i in range(len(node_sequence) - 1):
        current_node = node_sequence[i]
        next_node = node_sequence[i+1]

        warp_description = drawGraph.get_edge_data(current_node, next_node)['desc']
        forward_instructions.append(
            f"From [{current_node}] to [{next_node}]: {warp_description}"
        )

    return forward_instructions

if __name__ == "__main__":
    main()
