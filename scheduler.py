import collections
import itertools
import queue
from typing import Optional, List

import networkx as nx
import networkx.exception


class Node:

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return self.value

    def __hash__(self):
        if self.value == 'or':
            return hash(id(self))
        return hash(self.value)

    def __eq__(self, other):
        if self.value == 'or' and other.value == 'or':
            return id(self) == id(other)
        return self.value == other.value


def create_schedule(required_courses: [str], max_courses_per_quarter: int = 4, completed_courses: Optional[List[str]] = None):
    """
    ALGO:
    1) Create graph of all courses and their dependencies.
    2) Find all leaf nodes. (courses with no prerequisites)
    3) Find all root nodes. (courses with no incoming edges)
    4) Find all paths from all root nodes to all leaf nodes.
    5) Filter these paths so that only those that contain all required courses
    remain.
    6) Choose the shortest one of these paths
    8) Remove all nodes from the graph that are not in the shortest path
    9) Remove all intermediate 'or' nodes so that we are left with a simple DAG
    of course nodes.
    10) Run a topological sort to create a schedule
    :param required_courses:
    :param max_courses_per_quarter:
    :param completed_courses:
    :return:
    """
    if completed_courses is None:
        completed_courses = []

    # Remove completed courses from the required courses
    for course in completed_courses:
        if course in required_courses:
            required_courses.remove(course)

    # Create a directed graph of all courses and their prerequisites,
    # corequisites, and prerequisite-or-corequisites
    graph = create_graph(required_courses)

    # Create a graph of only 'alpha' edges
    alpha_graph = nx.DiGraph()
    for u, v, d in [x for x in graph.edges(data=True) if x[2]['t'] == 'a']:
        alpha_graph.add_edge(u, v, **d)

    def maybe_delete_node_and_children(node):
        for child in [x for x in alpha_graph.successors(node)]:
            maybe_delete_node_and_children(child)
        if alpha_graph.in_degree(node) <= 1:
            alpha_graph.remove_node(node)
            graph.remove_node(node)
            print('REMOVE:', node)
        else:
            print('delete later', node)

    # Remove completed courses from the graph
    for course in completed_courses:
        parents = [x for x in alpha_graph.predecessors(course)]
        for parent in parents:
            if parent.startswith('or'):

                # Get children of this 'or' node
                or_children = [x for x in alpha_graph.successors(parent)]

                # Delete children if they have no other parents
                for child in or_children:
                    maybe_delete_node_and_children(child)

                # Delete the 'or' node
                alpha_graph.remove_node(parent)
                print('REMOVE:', parent)

            else:
                maybe_delete_node_and_children(course)

    print('required_courses:', required_courses)

    leaf_nodes = [x[0] for x in alpha_graph.out_degree() if x[1] == 0]
    print('leafs:', leaf_nodes)

    paths = collections.defaultdict(list)
    for root in required_courses:
        for leaf in leaf_nodes:
            paths[root].extend([x for x in nx.all_simple_paths(alpha_graph, root, leaf)])
    for k, v in paths.items():
        print(k, len(v), v)

    # get strand combinations
    strands = collections.defaultdict(list)
    for root in required_courses:
        for path in paths[root]:
            strands[path[1]].append(path)

    print('child strands')
    for k, v in strands.items():
        print(k, len(v), v)

    # get all combos
    combos = [x for x in itertools.product(*[strands[x] for x in strands])]
    print('combos:', len(combos))

    flat_combos = []
    for c in combos:
        flat = []
        for x in c:
            for i in x:
                flat.append(i)
        flat_combos.append(set(flat))

    # sort by fewest courses
    def count_nor(x):
        cnt = 0
        for i in x:
            if i.startswith('or'):
                continue
            cnt += 1
        return cnt

    flat_combos = sorted(flat_combos, key=count_nor)

    #for c in flat_combos:
    #    print(len(c), c)

    # remove nodes not in best path
    nodes = [x for x in alpha_graph.nodes()]
    for node in nodes:
        if node not in flat_combos[0]:
            alpha_graph.remove_node(node)

    # remove useless 'or' nodes
    nodes = [x for x in alpha_graph.nodes()]
    for node in nodes:
        if node.startswith('or'):
            child = next(alpha_graph.successors(node))
            parent = next(alpha_graph.predecessors(node))
            alpha_graph.add_edge(parent, child, t='a')
            alpha_graph.remove_node(node)

    # Create schedule from DAG
    schedule = create_schedule_from_dag(alpha_graph.reverse(), max_courses_per_quarter)

    return schedule


