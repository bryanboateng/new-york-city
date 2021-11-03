import itertools
from collections import Counter
from typing import List, Tuple, Any, Optional, Set

import networkx
from yak_parser.Statechart import Statechart, NodeType


class Diff:
    def __init__(self, matches: Set[Tuple[Tuple[Any, str], Tuple[Any, str]]], additions: Set[Tuple[Any, str]],
                 deletions: Set[Tuple[Any, str]]):
        self.matches = matches
        self.additions = additions
        self.deletions = deletions

    def __eq__(self, other) -> bool:
        return self.matches == other.matches and \
               self.additions == other.additions and \
               self.deletions == other.deletions


class ComparisonResult:
    def __init__(self, diff: Diff):
        self.diff = diff

    @property
    def similarity(self) -> float:
        return 2 * len(self.diff.matches) / \
               (
                       len(self.diff.matches) + len(self.diff.deletions) +
                       len(self.diff.matches) + len(self.diff.additions)
               )

    @property
    def max_similarity(self) -> float:
        return max(self.single_similarity0, self.single_similarity1)

    @property
    def single_similarity0(self) -> float:
        return self.__single_similarity(0)

    @property
    def single_similarity1(self) -> float:
        return self.__single_similarity(1)

    def __single_similarity(self, similarity_type: int) -> float:
        if similarity_type != 0 and similarity_type != 1:
            raise ValueError('A very specific bad thing happened')
        return len(self.diff.matches) / (
                       len(self.diff.matches) +
                       len(self.diff.additions if similarity_type else self.diff.deletions)
               )


def compare(statechart1: Statechart, statechart2: Statechart) -> ComparisonResult:
    graph1 = create_comparison_graph(statechart1)
    graph2 = create_comparison_graph(statechart2)

    possible_mappings = get_all_possible_mappings(graph1, graph2)
    best_mappings = maxima(possible_mappings, key=lambda mapping: score(graph1, graph2, mapping))

    if len(best_mappings) > 1:
        tie_break_graph1 = create_tie_break_comparison_graph(statechart1)
        tie_break_graph2 = create_tie_break_comparison_graph(statechart2)
        best_mapping = maxima(best_mappings, key=lambda mapping: score(tie_break_graph1, tie_break_graph2, mapping))[0]
    else:
        best_mapping = best_mappings[0]

    matches = get_matches(graph1, graph2, best_mapping)
    diff = Diff(
        matches,
        additions={labeled_node for labeled_node in get_labeled_nodes(graph2) if labeled_node not in
                   [match[1] for match in matches]},
        deletions={labeled_node for labeled_node in get_labeled_nodes(graph1) if labeled_node not in
                   [match[0] for match in matches]},
    )
    return ComparisonResult(diff)


def get_all_possible_mappings(graph1: networkx.DiGraph, graph2: networkx.DiGraph) -> List[Set[Tuple[Any, Any]]]:
    graph1_labels = networkx.get_node_attributes(graph1, 'labels').items()
    graph2_labels = networkx.get_node_attributes(graph2, 'labels').items()

    graph1_states = get_states(graph1_labels)
    graph2_states = get_states(graph2_labels)
    graph1_transitions = get_transitions(graph1_labels)
    graph2_transitions = get_transitions(graph2_labels)

    all_possible_state_mappings = [mapping for mapping in get_mappings(graph1_states, graph2_states)
                                   if not mapping_has_splits(mapping)]
    all_possible_transition_mappings = [mapping for mapping in get_mappings(graph1_transitions, graph2_transitions)
                                        if not mapping_has_splits(mapping)]

    return [set.union(state_mapping, transition_mapping) for state_mapping, transition_mapping in
            itertools.product(all_possible_state_mappings, all_possible_transition_mappings)
            if all(transition_mapping_element_is_valid(transition_mapping_element, state_mapping, graph1, graph2) for
                   transition_mapping_element in transition_mapping)]


def get_states(graph_labels) -> Set[Any]:
    return {node for node, labels in graph_labels if 'state' in labels}


def get_transitions(graph_labels) -> Set[Any]:
    return {node for node, labels in graph_labels if 'transition' in labels}


def get_mappings(set1: Set[Any], set2: Set[Any]) -> List[Set[Tuple[Any, Any]]]:
    mappings = []
    product = list(itertools.product(set1, set2))
    product_list = [list(x) for x in product]
    for i in range(0, len(product) + 1):
        combinations = [list(x) for x in list(itertools.combinations(product_list, i))]
        mappings.extend(combinations)
    return [{(x, y) for x, y in mapping} for mapping in mappings]


def mapping_has_splits(mapping: Set[Tuple[Any, Any]]) -> bool:
    left_mapping_nodes_counted = Counter([x for x, y in mapping])
    right_mapping_nodes_counted = Counter([y for x, y in mapping])
    return \
        any(count > 1 for count in left_mapping_nodes_counted.values()) or \
        any(count > 1 for count in right_mapping_nodes_counted.values())


