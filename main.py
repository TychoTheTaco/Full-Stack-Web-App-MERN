import collections
import json
import math
from abc import ABC, abstractmethod
from typing import List

import networkx
import networkx as nx

from catalog_parser.course import Course

groups = {}


class PrerequisiteTreeNode(ABC):

    def __init__(self, operator: str):
        self.operator = operator
        self.courses = []

    def __str__(self):
        result = '('
        for i, c in enumerate(self.courses):
            if i > 0:
                result += f' {self.operator} '
            if c is None:
                result += 'None'
            else:
                result += f'{c}'
        result += ')'
        return result

    def __len__(self):
        return len(self.courses)

    def __getitem__(self, item):
        return self.courses[item]


class CourseNode:

    def __init__(self, course):
        self.course = course
        self.child = None

    def __str__(self):
        if self.course is None:
            return 'None'
        return f'"{self.course["department_code"]} {self.course["number"]}"'


def get_or_groups(node):
    if isinstance(node, PrerequisiteTreeNode):
        if node.operator == 'or':
            groups[id(node)] = node
        for c in node.courses:
            get_or_groups(c)

    if isinstance(node, CourseNode):
        get_or_groups(node.child)


class DagNode:

    def __init__(self, courses):
        self.courses = courses

    def __repr__(self):
        result = '('
        for c in self.courses:
            result += c
        result += ')'
        return result

    def __eq__(self, other):
        a = set(self.courses)
        b = set(other.courses)
        return a == b

    def __hash__(self):
        return hash(tuple(self.courses))


def tree_to_dag(tree, parent):
    dag = nx.DiGraph()

    def f(tree, parent):
        if isinstance(tree, PrerequisiteTreeNode):
            for c in tree.courses:
                f(c, parent)
        elif isinstance(tree, CourseNode):
            src = tree.course['department_code'] + ' ' + tree.course['number']
            dst = parent
            dag.add_edge(DagNode([src]), DagNode([dst]))
            f(tree.child, src)

    f(tree, parent)
    return dag


def print_tree(tree, indent=0):
    if isinstance(tree, PrerequisiteTreeNode):
        print(' ' * indent, tree.operator)
        for c in tree.courses:
            print_tree(c, indent + 4)
    elif isinstance(tree, CourseNode):
        if tree.course is None:
            print(' ' * indent, 'None')
        else:
            print(' ' * indent, tree.course['department_code'], tree.course['number'])
            print_tree(tree.child, indent + 4)


def expand_prerequisites(p):
    if isinstance(p, str):
        c = get_course(p)
        node = CourseNode(c)
        if c is None:
            return node
        if 'prerequisite_courses' in c:
            node.child = expand_prerequisites(c['prerequisite_courses'])
        return node

    if isinstance(p, list):
        node = PrerequisiteTreeNode(p[0])
        for i, cc in enumerate(p[1]):
            node.courses.append(expand_prerequisites(cc))
        return node

    return None


def get_combo(graph, constraints, indexes):
    other = networkx.DiGraph(graph)
    selected_courses = []
    while True:
        available_courses = [n for n, d in graph.in_degree() if d == 0]
        print('AVAILABLE:', available_courses)
        if len(available_courses) == 0:
            break
        for course in available_courses:
            print('CONSIDER:', course)

            # remove if or-satisfied
            parents = [n for n in other.predecessors(course)]
            or_satisfied = False
            for parent in parents:
                for con in constraints[parent]:
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
                continue
            # if len([n for n in graph.predecessors(course)]) == 0:
            #     print('Removing')
            #     graph.remove_node(course)
            #     continue

            children = [n for n in graph.successors(course)]
            # check constrints
            if course in constraints:
                print('FOUND CONSTRAINTS', constraints[course])
                for i in range(len(constraints[course])):
                    if constraints[course][i][0] == 'or':
                        selected = constraints[course][i][1][indexes[course][i]]
                        print('SELECT:', selected)
                        selected_courses.append(selected)
                        graph.remove_node(selected)

            print('SELECT:', course)
            selected_courses.append(course)
            graph.remove_node(course)

    # if isinstance(src_tree, PrerequisiteTreeNode):
    #     if id(src_tree) in groups:
    #         return get_combo(src_tree[indexes[id(src_tree)]], groups, indexes)
    #     else:
    #         node = PrerequisiteTreeNode('and')
    #         for c in src_tree.courses:
    #             node.courses.append(get_combo(c, groups, indexes))
    #         return node
    # elif isinstance(src_tree, CourseNode):
    #     node = CourseNode(src_tree.course)
    #     node.child = get_combo(src_tree.child, groups, indexes)
    #     return node


