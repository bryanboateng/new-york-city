import itertools
from collections import defaultdict
from typing import List, Tuple, Any, Optional, Set, Dict

import networkx
from yak_parser.Statechart import Statechart, NodeType


class Diff:
    def __init__(self, matches: Dict[Tuple[Any, Any], Set[str]], additions: Dict[Any, Set[str]],
                 deletions: Dict[Any, Set[str]]):
        self.matches = matches
        self.additions = additions
        self.deletions = deletions

    def __eq__(self, other) -> bool:
        return self.matches == other.matches and \
               self.additions == other.additions and \
               self.deletions == other.deletions


class ComparisonResult:
    def __init__(self, diff: Diff, similarity_: float, single_similarity0: float, single_similarity1: float):
        self.diff = diff
        self.similarity = similarity_
        self.single_similarity0 = single_similarity0
        self.single_similarity1 = single_similarity1

    @property
    def max_similarity(self) -> float:
        return max(self.single_similarity0, self.single_similarity1)


def compare(statechart1: Statechart, statechart2: Statechart) -> ComparisonResult:
    graph1 = create_comparison_graph(statechart1)
    graph2 = create_comparison_graph(statechart2)

    mappings = get_statechart_mappings(graph1, graph2)
    best_mappings, similarity_ = maxima(mappings, key=lambda mapping: similarity(graph1, graph2, mapping))

    if len(best_mappings) > 1:
        tie_break_graph1 = create_tie_break_comparison_graph(statechart1)
        tie_break_graph2 = create_tie_break_comparison_graph(statechart2)
        best_mapping = \
            maxima(best_mappings, key=lambda mapping: similarity(tie_break_graph1, tie_break_graph2, mapping))[0][0]
    else:
        best_mapping = best_mappings[0]

    matches = get_matches(graph1, graph2, best_mapping)
    diff = Diff(
        group_labeled_matches(matches),
        additions=group_labeled_elements({labeled_node for labeled_node in get_labeled_nodes(graph2)
                                          if labeled_node not in [match[1] for match in matches]}),
        deletions=group_labeled_elements({labeled_node for labeled_node in get_labeled_nodes(graph1)
                                          if labeled_node not in [match[0] for match in matches]})
    )
    return ComparisonResult(
        diff=diff,
        similarity_=similarity_,
        single_similarity0=single_similarity(0, graph1, graph2, best_mapping),
        single_similarity1=single_similarity(1, graph1, graph2, best_mapping)
    )


def create_comparison_graph(statechart: Statechart) -> networkx.DiGraph:
    graph = networkx.DiGraph()
    for node in [
        node for node in statechart.hierarchy.nodes if statechart.hierarchy.nodes[node]['ntype'] == NodeType.STATE
    ]:
        labels = {'state'}
        if statechart.hierarchy.nodes[node]['obj'].initial:
            labels.add('initial')
        # noinspection PyCallingNonCallable
        if statechart.hierarchy.out_degree(node) > 0:
            labels.add('composite')
        graph.add_node(node, labels=labels)
    for transitions in statechart.transitions.values():
        for transition in transitions:
            labels = {'transition'}
            for trigger in transition.specification.triggers:
                labels.add('trigger_' + trigger)
            for effect in transition.specification.effects:
                labels.add('effect_' + effect)
            graph.add_node(transition.transition_id, labels=labels, source_id=transition.source_id,
                           target_id=transition.target_id)

            graph.add_edge(transition.source_id, transition.transition_id)
            graph.add_edge(transition.transition_id, transition.target_id)
    return graph


def create_tie_break_comparison_graph(statechart: Statechart) -> networkx.DiGraph:
    graph = networkx.DiGraph()
    for node in [
        node for node in statechart.hierarchy.nodes if statechart.hierarchy.nodes[node]['ntype'] == NodeType.STATE
    ]:
        graph.add_node(node, labels={'state', 'name_' + statechart.hierarchy.nodes[node]['obj'].name})
    return graph


def get_statechart_mappings(graph1: networkx.DiGraph, graph2: networkx.DiGraph) -> List[Dict[Any, Any]]:
    state_mappings = get_mappings(get_states(graph1), get_states(graph2))
    mappings = []
    for state_mapping in state_mappings:
        grouped_transitions1 = group_transitions(graph1, get_transitions(graph1))
        grouped_transitions2 = group_transitions(graph2, get_transitions(graph2))

        grouped_transition_mapping_groups = []
        for (source, target), transitions1 in grouped_transitions1.items():
            if state_mapping.get(source) and state_mapping.get(target):
                transitions2 = grouped_transitions2[state_mapping[source], state_mapping[target]]
                transition_mappings = get_mappings(transitions1, transitions2)
                if transition_mappings != [{}]:
                    grouped_transition_mapping_groups.append(transition_mappings)
        for transition_mapping_groups in list(itertools.product(*grouped_transition_mapping_groups)):
            mapping = state_mapping.copy()
            for transition_mapping_group in transition_mapping_groups:
                mapping.update(transition_mapping_group)
            mappings.append(mapping)
    return mappings


