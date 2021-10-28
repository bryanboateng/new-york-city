# Allow direct execution
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # noqa: E402

import unittest

from nyc import charlie
from nyc.charlie import Diff
from yak_parser.StatechartParser import StatechartParser


class TestMatching(unittest.TestCase):
    def test(self):
        statechart1 = StatechartParser().parse(path='testdata/test_matching/test11.ysc')
        statechart2 = StatechartParser().parse(path='testdata/test_matching/test12.ysc')

        self.assertEqual(
            Diff(
                unchanged_node_features=[
                    ('_3ASwp5OAEeWuO-fDDpYHyA', 'state'),
                    ('_3ASwp5OAEeWuO-fDDpYHyA', 'initial'),
                    ('_Muq1cJQtEeWuO-fDDpYHyA', 'state')
                ],
                unchanged_edge_features=[
                    ('_3ASwp5OAEeWuO-fDDpYHyA', '_Muq1cJQtEeWuO-fDDpYHyA', 'transition'),
                    ('_3ASwp5OAEeWuO-fDDpYHyA', '_Muq1cJQtEeWuO-fDDpYHyA', 'trigger_operate'),
                    ('_Muq1cJQtEeWuO-fDDpYHyA', '_3ASwp5OAEeWuO-fDDpYHyA', 'transition'),
                    ('_Muq1cJQtEeWuO-fDDpYHyA', '_3ASwp5OAEeWuO-fDDpYHyA', 'trigger_operate')
                ],
                added_node_features=[
                    ('_ZG7dMDPkEeyXfeIrKnJaqg', 'state')
                ],
                added_edge_features=[
                    ('_Muq1cJQtEeWuO-fDDpYHyA', '_ZG7dMDPkEeyXfeIrKnJaqg', 'transition'),
                    ('_Muq1cJQtEeWuO-fDDpYHyA', '_ZG7dMDPkEeyXfeIrKnJaqg', 'trigger_control')
                ],
                deleted_node_features=[],
                deleted_edge_features=[]
            ),
            charlie.get_diff(statechart1, statechart2)
        )
        self.assertEqual(1, charlie.max_similarity(statechart1, statechart2))
        self.assertEqual(1, charlie.single_similarity(statechart1, statechart2))
        self.assertEqual(7 / 10, charlie.single_similarity(statechart2, statechart1))
        self.assertEqual(14 / 17, charlie.similarity(statechart1, statechart2))

    def test2(self):
        statechart1 = StatechartParser().parse(path='testdata/test_matching/test21.ysc')
        statechart2 = StatechartParser().parse(path='testdata/test_matching/test22.ysc')

        self.assertEqual(
            Diff(
                unchanged_node_features=[
                    ('_A2j7xjglEeykxvg1BffPgg', 'state'),
                    ('_A2j7xjglEeykxvg1BffPgg', 'initial'),
                    ('_A2ki2TglEeykxvg1BffPgg', 'state')
                ],
                unchanged_edge_features=[
                    ('_A2j7xjglEeykxvg1BffPgg', '_A2ki2TglEeykxvg1BffPgg', 'transition'),
                    ('_A2j7xjglEeykxvg1BffPgg', '_A2ki2TglEeykxvg1BffPgg', 'trigger_myEvent')
                ],
                added_node_features=[],
                added_edge_features=[],
                deleted_node_features=[
                    ('_KA5kYDglEeykxvg1BffPgg', 'state')
                ],
                deleted_edge_features=[
                    ('_A2ki2TglEeykxvg1BffPgg', '_KA5kYDglEeykxvg1BffPgg', 'transition'),
                    ('_A2ki2TglEeykxvg1BffPgg', '_KA5kYDglEeykxvg1BffPgg', 'trigger_myEvent'),
                    ('_KA5kYDglEeykxvg1BffPgg', '_A2j7xjglEeykxvg1BffPgg', 'transition'),
                    ('_KA5kYDglEeykxvg1BffPgg', '_A2j7xjglEeykxvg1BffPgg', 'trigger_myEvent')
                ]
            ),
            charlie.get_diff(statechart1, statechart2)
        )
        self.assertEqual(1, charlie.max_similarity(statechart1, statechart2))
        self.assertEqual(1/2, charlie.single_similarity(statechart1, statechart2))
        self.assertEqual(1, charlie.single_similarity(statechart2, statechart1))
        self.assertEqual(2/3, charlie.similarity(statechart1, statechart2))


if __name__ == '__main__':
    unittest.main()
