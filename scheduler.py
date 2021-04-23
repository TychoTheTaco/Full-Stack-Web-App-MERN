from collections import defaultdict

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


def recursive_remove(graph, node):
    pending = []

    def f(graph, node):
        pending.append(node)
        for n in graph.out_edges(node):
            f(graph, n[1])

    f(graph, node)
    graph.remove_nodes_from(pending)


def create_schedule(graph: nx.DiGraph, constraints: {}, preferences: {}, max_courses_per_quarter: int = 4):
    schedule = []
    quarter_index = -1

    def add(course):
        nonlocal quarter_index
        if len(schedule[quarter_index]) >= max_courses_per_quarter:
            quarter_index += 1
            schedule.append([])

        schedule[quarter_index].append(course)

    other = nx.DiGraph(graph)
    selected_courses = []

    while True:

        available_courses = []
        for n in graph.nodes:
            edges = graph.in_edges(n, data=True)
            for e in edges:
                if e[2]['t'] in [0, 2]:
                    break
            else:
                available_courses.append(n)
        print('Available:', available_courses)

        if len(available_courses) == 0:
            break

        schedule.append([])
        quarter_index += 1

        for course in available_courses:
            print('Consider:', course)

            # Check if all constraints have already been satisfied
            parents = [n for n in other.predecessors(course)]
            or_satisfied = False
            for parent in parents:
                if parent in constraints:
                    for i, con in enumerate(constraints[parent]):
                        if course in con[1]:
                            print('IN CON')

                            for c in con[1]:
                                if c in selected_courses:
                                    print('ALREADY SATISFIED')
                                    or_satisfied = True
                                    break

                            if parent in preferences:
                                pref = preferences[parent][i]
                                if pref != course:
                                    print('YIELD FOR PREFERENCE')
                                    continue

                        if or_satisfied:
                            break
                    if or_satisfied:
                        break
            if or_satisfied:
                recursive_remove(graph, course)
                continue

            # constraints not satisfied yet, select course
            print('SELECT', course)
            selected_courses.append(course)
            graph.remove_node(course)
            add(course)

    print(selected_courses)
    return schedule


def create_schedule_reverse(graph: nx.DiGraph, constraints: {}, preferences: {}, max_courses_per_quarter: int = 4):
    schedule = []
    quarter_index = -1

    def add(course):
        nonlocal quarter_index
        if len(schedule[quarter_index]) >= max_courses_per_quarter:
            quarter_index += 1
            schedule.append([])

        schedule[quarter_index].append(course)

    other = nx.DiGraph(graph)
    selected_courses = []

    while True:

        available_courses = [n for n, d in graph.in_degree() if d == 0]
        print('Available:', available_courses)

        if len(available_courses) == 0:
            break

        schedule.append([])
        quarter_index += 1

        shortest_path = nx.shortest_path_length(graph, target='COMPSCI 111')

        candidates = sorted([x for x in shortest_path if x in available_courses], key=lambda x: shortest_path[x])
        print('CAN:', candidates)

        course = candidates[0]
        print('Consider:', course)

        parents = [n for n in other.successors(course)]

        if len(parents) == 0:
            add(course)
            selected_courses.append(course)
            graph.remove_node(course)
            continue

        # find 'or' neighbors
        for parent in parents:
            if parent in constraints:
                for i, con in enumerate(constraints[parent]):
                    if course in con[1]:
                        print('SATISFY PARENT:', parent)
                        if course not in selected_courses:
                            add(course)
                            selected_courses.append(course)
                        for c in con[1]:
                            if graph.has_node(c):
                                graph.remove_node(c)  # TODO: RECURSIFVE
                                print('REMOVE', c)

        if course not in selected_courses:
            add(course)
            graph.remove_node(course)
            selected_courses.append(course)

    print(selected_courses)
    return schedule