def get_states(graph: networkx.DiGraph) -> List[Any]:
    graph_labels = networkx.get_node_attributes(graph, 'labels').items()
    return [node for node, labels in graph_labels if 'state' in labels]


def get_transitions(graph: networkx.DiGraph) -> List[Any]:
    graph_labels = networkx.get_node_attributes(graph, 'labels').items()
    return [node for node, labels in graph_labels if 'transition' in labels]


def get_mappings(list1: List[Any], list2: List[Any]) -> List[Dict[Any, Any]]:
    element_count = min(len(list1), len(list2))
    list1_permutations = list(itertools.permutations(list1, element_count))
    list2_combinations = list(itertools.combinations(list2, element_count))
    return [dict(tuples) for tuples in [
        list(zip(permutation, combination))
        for permutation in list1_permutations
        for combination in list2_combinations
    ]]


def group_transitions(graph: networkx.DiGraph, transitions: List[Any]) -> Dict[Tuple[Any, Any], List[Any]]:
    dictionary = defaultdict(list)
    for transition in transitions:
        dictionary[get_source_and_target_states(graph, transition)].append(transition)
    return dictionary


def get_source_and_target_states(graph, transition):
    transition_attributes = graph.nodes[transition]
    source = transition_attributes['source_id']
    target = transition_attributes['target_id']
    return source, target


def maxima(iterable: List[Any], key) -> Tuple[List[Any], float]:
    elements_scored = [(element, key(element)) for element in iterable]
    max_score = max([score_ for element, score_ in elements_scored])
    return [element for element, score_ in elements_scored if score_ == max_score], max_score


def similarity(graph1: networkx.DiGraph, graph2: networkx.DiGraph, mapping: Dict[Any, Any]) -> float:
    return 2 * len(get_matches(graph1, graph2, mapping)) / (
            len(get_labeled_nodes(graph1)) + len(get_labeled_nodes(graph2)))


def single_similarity(similarity_type: int, graph1: networkx.DiGraph, graph2: networkx.DiGraph,
                      mapping: Dict[Any, Any]) -> float:
    if similarity_type != 0 and similarity_type != 1:
        raise ValueError('A very specific bad thing happened')

    return len(get_matches(graph1, graph2, mapping)) / len(get_labeled_nodes(graph2 if similarity_type else graph1))


def get_matches(graph1: networkx.DiGraph, graph2: networkx.DiGraph, mapping: Dict[Any, Any]) \
        -> Set[Tuple[Tuple[Any, str], Tuple[Any, str]]]:
    matches = set()
    for labeled_node in get_labeled_nodes(graph1):
        match = get_matching_labeled_node(labeled_node, mapping, graph2)
        if match is not None:
            matches.add((labeled_node, match))
    return matches


def get_labeled_nodes(graph: networkx.DiGraph) -> Set[Tuple[Any, str]]:
    return {
        grandchild for sublist in
        [[(node, label) for label in labels] for (node, labels) in
         networkx.get_node_attributes(graph, 'labels').items()]
        for grandchild in sublist
    }


def get_matching_labeled_node(labeled_node: Tuple[Any, str], mapping: Dict[Any, Any], graph: networkx.DiGraph) \
        -> Optional[Tuple[Any, str]]:
    matching_labeled_nodes = [(node, label) for node, label in get_labeled_nodes(graph)
                              if node == mapping.get(labeled_node[0]) and label == labeled_node[1]]
    if len(matching_labeled_nodes) > 1:
        raise ValueError('A very specific bad thing happened')
    if len(matching_labeled_nodes) == 1:
        matching_labeled_node = matching_labeled_nodes[0]
        if labeled_node[1] == matching_labeled_node[1]:
            return matching_labeled_node


def group_labeled_matches(matches: Set[Tuple[Tuple[Any, str], Tuple[Any, str]]]) -> Dict[Tuple[Any, Any], Set[str]]:
    return group_labeled_elements({((x[0], y[0]), x[1]) for x, y in matches})


def group_labeled_elements(labeled_elements: Set[Tuple[Any, str]]) -> Dict[Any, Set[str]]:
    dictionary = {}
    for element, label in labeled_elements:
        if element not in dictionary:
            dictionary[element] = set()
        dictionary[element].add(label)
    return dictionary
