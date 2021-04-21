from collections import defaultdict

import networkx as nx


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
