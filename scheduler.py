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


def succ_with_atr(graph: nx.DiGraph, node, attr: {}):
    children = []
    for src, dst, data in graph.edges(node, data=True):
        if len(attr) == 0:
            children.append(dst)
        for k, v in attr.items():
            if k in data and data[k] == v:
                children.append(dst)
    return children


def pred_with_atr(graph, node, attr):
    parents = []
    for src, dst, data in graph.in_edges(node, data=True):
        if len(attr) == 0:
            parents.append(dst)
        for k, v in attr.items():
            if k in data and data[k] == v:
                parents.append(src)
    return parents


def custom_all_simple_paths(graph, src, dst):
    paths = []

    stack = []

    def dfs(node):
        stack.append(node)
        if node == dst:
            paths.append(list(stack))

        for s, d, data in graph.edges(node, data=True):
            if len(stack) > 1 and stack[-2] == d:
                continue
            dfs(d)
        stack.pop()

    dfs(src)

    return paths


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

    def maybe_delete_node_and_children(node):
        for child in [x for x in graph.successors(node)]:
            maybe_delete_node_and_children(child)
        if graph.in_degree(node) <= 1:
            graph.remove_node(node)

    # Remove completed courses from the graph
    for course in completed_courses:
        parents = [x for x in graph.predecessors(course)]
        for parent in parents:
            if parent.startswith('or'):

                # Get children of this 'or' node
                or_children = [x for x in graph.successors(parent)]

                # Delete children if they have no other parents
                for child in or_children:
                    maybe_delete_node_and_children(child)

                # Delete the 'or' node
                graph.remove_node(parent)
                print('REMOVE:', parent)

            else:
                maybe_delete_node_and_children(course)

    # Find all leaf nodes. These are courses with no prerequisites (but they may
    # have corequisites)
    leaf_nodes = []
    for node in graph.nodes():
        children = succ_with_atr(graph, node, {'t': 'a'})
        if len(children) == 0:
            leaf_nodes.append(node)

    paths = collections.defaultdict(list)
    for root in required_courses:
        for leaf in leaf_nodes:
            paths[root].extend(custom_all_simple_paths(graph, root, leaf))

    # get strand combinations
    strands = collections.defaultdict(list)
    for root in required_courses:
        for path in paths[root]:
            strands[path[1]].append(path)

    # get all combos
    combos = [x for x in itertools.product(*[strands[x] for x in strands])]

    def get_depth(path):
        depth = 0
        for node in path:
            if node.startswith('or'):
                continue
            depth += 1
        return depth

    flat_combos = []
    for c in combos:
        flat = []
        for x in c:
            for i in x:
                flat.append(i)
        flat_combos.append((get_depth(flat), set(flat)))

    # sort by fewest courses
    flat_combos = sorted(flat_combos, key=lambda x:x[0])

    # remove nodes not in best path
    nodes = [x for x in graph.nodes()]
    for node in nodes:
        if node not in flat_combos[0]:
            graph.remove_node(node)

    # remove useless 'or' nodes
    nodes = [x for x in graph.nodes()]
    for node in nodes:
        if node.startswith('or'):
            child = next(graph.successors(node))
            parent = next(graph.predecessors(node))
            graph.add_edge(parent, child, t='a')
            graph.remove_node(node)

    # Create schedule from DAG
    schedule = create_schedule_from_dag(graph.reverse(), max_courses_per_quarter)

    return schedule


def get_course(course_id, courses):
    s = course_id.split()
    d = ' '.join(s[:-1])
    n = s[-1]
    for c in courses:
        if c['department_code'] == d and c['number'] == n:
            return c
    return None


def create_graph(courses: [str]) -> nx.DiGraph:
    import json
    with open('catalog_parser/catalog.json', 'r') as file:
        course_repo = json.load(file)

    graph = nx.DiGraph()

    or_index = 0

    for course in courses:
        c = get_course(course, course_repo)
        if c is None:
            continue

        def parse(p, parent, t='a'):
            nonlocal or_index
            if isinstance(p, str):
                if p in graph:
                    graph.add_edge(parent, p, t=t)
                    return

                graph.add_edge(parent, p, t=t)

                cc = get_course(p, course_repo)
                if cc is not None and 'prerequisite_courses' in cc:
                    parse(cc['prerequisite_courses'], p, 'a')
                if cc is not None and 'corequisite_courses' in cc:
                    parse(cc['corequisite_courses'], p, 'b')
            elif isinstance(p, list):
                if p[0] == 'or':
                    oi = f'or-{or_index}'
                    or_index += 1
                    graph.add_edge(parent, oi, t=t)
                    for cc in p[1]:
                        parse(cc, oi, t='a')
                elif p[0] == 'and':
                    for cc in p[1]:
                        parse(cc, parent, t='a')

        # Prerequisites
        if 'prerequisite_courses' in c:
            pc = c['prerequisite_courses']
            parse(pc, course)

        # Corequisites
        if 'corequisite_courses' in c:
            coro = c['corequisite_courses']
            parse(coro, course, t='b')

    return graph


def create_schedule_from_dag(graph: nx.DiGraph, max_courses_per_quarter: int = 4):
    schedule = []
    quarter_index = -1

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

                schedule[quarter_index].append(node)
                graph.remove_node(node)
            else:
                break

    return schedule


def show_graph(graph):
    import matplotlib.pyplot as plt
    pos = nx.spring_layout(graph, k=0.15, iterations=20)
    nx.draw_networkx_labels(graph, pos)
    color_map = {'a': 'red', 'b': 'blue'}
    colors = []
    for src, dst, data in graph.edges(data=True):
        if 't' in data:
            colors.append(color_map[data['t']])
        else:
            colors.append('red')
    nx.draw_networkx_edges(graph, pos, edgelist=graph.edges, edge_color=colors, arrows=True)
    plt.show()


if __name__ == '__main__':
    schedule = create_schedule(['EECS 163'])
    print(schedule)
