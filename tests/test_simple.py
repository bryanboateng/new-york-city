import unittest
from collections import Counter

import networkx
from yak_parser.Statechart import NodeType, Statechart, ScTransition
from yak_parser.StatechartParser import StatechartParser

from nyc import bryan


def node_match(node1, node2):
    if node1['ntype'] != node2['ntype']:
        return False

    if node1['ntype'] == NodeType.ROOT:
        return True
    else:
        labels_are_equal = node1['label'] == node2['label']
        if node1['ntype'] == NodeType.REGION:
            ids_are_equal = node1['obj'].state_id == node2['obj'].state_id
            histories_are_equal = node1['obj'].history == node2['obj'].history
            return labels_are_equal and ids_are_equal and histories_are_equal
        elif node1['ntype'] == NodeType.STATE:
            ids_are_equal = node1['obj'].initial == node2['obj'].initial
            names_are_equal = node1['obj'].name == node2['obj'].name
            specs_are_equal = \
                Counter([specification.__str__() for specification in node1['obj'].specifications]) == \
                Counter([specification.__str__() for specification in node2['obj'].specifications])

            return labels_are_equal and names_are_equal and specs_are_equal and ids_are_equal


def get_named_transitions(statechart: Statechart):
    transitions = [transition for sublist in statechart.transitions.values() for transition in sublist]
    return Counter([transition_convert_ids_to_names(transition, statechart) for transition in transitions])


def transition_convert_ids_to_names(transition: ScTransition, statechart: Statechart):
    source_name = statechart.hierarchy.nodes[transition.source_id]['obj'].name
    target_name = statechart.hierarchy.nodes[transition.target_id]['obj'].name

    return ScTransition(source_name, target_name, transition.specification)


class MyTestCase(unittest.TestCase):
    def test_remove_unreachable_states(self):
        statechart = StatechartParser().parse(path='test_remove_unreachable_states.ysc')
        bryan.process(statechart)
        statechart_expected = StatechartParser().parse(path='test_remove_unreachable_states_expected.ysc')

        self.assertStatechartEqual(statechart, statechart_expected)

    def assertStatechartEqual(self, statechart1: Statechart, statechart2: Statechart):
        self.assertEqual(statechart1.definition.events, statechart2.definition.events)
        self.assertTrue(networkx.is_isomorphic(statechart1.hierarchy, statechart2.hierarchy, node_match=node_match))
        self.assertEqual(get_named_transitions(statechart1), get_named_transitions(statechart2))
