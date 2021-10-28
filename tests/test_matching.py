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
        statechart1 = StatechartParser().parse(path='testdata/test_matching/test1.ysc')
        statechart2 = StatechartParser().parse(path='testdata/test_matching/test2.ysc')

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


if __name__ == '__main__':
    unittest.main()
