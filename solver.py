import networkx as nx
from parse import read_input_file, write_output_file
from utils import is_valid_solution, calculate_score
import sys
from os.path import basename, normpath
import glob
from fibheap import *

class GraphNode(Node):
    def __init__(self, key, p=None, left=None, right=None,
                 child=None, mark = None):
        self.value = key[1]
        super().__init__(key[0], p, left, right, child, mark)


#modified version which returns all minimum paths?
#definitely need both vertex AND edge paths
#remember s is always 0 and t is always max vertex
def dijkstra(G, s = 0):
    dist = {}
    prev = {}
    # since python numbers are unbounded, this caps the
    # max value at something higher and ensures Dijkstra works
    max_val = 100 * len(G.nodes)
    for v in G.nodes:
        dist[v] = max_val
    dist[s] = 0
    q = makefheap()
    # keep dictionary of fib nodes for decreasekey
    fib_nodes = {}
    for v in dist.keys():
        fib_nodes[v] = GraphNode((dist[v], v))
        q.insert(fib_nodes[v])
    while q.num_nodes:
        node = q.extract_min()
        u = node.value
        for v in G.adj[u]:
            last_dist = dist[v]
            dist[v] = min(dist[v], dist[u] + G[u][v]['weight'])
            if dist[v] < last_dist:
                q.decrease_key(fib_nodes[v], dist[v])
                prev[v] = u
    return dist, prev

def explore(G, v, visited):
    visited[v] = True
    for u in G.adj[v]:
        if not visited[u]:
            explore(G, u, visited)

def connected(G):
    visited = {}
    for v in G.nodes:
        visited[v] = False
    explore(G, 0, visited)
    for v in visited.values():
        if not v:
            return False
    return True 

#measures total weight of edges summed 
def weight(G, v):
    w = 0
    for u in G.adj[v]:
        w += G[v][u]['weight']
    return w

#method to get shortest nodes from prev
def shortest_path(G, prev):
    t = max(G.nodes)
    path = [t]
    while t != 0:
        path.append(prev[t])
        t = prev[t]
    return path

#termination should happen only if all nodes disconnect, otherwise continue
#in the case that the new shortest path allows us to remove more edges
def smart_greedy(G):
    G_node = G.copy()
    if len(G.nodes) <= 30:
        k = 15
        c = 1
    elif len(G.nodes) <= 50:
        k = 50
        c = 3
    else:
        k = 100
        c = 5
    start_d, start_p = dijkstra(G)
    starting_shortest = shortest_path(G, start_p)
    print("starting dist:", start_d[max(G_node.nodes)])

    shortest = starting_shortest[1:len(starting_shortest) - 1]
    nf_nodes, shortest, d, p = cut_nodes(G_node, shortest, start_d, start_p, c)
    nf_edges, shortest, d, p = cut_edges(G_node, shortest, d, p, k)
    node_first = d[max(G.nodes)]

    ef_edges, shortest, d, p = cut_edges(G, starting_shortest, start_d, start_p, k)
    shortest = shortest[1:len(shortest) - 1]
    ef_nodes, shortest, d, p = cut_nodes(G, shortest, d, p, c)
    edge_first = d[max(G.nodes)]

    if node_first > edge_first:
        result = node_first
        nodes = nf_nodes
        edges = nf_edges
    else:
        result = edge_first
        nodes = ef_nodes
        edges = ef_edges
    print("resulting dist:", result)
    #print("nodes:", nodes)
    #print("edges:", edges)
    return nodes, edges

def mixed_greedy(G):
    if len(G.nodes) <= 30:
        k = 15
        c = 1
    elif len(G.nodes) <= 50:
        k = 50
        c = 3
    else:
        k = 100
        c = 5
    d, p = dijkstra(G)
    shortest = shortest_path(G, p)
    print("starting dist:", d[max(G.nodes)])
    nodes, edges, shortest, d, p = cut_both(G, shortest, d, p, k, c)
    print("resulting dist:", d[max(G.nodes)])
    return nodes, edges

