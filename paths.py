import json
from os import read


def read_json(jsonfile,graph):
    f= open(jsonfile, 'r')
    network_config = json.load(f)  
    for i in network_config:
        for nodelist in network_config[i].values():
            for node in nodelist:
                if i in graph:
                    graph[i].append(node)
                else:
                    graph[i] = [node]


def BFS_SP(graph, start, goal):
    explored = []
     
    # Queue for traversing the
    # graph in the BFS
    queue = [[start]]
     
    # If the desired node is
    # reached
    if start == goal:
        print("Same Node")
        return
     
    # Loop to traverse the graph
    # with the help of the queue
    while queue:
        path = queue.pop(0)
        node = path[-1]
         
        # Condition to check if the
        # current node is not visited
        if node not in explored:
            neighbours = graph[node]
             
            # Loop to iterate over the
            # neighbours of the node
            for neighbour in neighbours:
                new_path = list(path)
                new_path.append(neighbour)
                queue.append(new_path)
                 
                # Condition to check if the
                # neighbour node is the goal
                if neighbour == goal:
                    print("Shortest path = ", *new_path)
                    return new_path
            explored.append(node)
        
    # Condition when the nodes
    # are not connected
    print("So sorry, but a connecting"\
                "path doesn't exist :(")
    return
     

def initGraph():
    graph = {}

    read_json('networkconfigotim.json', graph)
    return graph
    

# src : string 
# dest : string 
# graph : dictionary
def shortest_path(src,dest, graph):

    list = BFS_SP(graph, src, dest)
    return list


# graph : dictionary
# nodes : List<String>
def removeNodes(graph, nodes):
    for node in nodes:

        if node in graph:
            graph.pop(node)

        for key, value in graph.items():
            if node in value:
                value.remove(node)
    

# graph : dictionary
# nodes : List<String>
def addNodes(graph, nodes):
    for node in nodes:
        f = open('networkconfigotim.json', 'r')
        network_config = json.load(f)
        
        for i in network_config:

            if i == node :
                graph[i] = []

                for nlist in network_config[i].values():
                    graph[i].append(nlist[0])
                    
                    if nlist[0] in graph:
                        if node not in graph[nlist[0]]:
                            graph[nlist[0]].append(node)
            
            else:
                for nlist in network_config[i].values():
                    if node in nlist:
                        if i in graph:
                            if node not in graph[i]:
                                graph[i].append(node)

              

        

#graph = initGraph()
#print(graph)
#print("------------------------------------------------------------------------")
#shortest_path("10.0.0.10","10.0.0.1", graph)
#removeNodes(graph,['10.0.3.20', '10.0.2.2', '10.0.4.20'])
#print(graph)
#print("------------------------------------------------------------------------")
#addNodes(graph,['10.0.2.2','10.0.4.20'])
#print(graph)
