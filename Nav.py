import networkx as nx
import pylab
try:
    import regex as re
except:
    import re

from bs4 import BeautifulSoup
from pathlib import Path

import requests, random, pylab, pickle, dijkstar

def main():
    doDraw = input("Draw map? Warning, will be pretty incomprehensible. (y/n): ").lower() == 'y'
    if Path("map").is_file():
        graph = get_graph()
    else:
        print("No map detected. Generating one now from https://b3313official.miraheze.org/wiki/List_of_Areas")
        graph = make_graph()
        save_graph(graph)


    if doDraw:
        draw_graph(graph)

    while True:
        startingPoint = input("Start Stage(Stage name, such as 'Castle Grounds' without quotations. Warning: is case sensitive!!!): ")
        endingPoint = input("Goal Stage(Stage name, such as 'Castle Grounds' without quotations. Warning: is case sensitive!!!): ")
        avoidRNG = input("avoid RNG?(y/n): ").lower() == 'y'
        avoidDeaths = input("avoid necessary deaths?(y/n): ").lower() == 'y'
        avoidCaps = input("avoid Caps?(y/n): ").lower() == 'y'
        print("Finding path...")

        try:
            path = navigate_graph(graph,startPoint=startingPoint,endPoint=endingPoint,avoidRNG=avoidRNG, avoidCaps=avoidCaps,avoidDeaths=avoidDeaths)
            print("Done! Follow the path below:")
            print("\n".join(path.edges))
        except dijkstar.algorithm.NoPathError:
            print("Unable to find path.")

        print("press Ctrl C or close the window to exit. Otherwise, the program will now loop.")

    
    


