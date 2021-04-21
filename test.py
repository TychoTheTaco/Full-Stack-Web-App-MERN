import unittest

import networkx as nx
import matplotlib.pyplot as plt

import scheduler


class TestScheduler(unittest.TestCase):

    def test_graph(self):
        graph = nx.DiGraph()
        graph.add_edge('COMPSCI 111', 'ICS 46', t=0)
        graph.add_edge('COMPSCI 111', 'CSE 46', t=0)
        graph.add_edge('COMPSCI 111', 'ICS 6D', t=0)
        graph.add_edge('COMPSCI 111', 'MATH 3A', t=0)
        graph.add_edge('COMPSCI 111', 'ICS 6N', t=0)
        #graph.add_edge('ICS 46', 'CSE 46', t=1)
        #graph.add_edge('CSE 46', 'ICS 46', t=1)
        #graph.add_edge('MATH 3A', 'ICS 6N', t=1)
        #graph.add_edge('ICS 6N', 'MATH 3A', t=1)
        graph.add_edge('COMPSCI 112', 'MATH 3A', t=0)
        graph.add_edge('COMPSCI 112', 'ICS 6N', t=0)
        graph.add_edge('COMPSCI 112', 'CSE 45C', t=0)
        graph.add_edge('COMPSCI 112', 'ICS 45C', t=0)
        graph.add_edge('ICS 46', 'CSE 45C', t=0)
        graph.add_edge('ICS 46', 'ICS 45C', t=0)
        #graph.add_edge('CSE 45C', 'ICS 45C', t=1)
        #graph.add_edge('ICS 45C', 'CSE 45C', t=1)
        graph.add_edge('ICS 45C', 'ICS 33', t=0)
        graph.add_edge('ICS 45C', 'CSE 43', t=0)
        graph.add_edge('ICS 45C', 'EECS 40', t=0)
        #graph.add_edge('ICS 33', 'CSE 43', t=1)
        #graph.add_edge('CSE 43', 'ICS 33', t=1)
        #graph.add_edge('CSE 43', 'EECS 40', t=1)
        #graph.add_edge('EECS 40', 'CSE 43', t=1)
        graph.add_edge('ICS 33', 'ICS 32', t=0)
        graph.add_edge('ICS 33', 'CSE 42', t=0)
        graph.add_edge('ICS 33', 'ICS 32A', t=0)
        #graph.add_edge('ICS 32', 'CSE 42', t=1)
        #graph.add_edge('CSE 42', 'ICS 32', t=1)
        #graph.add_edge('CSE 42', 'ICS 32A', t=1)
        #graph.add_edge('ICS 32A', 'CSE 42', t=1)
        graph.add_edge('ICS 32', 'ICS 31', t=0)
        graph.add_edge('ICS 32', 'CSE 41', t=0)
        #graph.add_edge('ICS 31', 'CSE 41', t=1)
        #graph.add_edge('CSE 41', 'ICS 31', t=1)
        graph.add_edge('EECS 40', 'EECS 22L', t=0)
        graph.add_edge('EECS 22L', 'EECS 22', t=0)
        graph.add_edge('EECS 22L', 'EECS 22', t=2)
        graph.add_edge('EECS 22', 'EECS 22L', t=2)
        graph.add_edge('EECS 22', 'EECS 10', t=0)
        graph.add_edge('EECS 22', 'EECS 20', t=0)
        #graph.add_edge('EECS 10', 'EECS 20', t=1)
        #graph.add_edge('EECS 20', 'EECS 10', t=1)
        graph.add_edge('EECS 20', 'EECS 12', t=0)
        graph.add_edge('MATH 3A', 'MATH 2B', t=0)
        graph.add_edge('MATH 3A', 'MATH 5B', t=0)
        #graph.add_edge('MATH 2B', 'MATH 5B', t=1)
        #graph.add_edge('MATH 5B', 'MATH 2A', t=1)
        #graph.add_edge('EECS 10', 'MATH 2A', t=2)

        # colors = {
        #     0: 'r',
        #     1: 'g',
        #     2: 'b'
        # }
        #
        # pos = nx.spring_layout(graph, scale=10)
        # nx.draw_networkx_labels(graph, pos)
        # nx.draw_networkx_edges(graph, pos, edgelist=graph.edges, edge_color=[colors[x[2]['t']] for x in graph.edges(data=True)],
        #                        arrows=True)
        # plt.show()

        constraints = {
            'COMPSCI 111': [('or', ['ICS 46', 'CSE 46']), ('or', ['MATH 3A', 'ICS 6N'])],
            'ICS 46': [('or', ['CSE 45C',  'ICS 45C'])],
            'ICS 45C': [('or', ['ICS 33', 'CSE 43', 'EECS 40'])],
            'ICS 33': [('or', ['ICS 32', 'CSE 42', 'ICS 32A'])],
            'ICS 32': [('or', ['ICS 31', 'CSE 41'])],
            'EECS 22': [('or', ['EECS 10', 'EECS 20'])],
            'MATH 3A': [('or', ['MATH 2B', 'MATH 5B'])]
        }

        scheduler.schedule(graph, constraints)


if __name__ == '__main__':
    unittest.main()
