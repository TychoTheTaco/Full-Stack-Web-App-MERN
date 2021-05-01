import unittest

import networkx as nx

import scheduler


class TestScheduler(unittest.TestCase):

    def assert_schedule_equal(self, actual, expected):
        for a, b in zip(actual, expected):
            self.assertCountEqual(a, b, f'Expected equality of\nEXPECTED:\n{expected}\nACTUAL:\n{actual}')

    def test_all_paths_simple(self):
        graph = nx.DiGraph()
        graph.add_edge('A', 'B')
        graph.add_edge('B', 'C')
        graph.add_edge('D', 'C')
        graph.add_edge('D', 'A')
        graph.add_edge('D', 'E')

        a = list(nx.all_simple_paths(graph, 'D', 'C'))
        b = scheduler.custom_all_simple_paths(graph, 'D', 'C')
        self.assertCountEqual(a, b)

    def test_all_paths_complex(self):
        graph = scheduler.create_graph(['COMPSCI 111', 'COMPSCI 112'])

        src, dst = 'COMPSCI 111', 'EECS 10'
        a = list(nx.all_simple_paths(graph, src, dst))
        b = scheduler.custom_all_simple_paths(graph, src, dst)
        self.assertCountEqual(a, b)

    def test_all_paths_cycle(self):
        graph = nx.DiGraph()
        graph.add_edge('A', 'B', t='a')
        graph.add_edge('D', 'C', t='a')
        graph.add_edge('D', 'A', t='a')
        graph.add_edge('D', 'E', t='a')
        graph.add_edge('C', 'F', t='a')
        graph.add_edge('F', 'G', t='b')
        graph.add_edge('G', 'F', t='b')
        graph.add_edge('G', 'H', t='a')
        graph.add_edge('E', 'G', t='a')

        src, dst = 'D', 'H'
        a = list(nx.all_simple_paths(graph, src, dst))
        b = scheduler.custom_all_simple_paths(graph, src, dst)
        self.assertCountEqual(a, b)

    def test_scheduler_simple(self):
        graph = nx.DiGraph()
        graph.add_edge('A', 'B')
        graph.add_edge('D', 'C')
        graph.add_edge('D', 'A')
        graph.add_edge('D', 'E')
        graph.add_edge('B', 'F')
        graph.add_edge('C', 'G')
        graph.add_edge('C', 'H')
        graph.add_edge('A', 'I')
        graph = graph.reverse()
        scheduler.show_graph(graph)

        schedule = scheduler.create_schedule_from_dag(graph)
        self.assert_schedule_equal(
            schedule,
            [['E', 'F', 'G', 'H'], ['I', 'B', 'C'], ['A'], ['D']]
        )

    def test_scheduler_cycle(self):
        graph = nx.DiGraph()
        graph.add_edge('A', 'B')
        graph.add_edge('D', 'C')
        graph.add_edge('D', 'A')
        graph.add_edge('D', 'E')
        graph.add_edge('B', 'F')
        graph.add_edge('C', 'G')
        graph.add_edge('C', 'H')
        graph.add_edge('A', 'I')
        graph = graph.reverse()
        scheduler.show_graph(graph)

        schedule = scheduler.create_schedule_from_dag(graph)
        self.assert_schedule_equal(
            schedule,
            [['E', 'F', 'G', 'H'], ['I', 'B', 'C'], ['A'], ['D']]
        )

    def test_scheduler_complex(self):
        schedule = scheduler.create_schedule(
            ['COMPSCI 111', 'COMPSCI 112']
        )
        self.assert_schedule_equal(
            schedule,
            [['MATH 3A', 'I&C SCI 6D', 'CSE 46', 'CSE 45C'], ['COMPSCI 111', 'COMPSCI 112']]
        )

        schedule = scheduler.create_schedule(
            ['COMPSCI 111', 'COMPSCI 112', 'I&C SCI 33'],
        )
        self.assert_schedule_equal(
            schedule,
            [['I&C SCI 6D', 'CSE 46', 'CSE 45C', 'CSE 42'], ['MATH 3A', 'I&C SCI 33'], ['COMPSCI 111', 'COMPSCI 112']]
        )


if __name__ == '__main__':
    unittest.main()