def make_graph():
    stageExceptions = []
    stages = {}
    graph = nx.DiGraph()

    with requests.Session() as sess:
        
        #r1 = sess.get("https://b3313.fandom.com/wiki/List_of_Areas")
        r1 = sess.get("https://b3313official.miraheze.org/wiki/List_of_Areas",headers={'User-Agent': 'B3313 Mapper'})
        tablesoup = BeautifulSoup(r1.content, 'html.parser')
        
        #Official
        table = tablesoup.find_all("table")[1].find_all('a')

        for s in table:
            stages[str(s.string)] = str(s['href'])
        
        for stage in stages:

            ### TEST LINE ###
            #if str(stage) != 'Star Road' and str(stage) != 'World of Dreams':
            #    continue


            if str(stage) in stageExceptions:
                continue

            print("Retrieving " + str("".join(["https://b3313official.miraheze.org",stages[stage]])))
            r2 = sess.get("".join(["https://b3313official.miraheze.org",stages[stage]]),headers={'User-Agent': 'B3313 Mapper'})

            warpsoup = BeautifulSoup(r2.content, 'html.parser')

            #Two Ways
            #Treat same as leading away, will happen twice anyway
            twoWaySpan = warpsoup.find("span",id="Two-way")

            if twoWaySpan:
                for twoway in twoWaySpan.find_next("ul").find_all("li"):
                    nameMatch = re.search(r'.*:', twoway.text)
                    descMatch = re.search(r': .*', twoway.text)
                    if nameMatch == None or descMatch == None:
                        break
                    print("adding two-way edge " + nameMatch.group(0)[:-1])
                    graph.add_edge(stage,nameMatch.group(0)[:-1],weight=1, desc=descMatch.group(0)[2:])

            
            twoWaySpan = warpsoup.find("span",id="Two-way_2")

            if twoWaySpan:
                for twoway in twoWaySpan.find_next("ul").find_all("li"):
                    nameMatch = re.search(r'.*:', twoway.text)
                    descMatch = re.search(r': .*', twoway.text)
                    if nameMatch == None or descMatch == None:
                        break
                    print("adding two-way edge " + nameMatch.group(0)[:-1])
                    graph.add_edge(stage,nameMatch.group(0)[:-1],weight=1, desc=descMatch.group(0)[2:])


            #Leading Here
            leadHereSpan = warpsoup.find("span",id="Leading_Here")

            if leadHereSpan:
                for leadhere in leadHereSpan.find_next("ul").find_all("li"):
                    nameMatch = re.search(r'.*:', leadhere.text)
                    descMatch = re.search(r': .*', leadhere.text)
                    if nameMatch == None or descMatch == None:
                        break

                    for stageName in nameMatch.group(0)[:-1].split('/'):
                        print("adding leading here edge " + stageName)
                        graph.add_edge(stageName,stage,weight=1, desc=descMatch.group(0)[2:])

            
            leadHereSpan = warpsoup.find("span",id="Leading_Here_2")

            if leadHereSpan:
                for leadhere in leadHereSpan.find_next("ul").find_all("li"):
                    nameMatch = re.search(r'.*:', leadhere.text)
                    descMatch = re.search(r': .*', leadhere.text)
                    if nameMatch == None or descMatch == None:
                        break

                    for stageName in nameMatch.group(0)[:-1].split('/'):
                        print("adding leading here edge " + stageName)
                        graph.add_edge(stageName,stage,weight=1, desc=descMatch.group(0)[2:])


            #Leading Away
            leadAwaySpan = warpsoup.find("span",id="Leading_Away")

            if leadAwaySpan:
                for leadaway in leadAwaySpan.find_next("ul").find_all("li"):
                    nameMatch = re.search(r'.*:', leadaway.text)
                    descMatch = re.search(r': .*', leadaway.text)
                    if nameMatch == None or descMatch == None:
                        break
                    print("adding leading away edge " + nameMatch.group(0)[:-1])
                    graph.add_edge(stage,nameMatch.group(0)[:-1],weight=1, desc=descMatch.group(0)[2:])
            

            leadAwaySpan = warpsoup.find("span",id="Leading_Away_2")

            if leadAwaySpan:
                for leadaway in leadAwaySpan.find_next("ul").find_all("li"):
                    nameMatch = re.search(r'.*:', leadaway.text)
                    descMatch = re.search(r': .*', leadaway.text)
                    if nameMatch == None or descMatch == None:
                        break
                    print("adding leading away edge " + nameMatch.group(0)[:-1])
                    graph.add_edge(stage,nameMatch.group(0)[:-1],weight=1, desc=descMatch.group(0)[2:])

        return graph
    

def save_graph(graph:nx.DiGraph):
    graphFile = open("map",'wb')
    pickle.dump(graph,graphFile)
    graphFile.close()

def get_graph():
    graphFile = open("map",'rb')
    graph:nx.DiGraph = None
    graph = pickle.load(graphFile)
    graphFile.close()
    return graph

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

def navigate_graph(drawGraph:nx.DiGraph,startPoint:str, endPoint:str,avoidRNG=False,avoidCaps=False,avoidDeaths=False):

    navgraph = dijkstar.Graph(undirected=False)

    for edge in drawGraph.edges():
        if not ((avoidRNG and ("random" in drawGraph.get_edge_data(edge[0],edge[1])['desc'].lower())) or (avoidCaps and (("vanish cap" in drawGraph.get_edge_data(edge[0],edge[1])['desc'].lower()) or ("metal cap" in drawGraph.get_edge_data(edge[0],edge[1])['desc'].lower()) or ("wing cap" in drawGraph.get_edge_data(edge[0],edge[1])['desc'].lower()) or ("fly" in drawGraph.get_edge_data(edge[0],edge[1])['desc'].lower()))) or (avoidDeaths and ("die" in drawGraph.get_edge_data(edge[0],edge[1])['desc'].lower()))):
            navgraph.add_edge(edge[0],edge[1],drawGraph.get_edge_data(edge[0],edge[1])['desc'])

    return dijkstar.find_path(navgraph,startPoint,endPoint,cost_func=cost_func)

def cost_func(u, v, edge, prev_edge):
    return 1

if __name__ == "__main__":
    main()