def get_course(course_id: str):
    split = course_id.split()
    dept = ' '.join(split[:-1])
    number = split[-1]
    for c in courses:
        if c['department_code'] == dept and c['number'] == number:
            # return Course(c['department_code'], c['number'])
            R = ['description', 'restriction', 'units', 'title', 'prerequisite_notes', 'ge_category']
            for x in R:
                if x in c:
                    del c[x]
            return c
    return None


def create_schedule(dag: nx.DiGraph, max_courses_per_quarter=4):
    schedule = []
    quarter_index = -1

    def add(course):
        nonlocal quarter_index
        if len(schedule[quarter_index]) >= max_courses_per_quarter:
            quarter_index += 1
            schedule.append([])

        schedule[quarter_index].append(course)

    while dag.number_of_nodes() > 0:
        schedule.append([])
        quarter_index += 1

        available_courses = [n for n, d in dag.out_degree() if d == 0]

        for course in available_courses:
            add(course)

            # Add corequisites
            # print(course)
            # c = get_course(course)
            # if 'corequisite' in c:
            #     coro = c['corequisite']
            #     print('COREQ FOUND:', c['corequisite'])
            #     add(coro)
            #     if coro in dag:
            #         dag.remove_node(coro)

            dag.remove_node(course)

    return schedule


def create_graph_with_constraints(course):
    graph = networkx.DiGraph()

    cons = collections.defaultdict(list)

    def f(p, src):
        if isinstance(p, str):
            graph.add_edge(src, p, t=0)
            c = get_course(p)
            if c is not None and 'prerequisite_courses' in c:
                f(c['prerequisite_courses'], p)
        if isinstance(p, list):
            cl = []
            for cc in p[1]:
                cl.append(cc)
                f(cc, src)
            if p[0] == 'or':
                cons[src].append((p[0], cl))

    f(course['prerequisite_courses'], course['department_code'] + ' ' + course['number'])
    return graph, cons



def plot_graph(graph):
    import matplotlib.pyplot as plt

    colors = {
        0: 'r',
        1: 'g',
        2: 'b'
    }

    pos = nx.spring_layout(graph)
    nx.draw_networkx_labels(graph, pos)
    nx.draw_networkx_edges(graph, pos, edgelist=graph.edges, edge_color=[colors[x[2]['t']] for x in graph.edges(data=True)], arrows=True)
    plt.show()


# class Constraint(ABC):
#
#     def __init__(self):
#         pass
#
#
# class AtLeastOne(Constraint):
#
#     def __init__(self, courses: List):
#         super().__init__()
#         self.courses = courses
#
#
# class SameTime(Constraint):
#
#     def __init__(self, courses: List):
#         super().__init__()
#         self.courses = courses


def pd(d):
    for k, v in d.items():
        print(k, v)


if __name__ == '__main__':
    with open('catalog_parser/catalog.json') as file:
        courses = json.load(file)

    c = get_course('COMPSCI 111')
    compsci_111 = get_course('COMPSCI 111')

    graph, constraints = create_graph_with_constraints(c)
    plot_graph(graph)
    pd(constraints)

    max_indexes = []
    cur_indexes = []
    for k, v in constraints.items():
        max_indexes.append([])
        cur_indexes.append([])
        for x in v:
            max_indexes[-1].append(len(x[1]))
            cur_indexes[-1].append(0)
    print('MaX', max_indexes)
    print('START', cur_indexes)

    course_names = list(constraints.keys())

    def add(i, j):
        if i == len(cur_indexes):
            return True

        if j == len(cur_indexes[i]):
            return add(i + 1, 0)

        cur_indexes[i][j] += 1
        if cur_indexes[i][j] == max_indexes[i][j]:
            cur_indexes[i][j] = 0
            return add(i, j + 1)

        return False

    import copy
    combos = []
    while True:
        combos.append(copy.deepcopy(cur_indexes))
        if add(0, 0):
            break
    print('COMBOS:', len(combos))

    print(combos[8])
    f = get_combo(graph, constraints, {course_names[i]: combos[8][i] for i in range(len(course_names))})
    print(f)
    print_tree(f)

    dag = tree_to_dag(f, 'COMPSCI 111')
    print('DAG')

    plot_graph(dag)

    s = create_schedule(dag)
    print(s)