def create_new_schedule(graph: nx.DiGraph, required_courses):
    selected_courses = []

    # Create a copy of the graph with only alpha-edges (top to bottom)
    # This graph is used to find the deepest required course
    alpha_graph = nx.DiGraph()
    for u, v, d in [x for x in graph.edges(data=True) if x[2]['t'] == 'a']:
        alpha_graph.add_edge(u, v, **d)

    while not all([x in selected_courses for x in required_courses]):

        # Find distance to each required course
        sources = [x[0] for x in alpha_graph.in_degree() if x[1] == 0]
        print(sources)
        distances = {}
        for source in sources:
            for c in [x for x in required_courses if x not in selected_courses]:
                try:
                    distances[(source, c)] = nx.shortest_path_length(alpha_graph, source=source, target=c)
                except networkx.exception.NetworkXNoPath:
                    pass  # Ignore  if no path
        print('DISTANCE:', distances)
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

            deepest_alpha_children = get_children(alpha_graph, deepest, 'a')
            print(deepest_alpha_children)

            no_alpha_out_nodes = [x[0] for x in alpha_graph.out_degree() if x[1] == 0 and x[0] in deepest_alpha_children]
            print(no_alpha_out_nodes)

            # sort by closest to source
            child_distances = {}
            for n in no_alpha_out_nodes:
                child_distances[n] = nx.shortest_path_length(graph, source=deepest, target=n)
            print(child_distances)
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

            # find beta parents
            beta_parents = [x[1] for x in graph.edges(best_child)]

            if len(beta_parents) == 0:
                selected_courses.append(best_child)
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
                        selected_courses.append(best_child)  # select child
                        print('SELECT:', best_child)
                    # delete the or node and all children if no incoming nodes
                    maybe_delete_node_and_children(parent)
                else:
                    if best_child not in selected_courses:
                        selected_courses.append(best_child)
                    maybe_delete_node_and_children(best_child)

    return selected_courses


if __name__ == '__main__':

    def add__dual_edge(graph, src, dst, **kwargs):
        graph.add_edge(src, dst, t='a', **kwargs)
        graph.add_edge(dst, src, t='b', **kwargs)

    graph = nx.DiGraph()

    # alpha goes down the tree, beta goes up
    add__dual_edge(graph, 'CS 111', 'or-0')
    add__dual_edge(graph, 'or-0', 'ICS 46')
    add__dual_edge(graph, 'or-0', 'CSE 46')
    add__dual_edge(graph, 'CS 111', 'ICS 6D')
    add__dual_edge(graph, 'CS 111', 'or-1')
    add__dual_edge(graph, 'or-1', 'MATH 3A')
    add__dual_edge(graph, 'or-1', 'ICS 6N')
    add__dual_edge(graph, 'CS 112', 'ICS 46')
    add__dual_edge(graph, 'CS 112', 'CSE 46')
    add__dual_edge(graph, 'CS 112', 'or-2')
    add__dual_edge(graph, 'or-2', 'MATH 3A')
    add__dual_edge(graph, 'or-2', 'ICS 6N')
    add__dual_edge(graph, 'ICS 46', 'or-3')
    add__dual_edge(graph, 'or-3', 'CSE 45C')
    add__dual_edge(graph, 'or-3', 'ICS 45C')
    add__dual_edge(graph, 'MATH 3A', 'or-4')
    add__dual_edge(graph, 'or-4', 'MATH 2A')
    add__dual_edge(graph, 'or-4', 'MATH 5B')
    add__dual_edge(graph, 'ICS 45C', 'or-5')
    add__dual_edge(graph, 'or-5', 'ICS 33')
    add__dual_edge(graph, 'or-5', 'CSE 43')
    add__dual_edge(graph, 'or-5', 'EECS 40')
    add__dual_edge(graph, 'ICS 33', 'or-6')
    add__dual_edge(graph, 'or-6', 'ICS 32')
    add__dual_edge(graph, 'or-6', 'CSE 42')
    add__dual_edge(graph, 'or-6', 'ICS 32A')
    add__dual_edge(graph, 'ICS 32', 'or-7')
    add__dual_edge(graph, 'or-7', 'ICS 31')
    add__dual_edge(graph, 'or-7', 'CSE 41')
    add__dual_edge(graph, 'EECS 40', 'EECS 22L')
    add__dual_edge(graph, 'EECS 22L', 'EECS 22', p=1)
    add__dual_edge(graph, 'EECS 22', 'or-8')
    add__dual_edge(graph, 'or-8', 'EECS 10')
    add__dual_edge(graph, 'or-8', 'EECS 20')
    add__dual_edge(graph, 'EECS 20', 'EECS 12')
    add__dual_edge(graph, 'EECS 10', 'MATH 2B', p=1)

    import matplotlib.pyplot as plt
    pos = nx.spring_layout(graph)
    nx.draw_networkx_labels(graph, pos)
    nx.draw_networkx_edges(graph, pos, edgelist=graph.edges, edge_color='r', arrows=True)
    plt.show()

    schedule = create_new_schedule(graph, required_courses=['CS 111', 'CS 112', 'ICS 33'])
    print('SCHEDULE:', schedule)
