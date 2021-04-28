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


def create_schedule(graph: nx.DiGraph, required_courses: [str], max_courses_per_quarter: int = 4):
    """
    SETUP:
    1) Each course gets its own node
    2) Each 'or' relationship gets its own node.
    3) Create 'alpha' edges going from top to bottom (course points to prerequisite)
    4) Create 'beta' edges going from bottom to top (prerequisites point to successors)

    INPUT:
    1) List of courses to take: 'required_courses'

    ALGO:
    1) Let the root nodes be the courses with no incoming alpha edges
    2) Find deepest required course in the graph. The deepest course is the
    course which is farthest from the root nodes.
    3) Add deepest node to schedule
    4) For all 'alpha' children, if its a course, add it to the schedule. If the
    child has no other incoming alpha edges, remove it from the graph. Repeat
    this step for the selected child. If the child is an 'or' node, select any
    'alpha' child and delete the others if they have no other incoming 'alpha'
    edges'. Repeat this step for the selected child.

    :param graph:
    :param required_courses:
    :return:
    """
    schedule = []
    quarter_index = -1

    selected_courses = []

    def add(cn):
        nonlocal quarter_index, schedule
        if cn not in selected_courses:
            if len(schedule[quarter_index]) < max_courses_per_quarter:
                schedule[quarter_index].append(cn)
            else:
                schedule.append([])
                quarter_index += 1
                schedule[quarter_index].append(cn)
            selected_courses.append(cn)

    # Create a copy of the graph with only alpha-edges (top to bottom). This
    # graph is used to find the 'deepest' required course.
    alpha_graph = nx.DiGraph()
    for u, v, d in [x for x in graph.edges(data=True) if x[2]['t'] == 'a']:
        alpha_graph.add_edge(u, v, **d)

    # Loop until all required courses have been selected
    while not all([x in selected_courses for x in required_courses]):

        # Get the root nodes in the alpha graph. These nodes are those that have
        # no incoming 'alpha' edges.
        root_nodes = [x[0] for x in alpha_graph.in_degree() if x[1] == 0]

        # Find distance from each root node to each required course.
        distances = {}
        for source in root_nodes:
            for c in [x for x in required_courses if x not in selected_courses]:
                try:
                    distances[(source, c)] = nx.shortest_path_length(alpha_graph, source=source, target=c)
                except networkx.exception.NetworkXNoPath:
                    pass  # Ignore if no path

        # Get the 'deepest' node. This is the one with the largest maximum
        # distance to the root nodes.
        deepest = max(distances, key=lambda x: distances[x])[1]
        print(deepest)

        def get_children(graph: nx.DiGraph, node, t):
            children = []

            def f(node, t):
                children.append(node)
                for c in [x[1] for x in graph.edges(node, data=True) if x[2]['t'] == t]:
                    f(c, t)

            f(node, t)
            return children

        while deepest not in selected_courses:

            schedule.append([])
            quarter_index += 1

            # Get all 'alpha' children of the current node (recursively).
            deepest_alpha_children = get_children(alpha_graph, deepest, 'a')
            print(deepest_alpha_children)

            # Get all nodes with no outgoing 'alpha' edges. These are courses
            # that we could take immediately.
            no_alpha_out_nodes = [x[0] for x in alpha_graph.out_degree() if x[1] == 0 and x[0] in deepest_alpha_children]
            print(no_alpha_out_nodes)

            # Get distance from deepest node to all no_alpha_out_nodes
            child_distances = {}
            for n in no_alpha_out_nodes:
                child_distances[n] = nx.shortest_path_length(graph, source=deepest, target=n)
            print(child_distances)

            # Get the best child. This is the child that is closest to the
            # deepest node. It is the best because it is higher up the tree
            # compared to all other children.
            best_child = sorted(child_distances, key=lambda x: child_distances[x])[0]
            print('best:', best_child)

            def any_in_selected_courses(courses):
                for c in courses:
                    if c in selected_courses:
                        return True
                return False

            def maybe_delete_node_and_children(node):
                for child in [x for x in alpha_graph.successors(node)]:
                    maybe_delete_node_and_children(child)
                if alpha_graph.in_degree(node) <= 1:
                    alpha_graph.remove_node(node)
                    graph.remove_node(node)
                    print('REMOVE:', node)
                else:
                    print('delete later', node)

            # Get all 'beta' children of the best child. (Parents in the tree).
            beta_parents = [x[1] for x in graph.edges(best_child)]

            # Can we take anything at the same time? Get all paths from all leaf
            # nodes to all roots. If there is a leaf that shares no edges in the
            # path, we can take it at the same time.
            from collections import defaultdict
            paths = defaultdict(list)
            potential_courses = [x[0] for x in alpha_graph.out_degree() if x[1] == 0]
            for leaf in potential_courses:
                for root in root_nodes:
                    paths[leaf].append([x for x in nx.all_simple_paths(alpha_graph, root, leaf)])

            path_sets = defaultdict(set)
            for k, v in paths.items():
                for item in v:
                    if len(item) == 0:
                        continue
                    for c in item[0]:
                        if c not in root_nodes:
                            path_sets[k].add(c)

            same_time = []
            for c in potential_courses:
                can_we_take = True
                for cc in path_sets[c]:
                    if cc in path_sets[best_child]:
                        can_we_take = False
                print('CAN WE TAKE', c, ':', can_we_take)
                if can_we_take:
                    same_time.append(c)

            if len(beta_parents) == 0:
                add(best_child)
                maybe_delete_node_and_children(best_child)
                continue

            for parent in beta_parents:
                print('parent:', parent)
                if parent.startswith('or'):
                    or_children = [x for x in alpha_graph.successors(parent)]
                    print('OR CHILDS:', or_children)
                    if any_in_selected_courses(or_children):
                        pass
                    else:
                        add(best_child)
                    # delete the or node and all children if no incoming nodes
                    maybe_delete_node_and_children(parent)
                else:
                    add(best_child)
                    maybe_delete_node_and_children(best_child)

            for c in same_time:
                if len(schedule[quarter_index]) < max_courses_per_quarter:
                    if c in alpha_graph:
                        add(c)
                        bp = [x[1] for x in graph.edges(c)]
                        for b in bp:
                            if b.startswith('or'):
                                maybe_delete_node_and_children(b)

    return schedule, selected_courses


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


