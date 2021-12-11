# Allow direct execution
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # noqa: E402

import unittest
from nyc.comparator import get_statechart_mappings, create_comparison_graph
from yak_parser.StatechartParser import StatechartParser


class TestGetStatechartMappings(unittest.TestCase):
    def test1(self):
        statechart1 = StatechartParser().parse(
            path='testdata/test_comparison/test_get_statechart_mappings/test_get_statechart_mappings11.ysc'
        )
        statechart2 = StatechartParser().parse(
            path='testdata/test_comparison/test_get_statechart_mappings/test_get_statechart_mappings12.ysc'
        )
        graph1 = create_comparison_graph(statechart1)
        graph2 = create_comparison_graph(statechart2)

        expected = [
            {'A': '1', 'B': '2', 'q': 'x', 'r': 'y'},
            {'A': '1', 'B': '2', 'r': 'x', 'q': 'y'},
            {'B': '1', 'A': '2'}
        ]
        self.assertCountEqual(expected, get_statechart_mappings(graph1, graph2))

    def test2(self):
        statechart1 = StatechartParser().parse(
            path='testdata/test_comparison/test_get_statechart_mappings/test_get_statechart_mappings21.ysc'
        )
        statechart2 = StatechartParser().parse(
            path='testdata/test_comparison/test_get_statechart_mappings/test_get_statechart_mappings22.ysc'
        )
        graph1 = create_comparison_graph(statechart1)
        graph2 = create_comparison_graph(statechart2)

        expected = [
            {'D': 'A', 'E': 'B', 'F': 'C', '5': '1', '6': '2', '7': '3', '8': '4'},
            {'D': 'A', 'E': 'B', 'F': 'C', '5': '1', '6': '2', '8': '3', '7': '4'},
            {'D': 'A', 'E': 'B', 'F': 'C', '6': '1', '5': '2', '7': '3', '8': '4'},
            {'D': 'A', 'E': 'B', 'F': 'C', '6': '1', '5': '2', '8': '3', '7': '4'},
            {'D': 'A', 'F': 'B', 'E': 'C'},
            {'E': 'A', 'D': 'B', 'F': 'C'},
            {'E': 'A', 'F': 'B', 'D': 'C', '7': '1', '8': '2'},
            {'E': 'A', 'F': 'B', 'D': 'C', '8': '1', '7': '2'},
            {'F': 'A', 'D': 'B', 'E': 'C', '5': '3', '6': '4'},
            {'F': 'A', 'D': 'B', 'E': 'C', '6': '3', '5': '4'},
            {'F': 'A', 'E': 'B', 'D': 'C'}
        ]

        self.assertCountEqual(expected, get_statechart_mappings(graph1, graph2))

    def test3(self):
        statechart1 = StatechartParser().parse(
            path='testdata/test_comparison/test_get_statechart_mappings/test_get_statechart_mappings31.ysc'
        )
        statechart2 = StatechartParser().parse(
            path='testdata/test_comparison/test_get_statechart_mappings/test_get_statechart_mappings32.ysc'
        )
        graph1 = create_comparison_graph(statechart1)
        graph2 = create_comparison_graph(statechart2)

        expected = [
            {'A': 'D', 'B': 'E', '1': '4'},
            {'A': 'D', 'C': 'E'},
            {'B': 'D', 'A': 'E'},
            {'B': 'D', 'C': 'E', '2': '4'},
            {'C': 'D', 'A': 'E', '3': '4'},
            {'C': 'D', 'B': 'E'}
        ]

        self.assertCountEqual(expected, get_statechart_mappings(graph1, graph2))


if __name__ == '__main__':
    unittest.main()