def transition_mapping_element_is_valid(transition_mapping_element, state_mapping, graph1: networkx.DiGraph,
                                        graph2: networkx.DiGraph) -> bool:
    source_state1 = get_source_state(graph1, transition_mapping_element[0])
    source_state2 = get_source_state(graph2, transition_mapping_element[1])

    target_state1 = get_target_state(graph1, transition_mapping_element[0])
    target_state2 = get_target_state(graph2, transition_mapping_element[1])

    return (source_state1, source_state2) in state_mapping or (target_state1, target_state2) in state_mapping


def get_source_state(graph: networkx.DiGraph, transition) -> Any:
    in_edges = list(graph.in_edges(transition))
    if len(in_edges) != 1:
        raise ValueError('A very specific bad thing happened')
    return in_edges[0][0]


def get_target_state(graph: networkx.DiGraph, transition) -> Any:
    # noinspection PyArgumentList
    out_edges = list(graph.out_edges(transition))
    if len(out_edges) != 1:
        raise ValueError('A very specific bad thing happened')
    return out_edges[0][1]


def create_comparison_graph(statechart: Statechart) -> networkx.DiGraph:
    graph = networkx.DiGraph()
    for node in [
        node for node in statechart.hierarchy.nodes if statechart.hierarchy.nodes[node]['ntype'] == NodeType.STATE
    ]:
        labels = {'state'}
        if statechart.hierarchy.nodes[node]['obj'].initial:
            labels.add('initial')
        graph.add_node(node, labels=labels)
    for transitions in statechart.transitions.values():
        for transition in transitions:
            labels = {'transition'}
            for trigger in transition.specification.triggers:
                labels.add('trigger_' + trigger)
            for effect in transition.specification.effects:
                labels.add('effect_' + effect)
            graph.add_node(transition.transition_id, labels=labels)
            graph.add_edge(transition.source_id, transition.transition_id)
            graph.add_edge(transition.transition_id, transition.target_id)
    return graph


def create_tie_break_comparison_graph(statechart: Statechart) -> networkx.DiGraph:
    graph = networkx.DiGraph()
    for node in [
        node for node in statechart.hierarchy.nodes if statechart.hierarchy.nodes[node]['ntype'] == NodeType.STATE
    ]:
        graph.add_node(node, labels={'state', statechart.hierarchy.nodes[node]['obj'].name})
    return graph


def score(graph1: networkx.DiGraph, graph2: networkx.DiGraph, mapping: Set[Tuple[Any, Any]]) -> float:
    return (
                   2 * len(get_matches(graph1, graph2, mapping))
           ) / \
           (
                   len(get_labeled_nodes(graph1)) +
                   len(get_labeled_nodes(graph2))
           )


def get_matches(graph1: networkx.DiGraph, graph2: networkx.DiGraph, mapping: Set[Tuple[Any, Any]]) \
        -> Set[Tuple[Tuple[Any, str], Tuple[Any, str]]]:
    matches = set()
    for labeled_node in get_labeled_nodes(graph1):
        match = get_matching_labeled_node(labeled_node, mapping, graph2)
        if match is not None:
            matches.add((labeled_node, match))
    return matches


def get_matching_labeled_node(labeled_node: Tuple[Any, str], mapping: Set[Tuple[Any, Any]], graph: networkx.DiGraph) \
        -> Optional[Tuple[Any, str]]:
    mapped_node = apply_mapping(labeled_node[0], mapping)
    matching_labeled_nodes = [(node, label) for node, label in get_labeled_nodes(graph)
                              if node == mapped_node and label == labeled_node[1]]
    if len(matching_labeled_nodes) > 1:
        raise ValueError('A very specific bad thing happened')
    if len(matching_labeled_nodes) == 1:
        matching_labeled_node = matching_labeled_nodes[0]
        if labeled_node[1] == matching_labeled_node[1]:
            return matching_labeled_node


def apply_mapping(node: Any, mapping: Set[Tuple[Any, Any]]) -> Optional[Any]:
    relevant_mapping_elements = [(x, y) for x, y in mapping if x == node]
    if len(relevant_mapping_elements) > 1:
        raise ValueError('A very specific bad thing happened')
    elif len(relevant_mapping_elements) == 1:
        return relevant_mapping_elements[0][1]


def get_labeled_nodes(graph: networkx.DiGraph) -> Set[Tuple[Any, str]]:
    return {
        grandchild for sublist in
        [[(node, label) for label in labels] for (node, labels) in
         networkx.get_node_attributes(graph, 'labels').items()]
        for grandchild in sublist
    }


def maxima(iterable: List[Any], key) -> List[Any]:
    elements_scored = [(element, key(element)) for element in iterable]
    max_score = max([score_ for element, score_ in elements_scored])
    return [element for element, score_ in elements_scored if score_ == max_score]
