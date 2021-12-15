# Allow direct execution
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # noqa: E402

import unittest

from nyc.comparator import Diff, Comparator
from yak_parser.StatechartParser import StatechartParser


class TestComparator(unittest.TestCase):
    def test(self):
        statechart1 = StatechartParser().parse(path='testdata/test_comparison/test11.ysc')
        statechart2 = StatechartParser().parse(path='testdata/test_comparison/test12.ysc')

        comparison_result = Comparator(statechart1, statechart2).compare()
        self.assertEqual(
            Diff(
                matches={
                    ('_3ASwp5OAEeWuO-fDDpYHyA', '_3ASwp5OAEeWuO-fDDpYHyA'): {'state', 'initial'},
                    ('_Muq1cJQtEeWuO-fDDpYHyA', '_Muq1cJQtEeWuO-fDDpYHyA'): {'state'},
                    ('_Er2m0JQzEeWuO-fDDpYHyA', '_Er2m0JQzEeWuO-fDDpYHyA'): {'transition', 'trigger_operate'},
                    ('_QwgAQJQ6EeWuO-fDDpYHyA', '_QwgAQJQ6EeWuO-fDDpYHyA'): {'transition', 'trigger_operate'}
                },
                additions={
                    '_ZG7dMDPkEeyXfeIrKnJaqg': {'state'},
                    '_b3xNIDPkEeyXfeIrKnJaqg': {'transition', 'trigger_control'}
                },
                deletions={}
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

        comparison_result = Comparator(statechart1, statechart2).compare()
        self.assertEqual(
            Diff(
                matches={
                    ('A', '1'): {'state', 'initial'},
                    ('B', '2'): {'state'},
                    ('D', '3'): {'transition', 'trigger_myEvent'}
                },
                additions={},
                deletions={
                    'C': {'state'},
                    'E': {'transition', 'trigger_myEvent'},
                    'F': {'transition', 'trigger_myEvent'}
                }
            ),
            comparison_result.diff
        )
        self.assertEqual(1, comparison_result.max_similarity)
        self.assertEqual(1 / 2, comparison_result.single_similarity0)
        self.assertEqual(1, comparison_result.single_similarity1)
        self.assertEqual(2 / 3, comparison_result.similarity)

    def test3(self):
        statechart1 = StatechartParser().parse(path='testdata/test_comparison/test31.ysc')
        statechart2 = StatechartParser().parse(path='testdata/test_comparison/test32.ysc')

        comparison_result = Comparator(statechart1, statechart2).compare()
        self.assertEqual(
            Diff(
                matches={
                    ('_KvbzwB2oEeqjLfLN91KIGQ', '_Un6xkDpCEeyc9LxDSVYQGA'): {'state', 'initial'},
                    ('_LI9HAB2oEeqjLfLN91KIGQ', '_Un7YqTpCEeyc9LxDSVYQGA'): {'state'},
                    ('_TZxGoB2oEeqjLfLN91KIGQ', '_Un7YrDpCEeyc9LxDSVYQGA'): {'transition', 'trigger_Panel.btn_pressed', 'effect_z=0'},
                    ('_1MQwwB2oEeqjLfLN91KIGQ', '_Un7YojpCEeyc9LxDSVYQGA'): {'transition', 'trigger_vier'},
                    ('_sTVBMB2oEeqjLfLN91KIGQ', '_pR-l0DpCEeyc9LxDSVYQGA'): {'transition', 'trigger_after1000000ns', 'effect_pau=2', 'effect_raisevier'},
                    ('_Oed_YB2qEeqjLfLN91KIGQ', '_hDBAUDpCEeyc9LxDSVYQGA'): {'transition', 'trigger_Panel.btn_pressed', 'effect_z=0'},
                },
                additions={},
                deletions={},
            ),
            comparison_result.diff
        )
        self.assertEqual(1, comparison_result.max_similarity)
        self.assertEqual(1, comparison_result.single_similarity0)
        self.assertEqual(1, comparison_result.single_similarity1)
        self.assertEqual(1, comparison_result.similarity)

    def test4(self):
        statechart1 = StatechartParser().parse(path='testdata/test_comparison/test41.ysc')
        statechart2 = StatechartParser().parse(path='testdata/test_comparison/test42.ysc')

        comparison_result = Comparator(statechart1, statechart2).compare()
        self.assertEqual(
            Diff(
                matches={
                    ('_A0h8LkDQEeyOTKblN67hww', '_5FbX5kDOEeyOTKblN67hww'): {'state', 'initial'},
                    ('_A0ijNkDQEeyOTKblN67hww', '_5FbX8EDOEeyOTKblN67hww'): {'state', 'composite'},
                    ('_PPvogEDQEeyOTKblN67hww', '_aO4sEEDPEeyOTKblN67hww'): {'state', 'initial'},
                    ('_PeU3EEDQEeyOTKblN67hww', '_h3teoEDPEeyOTKblN67hww'): {'state'},
                    ('_A0h8MUDQEeyOTKblN67hww', '_5FbX6UDOEeyOTKblN67hww'): {'transition', 'trigger_Panel.btn_pressed'},
                    ('_A0ijOUDQEeyOTKblN67hww', '_5Fb-8UDOEeyOTKblN67hww'): {'transition', 'trigger_Panel.btn_pressed'},
                    ('_SZfnsEDQEeyOTKblN67hww', '_kBNhwEDPEeyOTKblN67hww'): {'transition', 'trigger_vier', 'effect_pau=4', 'effect_z=2'},
                    ('_A0ijNkDQEeyOTKblN67hww_PPvogEDQEeyOTKblN67hww',
                     '_5FbX8EDOEeyOTKblN67hww_aO4sEEDPEeyOTKblN67hww'): {'hierarchy'},
                    ('_A0ijNkDQEeyOTKblN67hww_PeU3EEDQEeyOTKblN67hww',
                     '_5FbX8EDOEeyOTKblN67hww_h3teoEDPEeyOTKblN67hww'): {'hierarchy'},
                },
                additions={},
                deletions={}
            ),
            comparison_result.diff
        )
        self.assertEqual(1, comparison_result.max_similarity)
        self.assertEqual(1, comparison_result.single_similarity0)
        self.assertEqual(1, comparison_result.single_similarity1)
        self.assertEqual(1, comparison_result.similarity)


if __name__ == '__main__':
    unittest.main()
