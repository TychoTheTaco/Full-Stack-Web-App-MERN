from collections import defaultdict

import networkx as nx


def schedule(graph: nx.DiGraph, constraints: {}):
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

        for course in available_courses:
            print('Consider:', course)

            # Check if all constraints have already been satisfied
            parents = [n for n in other.predecessors(course)]
            or_satisfied = False
            for parent in parents:
                if parent in constraints:
                    for con in constraints[parent]:
                        if course in con[1]:
                            print('IN CON')
                            for c in con[1]:
                                if c in selected_courses:
                                    print('ALREADY SATISFIED')
                                    or_satisfied = True
                                    break
                        if or_satisfied:
                            break
                    if or_satisfied:
                        break
            if or_satisfied:
                graph.remove_node(course)
                continue

            # constraints not satisfied yet, select course
            print('SELECT', course)
            selected_courses.append(course)
            graph.remove_node(course)