def cut_edges(G, shortest, d, p, k):
    t = max(G.nodes)
    original = d[t]
    #print(shortest)
    edges = []
    while k > 0:
        #print(k)
        max_increase = 0
        curr_dist = d[t]
        first_connected = None
        for i in range(len(shortest) - 1, 0, -1) :
            u = shortest[i]
            v = shortest[i - 1]
            w = G[u][v]['weight']
            G.remove_edge(u, v)
            if not connected(G):
                G.add_edge(u, v, weight=w)
                continue
            candidate_d, candidate_p = dijkstra(G)
            if not first_connected:
                first_connected = (u, v)
                first_d, first_p = candidate_d, candidate_p
            if candidate_d[t] - curr_dist > max_increase:
                best_d, best_p = candidate_d, candidate_p
                e = (u, v)
                max_increase = candidate_d[t] - curr_dist
            G.add_edge(u, v, weight=w)
        if max_increase > 0:
            edges.append(e)
            G.remove_edge(e[0], e[1])
            d, p = best_d, best_p
            shortest = shortest_path(G, p)
            k -= 1
        elif first_connected:
            edges.append(first_connected)
            G.remove_edge(first_connected[0], first_connected[1])
            d, p = first_d, first_p
            shortest = shortest_path(G, first_p)
            k -= 1
        else:
            break
    #print(original, d[t])
    #print(edges)
    #print(shortest)
    return edges, shortest, d, p

def cut_nodes(G, shortest, d, p, c):
    t = max(G.nodes)
    original = d[t]
    #print(shortest)
    nodes = []
    while c > 0:
        #print(k)
        max_increase = 0
        curr_dist = d[t]
        first_connected = None
        for i in range(len(shortest) - 1, -1, -1):
            u = shortest[i]
            removed_edges = []
            for v in G.adj[u]:
                w = G[u][v]['weight']
                removed_edges.append((u, v, w))
            G.remove_node(u)
            if not connected(G):
                G.add_node(u)
                for e in removed_edges:
                    G.add_edge(e[0], e[1], weight=e[2])
                continue
            candidate_d, candidate_p = dijkstra(G)
            if not first_connected:
                first_connected = u
                first_d, first_p = candidate_d, candidate_p
            if candidate_d[t] - curr_dist > max_increase:
                best_d, best_p = candidate_d, candidate_p
                best_node = u
                max_increase = candidate_d[t] - curr_dist
            G.add_node(u)
            for e in removed_edges:
                G.add_edge(e[0], e[1], weight=e[2])
        if max_increase > 0:
            nodes.append(best_node)
            G.remove_node(best_node)
            d, p = best_d, best_p
            shortest = shortest_path(G, p)
            shortest = shortest[1:len(shortest) - 1]
            c -= 1
        elif first_connected:
            nodes.append(first_connected)
            G.remove_node(first_connected)
            d, p = first_d, first_p
            shortest = shortest_path(G, first_p)
            shortest = shortest[1:len(shortest) - 1]
            c -= 1
        else:
            break
    shortest.insert(0, t)
    shortest.append(0)
    #print(original, d[t])
    #print(nodes)
    #print(shortest)
    return nodes, shortest, d, p