if __name__ == '__main__':
    # def add__dual_edge(graph, src, dst, **kwargs):
    #     graph.add_edge(src, dst, t='a', **kwargs)
    #     graph.add_edge(dst, src, t='b', **kwargs)
    #
    # graph = nx.DiGraph()
    #
    # # alpha goes down the tree, beta goes up
    # add__dual_edge(graph, 'CS 111', 'or-0')
    # add__dual_edge(graph, 'or-0', 'ICS 46')
    # add__dual_edge(graph, 'or-0', 'CSE 46')
    # add__dual_edge(graph, 'CS 111', 'ICS 6D')
    # add__dual_edge(graph, 'CS 111', 'or-1')
    # add__dual_edge(graph, 'or-1', 'MATH 3A')
    # add__dual_edge(graph, 'or-1', 'ICS 6N')
    # add__dual_edge(graph, 'CS 112', 'ICS 46')
    # add__dual_edge(graph, 'CS 112', 'CSE 46')
    # add__dual_edge(graph, 'CS 112', 'or-2')
    # add__dual_edge(graph, 'or-2', 'MATH 3A')
    # add__dual_edge(graph, 'or-2', 'ICS 6N')
    # add__dual_edge(graph, 'ICS 46', 'or-3')
    # add__dual_edge(graph, 'or-3', 'CSE 45C')
    # add__dual_edge(graph, 'or-3', 'ICS 45C')
    # add__dual_edge(graph, 'MATH 3A', 'or-4')
    # add__dual_edge(graph, 'or-4', 'MATH 2A')
    # add__dual_edge(graph, 'or-4', 'MATH 5B')
    # add__dual_edge(graph, 'ICS 45C', 'or-5')
    # add__dual_edge(graph, 'or-5', 'ICS 33')
    # add__dual_edge(graph, 'or-5', 'CSE 43')
    # add__dual_edge(graph, 'or-5', 'EECS 40')
    # add__dual_edge(graph, 'ICS 33', 'or-6')
    # add__dual_edge(graph, 'or-6', 'ICS 32')
    # add__dual_edge(graph, 'or-6', 'CSE 42')
    # add__dual_edge(graph, 'or-6', 'ICS 32A')
    # add__dual_edge(graph, 'ICS 32', 'or-7')
    # add__dual_edge(graph, 'or-7', 'ICS 31')
    # add__dual_edge(graph, 'or-7', 'CSE 41')
    # add__dual_edge(graph, 'EECS 40', 'EECS 22L')
    # add__dual_edge(graph, 'EECS 22L', 'EECS 22', c=1)
    # add__dual_edge(graph, 'EECS 22', 'or-8')
    # add__dual_edge(graph, 'or-8', 'EECS 10')
    # add__dual_edge(graph, 'or-8', 'EECS 20')
    # add__dual_edge(graph, 'EECS 20', 'EECS 12')
    # graph.add_edge('EECS 10', 'MATH 2A', t='a', c=1)
    # graph.add_edge('MATH 2A', 'EECS 10', t='b')

    graph = create_graph(['COMPSCI 111', 'COMPSCI 112'])

    import matplotlib.pyplot as plt

    pos = nx.spring_layout(graph)
    nx.draw_networkx_labels(graph, pos)
    nx.draw_networkx_edges(graph, pos, edgelist=graph.edges, edge_color='r', arrows=True)
    plt.show()

    schedule, _ = create_schedule(graph, required_courses=['COMPSCI 111', 'COMPSCI 112', 'EECS 22'])
    print('SCHEDULE:', schedule)