def get_course(course_id, courses):
    s = course_id.split()
    d = ' '.join(s[:-1])
    n = s[-1]
    for c in courses:
        if c['department_code'] == d and c['number'] == n:
            return c
    return None


def add_dual_edge(graph, src, dst, **kwargs):
    graph.add_edge(src, dst, t='a', **kwargs)
    graph.add_edge(dst, src, t='b', **kwargs)


def create_graph(required_courses: [str]) -> nx.DiGraph:
    import json
    with open('catalog_parser/catalog.json', 'r') as file:
        courses = json.load(file)

    graph = nx.DiGraph()

    or_index = 0

    for course in required_courses:
        c = get_course(course, courses)
        if c is None:
            continue

        if 'prerequisite_courses' in c:
            pc = c['prerequisite_courses']

            def parse(p, parent):
                nonlocal or_index
                if isinstance(p, str):
                    if p in graph:
                        add_dual_edge(graph, parent, p)
                        print('SKIP CHILDS OF', p)
                        return

                    add_dual_edge(graph, parent, p)
                    print('ADD DUAL:', parent, p)

                    cc = get_course(p, courses)
                    if cc is not None and 'prerequisite_courses' in cc:
                        parse(cc['prerequisite_courses'], p)
                elif isinstance(p, list):
                    if p[0] == 'or':
                        oi = f'or-{or_index}'
                        or_index += 1
                        add_dual_edge(graph, parent, oi)
                        print('ADD DUAL:', parent, oi)
                        for cc in p[1]:
                            parse(cc, oi)
                    elif p[0] == 'and':
                        for cc in p[1]:
                            parse(cc, parent)

            parse(pc, course)

    return graph


def create_schedule_from_dag(graph: nx.DiGraph, max_courses_per_quarter: int = 4):
    schedule = []
    quarter_index = -1

    pending = collections.defaultdict(list)

    available = queue.Queue()
    while graph.number_of_nodes() > 0:

        # Start a new quarter
        schedule.append([])
        quarter_index += 1

        # Get available courses
        for x in [x[0] for x in graph.in_degree() if x[1] == 0]:
            available.put(x)

        while not available.empty():
            if len(schedule[quarter_index]) < max_courses_per_quarter:
                node = available.get()
                if node not in graph:
                    continue

                childs = list(graph.successors(node))
                if len(childs) == 1:
                    pending[quarter_index].append(node)
                    graph.remove_node(node)
                    continue

                schedule[quarter_index].append(node)
                graph.remove_node(node)
            else:
                break

    print('PENDING:', pending)
    for k, v in pending.items():
        quarter_index = k
        for course in v:
            while len(schedule[quarter_index]) >= max_courses_per_quarter:
                quarter_index += 1
            schedule[quarter_index].append(course)

    return schedule


def show_graph(graph):
    import matplotlib.pyplot as plt
    pos = nx.spring_layout(graph, k=0.15, iterations=20)
    nx.draw_networkx_labels(graph, pos)
    nx.draw_networkx_edges(graph, pos, edgelist=graph.edges, edge_color='r', arrows=True)
    plt.show()


if __name__ == '__main__':

    schedule = create_schedule(['COMPSCI 111', 'COMPSCI 112', 'EECS 40'], completed_courses=['EECS 22', 'MATH 3A'])
    print(schedule)
