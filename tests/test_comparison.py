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
                matches={
                    (('_3ASwp5OAEeWuO-fDDpYHyA', 'state'), ('_3ASwp5OAEeWuO-fDDpYHyA', 'state')),
                    (('_3ASwp5OAEeWuO-fDDpYHyA', 'initial'), ('_3ASwp5OAEeWuO-fDDpYHyA', 'initial')),
                    (('_Muq1cJQtEeWuO-fDDpYHyA', 'state'), ('_Muq1cJQtEeWuO-fDDpYHyA', 'state')),
                    (('_Er2m0JQzEeWuO-fDDpYHyA', 'transition'), ('_Er2m0JQzEeWuO-fDDpYHyA', 'transition')),
                    (('_Er2m0JQzEeWuO-fDDpYHyA', 'trigger_operate'), ('_Er2m0JQzEeWuO-fDDpYHyA', 'trigger_operate')),
                    (('_QwgAQJQ6EeWuO-fDDpYHyA', 'transition'), ('_QwgAQJQ6EeWuO-fDDpYHyA', 'transition')),
                    (('_QwgAQJQ6EeWuO-fDDpYHyA', 'trigger_operate'), ('_QwgAQJQ6EeWuO-fDDpYHyA', 'trigger_operate'))
                },
                additions={
                    ('_ZG7dMDPkEeyXfeIrKnJaqg', 'state'),
                    ('_b3xNIDPkEeyXfeIrKnJaqg', 'transition'),
                    ('_b3xNIDPkEeyXfeIrKnJaqg', 'trigger_control')
                },
                deletions=set(),
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
                matches={
                    (('_A2j7xjglEeykxvg1BffPgg', 'state'), ('_TzjKMDglEeykxvg1BffPgg', 'state')),
                    (('_A2j7xjglEeykxvg1BffPgg', 'initial'), ('_TzjKMDglEeykxvg1BffPgg', 'initial')),
                    (('_A2ki2TglEeykxvg1BffPgg', 'state'), ('_TzjKOjglEeykxvg1BffPgg', 'state')),
                    (('_A2ki0jglEeykxvg1BffPgg', 'transition'), ('_TzjKMzglEeykxvg1BffPgg', 'transition')),
                    (('_A2ki0jglEeykxvg1BffPgg', 'trigger_myEvent'), ('_TzjKMzglEeykxvg1BffPgg', 'trigger_myEvent'))
                },
                additions=set(),
                deletions={
                    ('_KA5kYDglEeykxvg1BffPgg', 'state'),
                    ('_A2lJ4jglEeykxvg1BffPgg', 'transition'),
                    ('_A2lJ4jglEeykxvg1BffPgg', 'trigger_myEvent'),
                    ('_M1EVIDglEeykxvg1BffPgg', 'transition'),
                    ('_M1EVIDglEeykxvg1BffPgg', 'trigger_myEvent')
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

        comparison_result = comparator.compare(statechart1, statechart2)
        self.assertEqual(
            Diff(
                matches={
                    (('_KvbzwB2oEeqjLfLN91KIGQ', 'state'), ('_Un6xkDpCEeyc9LxDSVYQGA', 'state')),
                    (('_KvbzwB2oEeqjLfLN91KIGQ', 'initial'), ('_Un6xkDpCEeyc9LxDSVYQGA', 'initial')),
                    (('_LI9HAB2oEeqjLfLN91KIGQ', 'state'), ('_Un7YqTpCEeyc9LxDSVYQGA', 'state')),
                    (('_TZxGoB2oEeqjLfLN91KIGQ', 'transition'), ('_Un7YrDpCEeyc9LxDSVYQGA', 'transition')),
                    (('_TZxGoB2oEeqjLfLN91KIGQ', 'trigger_Panel.btn_pressed'),
                     ('_Un7YrDpCEeyc9LxDSVYQGA', 'trigger_Panel.btn_pressed')),
                    (('_TZxGoB2oEeqjLfLN91KIGQ', 'effect_z=0'), ('_Un7YrDpCEeyc9LxDSVYQGA', 'effect_z=0')),
                    (('_1MQwwB2oEeqjLfLN91KIGQ', 'transition'), ('_Un7YojpCEeyc9LxDSVYQGA', 'transition')),
                    (('_1MQwwB2oEeqjLfLN91KIGQ', 'trigger_vier'), ('_Un7YojpCEeyc9LxDSVYQGA', 'trigger_vier')),
                    (('_sTVBMB2oEeqjLfLN91KIGQ', 'transition'), ('_pR-l0DpCEeyc9LxDSVYQGA', 'transition')),
                    (('_sTVBMB2oEeqjLfLN91KIGQ', 'trigger_after 1000000 ns'),
                     ('_pR-l0DpCEeyc9LxDSVYQGA', 'trigger_after 1000000 ns')),
                    (('_sTVBMB2oEeqjLfLN91KIGQ', 'effect_pau=2'), ('_pR-l0DpCEeyc9LxDSVYQGA', 'effect_pau=2')),
                    (('_sTVBMB2oEeqjLfLN91KIGQ', 'effect_raise vier'),
                     ('_pR-l0DpCEeyc9LxDSVYQGA', 'effect_raise vier')),
                    (('_Oed_YB2qEeqjLfLN91KIGQ', 'transition'), ('_hDBAUDpCEeyc9LxDSVYQGA', 'transition')),
                    (('_Oed_YB2qEeqjLfLN91KIGQ', 'trigger_Panel.btn_pressed'),
                     ('_hDBAUDpCEeyc9LxDSVYQGA', 'trigger_Panel.btn_pressed')),
                    (('_Oed_YB2qEeqjLfLN91KIGQ', 'effect_z=0'), ('_hDBAUDpCEeyc9LxDSVYQGA', 'effect_z=0'))
                },
                additions=set(),
                deletions=set(),
            ),
            comparison_result.diff
        )
        self.assertEqual(1, comparison_result.max_similarity)
        self.assertEqual(1, comparison_result.single_similarity0)
        self.assertEqual(1, comparison_result.single_similarity1)
        self.assertEqual(1, comparison_result.similarity)


if __name__ == '__main__':
    unittest.main()
