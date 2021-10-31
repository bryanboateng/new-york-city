# Allow direct execution
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # noqa: E402

import unittest

from nyc import comparator
from nyc.comparator import Diff
from yak_parser.StatechartParser import StatechartParser


class TestComparator(unittest.TestCase):
    def test(self):
        statechart1 = StatechartParser().parse(path='testdata/test_comparison/test11.ysc')
        statechart2 = StatechartParser().parse(path='testdata/test_comparison/test12.ysc')

        comparison_result = comparator.compare(statechart1, statechart2)
        self.assertEqual(
            Diff(
                matching_node_labels=[
                    (('_3ASwp5OAEeWuO-fDDpYHyA', 'state'), ('_3ASwp5OAEeWuO-fDDpYHyA', 'state')),
                    (('_3ASwp5OAEeWuO-fDDpYHyA', 'initial'), ('_3ASwp5OAEeWuO-fDDpYHyA', 'initial')),
                    (('_Muq1cJQtEeWuO-fDDpYHyA', 'state'), ('_Muq1cJQtEeWuO-fDDpYHyA', 'state'))
                ],
                matching_edge_labels=[
                    (
                        ('_3ASwp5OAEeWuO-fDDpYHyA', '_Muq1cJQtEeWuO-fDDpYHyA', 'transition'),
                        ('_3ASwp5OAEeWuO-fDDpYHyA', '_Muq1cJQtEeWuO-fDDpYHyA', 'transition')
                    ),
                    (
                        ('_3ASwp5OAEeWuO-fDDpYHyA', '_Muq1cJQtEeWuO-fDDpYHyA', 'trigger_operate'),
                        ('_3ASwp5OAEeWuO-fDDpYHyA', '_Muq1cJQtEeWuO-fDDpYHyA', 'trigger_operate')
                    ),
                    (
                        ('_Muq1cJQtEeWuO-fDDpYHyA', '_3ASwp5OAEeWuO-fDDpYHyA', 'transition'),
                        ('_Muq1cJQtEeWuO-fDDpYHyA', '_3ASwp5OAEeWuO-fDDpYHyA', 'transition')
                    ),
                    (
                        ('_Muq1cJQtEeWuO-fDDpYHyA', '_3ASwp5OAEeWuO-fDDpYHyA', 'trigger_operate'),
                        ('_Muq1cJQtEeWuO-fDDpYHyA', '_3ASwp5OAEeWuO-fDDpYHyA', 'trigger_operate')
                    )
                ],
                added_node_labels=[
                    ('_ZG7dMDPkEeyXfeIrKnJaqg', 'state')
                ],
                added_edge_labels=[
                    ('_Muq1cJQtEeWuO-fDDpYHyA', '_ZG7dMDPkEeyXfeIrKnJaqg', 'transition'),
                    ('_Muq1cJQtEeWuO-fDDpYHyA', '_ZG7dMDPkEeyXfeIrKnJaqg', 'trigger_control')
                ],
                deleted_node_labels=[],
                deleted_edge_labels=[]
            ),
            comparison_result.diff
        )
        self.assertEqual(1, comparison_result.max_similarity)
        self.assertEqual(1, comparison_result.single_similarity0)
        self.assertEqual(7 / 10, comparison_result.single_similarity1)
        self.assertEqual(14 / 17, comparison_result.similarity)

    def test2(self):
        statechart1 = StatechartParser().parse(path='testdata/test_comparison/test21.ysc')
        statechart2 = StatechartParser().parse(path='testdata/test_comparison/test22.ysc')

        comparison_result = comparator.compare(statechart1, statechart2)
        self.assertEqual(
            Diff(
                matching_node_labels=[
                    (('_A2j7xjglEeykxvg1BffPgg', 'state'), ('_TzjKMDglEeykxvg1BffPgg', 'state')),
                    (('_A2j7xjglEeykxvg1BffPgg', 'initial'), ('_TzjKMDglEeykxvg1BffPgg', 'initial')),
                    (('_A2ki2TglEeykxvg1BffPgg', 'state'), ('_TzjKOjglEeykxvg1BffPgg', 'state'))
                ],
                matching_edge_labels=[
                    (
                        ('_A2j7xjglEeykxvg1BffPgg', '_A2ki2TglEeykxvg1BffPgg', 'transition'),
                        ('_TzjKMDglEeykxvg1BffPgg', '_TzjKOjglEeykxvg1BffPgg', 'transition')
                    ),
                    (
                        ('_A2j7xjglEeykxvg1BffPgg', '_A2ki2TglEeykxvg1BffPgg', 'trigger_myEvent'),
                        ('_TzjKMDglEeykxvg1BffPgg', '_TzjKOjglEeykxvg1BffPgg', 'trigger_myEvent')
                    )
                ],
                added_node_labels=[],
                added_edge_labels=[],
                deleted_node_labels=[
                    ('_KA5kYDglEeykxvg1BffPgg', 'state')
                ],
                deleted_edge_labels=[
                    ('_A2ki2TglEeykxvg1BffPgg', '_KA5kYDglEeykxvg1BffPgg', 'transition'),
                    ('_A2ki2TglEeykxvg1BffPgg', '_KA5kYDglEeykxvg1BffPgg', 'trigger_myEvent'),
                    ('_KA5kYDglEeykxvg1BffPgg', '_A2j7xjglEeykxvg1BffPgg', 'transition'),
                    ('_KA5kYDglEeykxvg1BffPgg', '_A2j7xjglEeykxvg1BffPgg', 'trigger_myEvent')
                ]
            ),
            comparison_result.diff
        )
        self.assertEqual(1, comparison_result.max_similarity)
        self.assertEqual(1 / 2, comparison_result.single_similarity0)
        self.assertEqual(1, comparison_result.single_similarity1)
        self.assertEqual(2 / 3, comparison_result.similarity)


if __name__ == '__main__':
    unittest.main()
