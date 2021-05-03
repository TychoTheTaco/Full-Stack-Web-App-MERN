import unittest

import networkx as nx

import scheduler


class TestScheduler(unittest.TestCase):

    def assert_schedule_one_of(self, actual, expected_schedules):
        for expected in expected_schedules:
            is_ok = True
            if len(actual) != len(expected):
                continue
            for a, b in zip(actual, expected):
                for x in a:
                    if x not in b:
                        is_ok = False
                        break
                if not is_ok:
                    break
                for x in b:
                    if x not in a:
                        is_ok = False
                        break
                if not is_ok:
                    break
            if is_ok:
                return
        self.assertFalse(True, f'Expected equality of\nEXPECTED:\n{expected_schedules}\nACTUAL:\n{actual}')

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
        graph.add_edge('A', 'B', t='a')
        graph.add_edge('D', 'C', t='a')
        graph.add_edge('D', 'A', t='a')
        graph.add_edge('D', 'E', t='a')
        graph.add_edge('B', 'F', t='a')
        graph.add_edge('C', 'G', t='a')
        graph.add_edge('C', 'H', t='a')
        graph.add_edge('A', 'I', t='a')
        graph = graph.reverse()

        schedule = scheduler.create_schedule_from_dag(graph)
        self.assert_schedule_one_of(
            schedule,
            [
                [['I', 'H', 'G', 'F'], ['E', 'C', 'B'], ['A'], ['D']]
            ]
        )

    def test_scheduler_cycle(self):
        graph = nx.DiGraph()
        graph.add_edge('A', 'B', t='a')
        graph.add_edge('D', 'C', t='a')
        graph.add_edge('D', 'A', t='a')
        graph.add_edge('D', 'E', t='a')
        graph.add_edge('B', 'F', t='a')
        graph.add_edge('C', 'G', t='a')
        graph.add_edge('C', 'H', t='a')
        graph.add_edge('A', 'I', t='b')
        graph.add_edge('I', 'A', t='b')
        graph = graph.reverse()

        schedule = scheduler.create_schedule_from_dag(graph)
        self.assert_schedule_one_of(
            schedule,
            [
                [['H', 'G', 'F', 'E'], ['C', 'B'], ['A', 'I'], ['D']]
            ]
        )

    def test_scheduler_complex(self):
        schedule = scheduler.create_schedule(
            ['COMPSCI 111', 'COMPSCI 112']
        )
        self.assert_schedule_one_of(
            schedule,
            [
                [['MATH 3A', 'I&C SCI 6D', 'CSE 46', 'CSE 45C'], ['COMPSCI 111', 'COMPSCI 112']],
                [['MATH 3A', 'I&C SCI 6D', 'CSE 45C'], ['COMPSCI 112', 'I&C SCI 46'], ['COMPSCI 111']]
            ]
        )

        schedule = scheduler.create_schedule(
            ['COMPSCI 111', 'COMPSCI 112', 'I&C SCI 33'],
        )
        self.assert_schedule_one_of(
            schedule,
            [
                [['I&C SCI 6D', 'CSE 46', 'CSE 45C', 'CSE 42'], ['MATH 3A', 'I&C SCI 33'], ['COMPSCI 111', 'COMPSCI 112']],
                [['MATH 3A', 'I&C SCI 6D', 'CSE 46', 'CSE 42'], ['I&C SCI 33', 'CSE 45C', 'COMPSCI 111'], ['COMPSCI 112']]
            ]
        )

    def test_scheduler_corequisite_cycle(self):
        schedule = scheduler.create_schedule(
            ['MATH 105A']
        )
        self.assert_schedule_one_of(
            schedule,
            [
                [['MATH 3A'], ['MATH 105A', 'MATH 105LA']]
            ]
        )

    def test_scheduler_eecs163(self):
        schedule = scheduler.create_schedule(
            ['EECS 163']
        )
        self.assert_schedule_one_of(
            schedule,
            [
                [['PHYS 7D', 'MAE 10', 'ICS 31'], ['EECS 70A', 'MATH 3D'], ['EECS 70B', 'EECS 70LB'], ['EECS 163', 'EECS 163L']]
            ]
        )


if __name__ == '__main__':
    unittest.main()