def cut_both(G, shortest, d, p, k, c):
    t = max(G.nodes)
    original = d[t]
    #print(shortest)
    edges = []
    nodes = []
    while k > 0 or c > 0:
        #print(k, c)
        #print(G.nodes)
        #print(edges)
        max_increase = 0
        edge_inc = -1
        node_inc = -1
        curr_dist = d[t]
        first_connected_e = None
        first_index = 1000
        if k > 0:
            for i in range(len(shortest) - 1, 0, -1) :
                u = shortest[i]
                v = shortest[i - 1]
                #print(u, v)
                w = G[u][v]['weight']
                G.remove_edge(u, v)
                if not connected(G):
                    G.add_edge(u, v, weight=w)
                    continue
                candidate_d, candidate_p = dijkstra(G)
                if not first_connected_e:
                    first_connected_e = (u, v)
                    first_index = i
                    first_e_d, first_e_p = candidate_d, candidate_p
                if candidate_d[t] - curr_dist > max_increase:
                    best_d, best_p = candidate_d, candidate_p
                    best_e = (u, v)
                    max_increase = candidate_d[t] - curr_dist
                    edge_inc = max_increase
                G.add_edge(u, v, weight=w)
        first_connected_n = None
        if c > 0:
            for i in range(min(len(shortest) - 2, first_index), 0, -1):
                u = shortest[i]
                removed_edges = []
                for v in G.adj[u]:
                    w = G[u][v]['weight']
                    removed_edges.append((u, v, w))
                G.remove_node(u)
                if not connected(G):
                    G.add_node(u)
                    for e in removed_edges:
                        G.add_edge(e[0], e[1], weight=e[2])
                    continue
                candidate_d, candidate_p = dijkstra(G)
                if not first_connected_n:
                    first_connected_n = u
                    first_n_d, first_n_p = candidate_d, candidate_p
                if candidate_d[t] - curr_dist > max_increase:
                    best_d, best_p = candidate_d, candidate_p
                    best_node = u
                    max_increase = candidate_d[t] - curr_dist
                    node_inc = max_increase
                G.add_node(u)
                for e in removed_edges:
                    G.add_edge(e[0], e[1], weight=e[2])

        if max_increase > 0:
            if edge_inc > node_inc:
                edges.append(best_e)
                G.remove_edge(best_e[0], best_e[1])
                d, p = best_d, best_p
                shortest = shortest_path(G, p)
                k -= 1
            else:
                nodes.append(best_node)
                G.remove_node(best_node)
                d, p = best_d, best_p
                shortest = shortest_path(G, p)
                c -= 1
        elif first_connected_e or first_connected_n:
            if not first_connected_n:
                edges.append(first_connected_e)
                G.remove_edge(first_connected_e[0], first_connected_e[1])
                d, p = first_e_d, first_e_p
                shortest = shortest_path(G, p)
                k -= 1
            elif not first_connected_e:
                nodes.append(first_connected_n)
                G.remove_node(first_connected_n)
                d, p = first_n_d, first_n_p
                shortest = shortest_path(G, p)
                c -= 1
            else:
                shortest_e = shortest_path(G, first_e_p)
                shortest_n = shortest_path(G, first_n_p)
                if len(shortest_e) >= len(shortest_n):
                    edges.append(first_connected_e)
                    G.remove_edge(first_connected_e[0], first_connected_e[1])
                    d, p = first_e_d, first_e_p
                    shortest = shortest_e
                    k -= 1
                else:
                    nodes.append(first_connected_n)
                    G.remove_node(first_connected_n)
                    d, p = first_n_d, first_n_p
                    shortest = shortest_n
                    c -= 1
        else:
            break
    return nodes, edges, shortest, d, p
        


def solve(G):
    #small k = 15, c = 1
    #medium k = 50, c = 3
    #large k = 100, c = 5
    """
    Args:
        G: networkx.Graph
    Returns:
        c: list of cities to remove
        k: list of edges to remove
    """
    return smart_greedy(G)


# Here's an example of how to run your solver.

# Usage: python3 solver.py test.in
"""
if __name__ == '__main__':
    assert len(sys.argv) == 2
    path = sys.argv[1]
    G = read_input_file(path)
    G_solve = G.copy()
    c, k = solve(G_solve)
    assert is_valid_solution(G, c, k)
    print("Shortest Path Difference: {}".format(calculate_score(G, c, k)))
    write_output_file(G, c, k, 'outputs/test.out')
"""

# For testing a folder of inputs to create a folder of outputs, you can use glob (need to import it)

if __name__ == '__main__':
    folders = ['small', 'medium', 'large']
    for f in folders:
        inputs = glob.glob('inputs/' + f + '/*', recursive=True)
        for input_path in inputs:
            output_path = 'outputs/' + f + '/' + basename(normpath(input_path))[:-3] + '.out'
            G = read_input_file(input_path)
            G_solve = G.copy()
            c, k = solve(G_solve)
            assert is_valid_solution(G, c, k)
            distance = calculate_score(G, c, k)
            write_output_file(G, c, k, output_path)

