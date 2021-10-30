import itertools
from collections import Counter
from typing import List, Tuple, Any, Optional

import networkx
from yak_parser.Statechart import Statechart, NodeType


class Diff:
    def __init__(self,
                 matching_node_labels: List[Tuple[Tuple[Any, str], Tuple[Any, str]]],
                 matching_edge_labels: List[Tuple[Tuple[Any, Any, str], Tuple[Any, Any, str]]],
                 added_node_labels: List[Tuple[Any, str]],
                 added_edge_labels: List[Tuple[Any, Any, str]],
                 deleted_node_labels: List[Tuple[Any, str]],
                 deleted_edge_labels: List[Tuple[Any, Any, str]]
                 ):
        self.matching_node_labels = matching_node_labels
        self.matching_edge_labels = matching_edge_labels
        self.added_node_labels = added_node_labels
        self.added_edge_labels = added_edge_labels
        self.deleted_node_labels = deleted_node_labels
        self.deleted_edge_labels = deleted_edge_labels

    def __eq__(self, other):
        return self.matching_node_labels == other.matching_node_labels and \
               self.matching_edge_labels == other.matching_edge_labels and \
               self.added_node_labels == other.added_node_labels and \
               self.added_edge_labels == other.added_edge_labels and \
               self.deleted_node_labels == other.deleted_node_labels and \
               self.deleted_edge_labels == other.deleted_edge_labels


class ComparisonResult:
    def __init__(self, diff: Diff):
        self.diff = diff

    @property
    def similarity(self):
        return 2 * (len(self.diff.matching_node_labels) + len(self.diff.matching_edge_labels)) / \
               (
                       len(self.diff.matching_node_labels) + len(self.diff.deleted_node_labels) +
                       len(self.diff.matching_node_labels) + len(self.diff.added_node_labels) +
                       len(self.diff.matching_edge_labels) + len(self.diff.deleted_edge_labels) +
                       len(self.diff.matching_edge_labels) + len(self.diff.added_edge_labels)
               )

    @property
    def max_similarity(self) -> float:
        return max(self.single_similarity0, self.single_similarity1)

    @property
    def single_similarity0(self):
        return self.__single_similarity(0)

    @property
    def single_similarity1(self):
        return self.__single_similarity(1)

    def __single_similarity(self, similarity_type: int):
        if similarity_type != 0 and similarity_type != 1:
            raise ValueError('A very specific bad thing happened')
        return (len(self.diff.matching_node_labels) + len(self.diff.matching_edge_labels)) / \
               (
                       len(self.diff.matching_node_labels) +
                       len(self.diff.added_node_labels if similarity_type else self.diff.deleted_node_labels) +
                       len(self.diff.matching_edge_labels) +
                       len(self.diff.added_edge_labels if similarity_type else self.diff.deleted_edge_labels)
               )


def compare(statechart1: Statechart, statechart2: Statechart) -> ComparisonResult:
    graph1 = create_comparison_graph(statechart1)
    graph2 = create_comparison_graph(statechart2)

    possible_mappings = get_all_possible_mappings(graph1, graph2)
    best_mapping = max(possible_mappings, key=lambda mapping: score(graph1, graph2, mapping))

    matching_node_labels = get_matching_node_labels(graph1, graph2, best_mapping)
    matching_edge_labels = get_matching_edge_labels(graph1, graph2, best_mapping)
    diff = Diff(
        matching_node_labels,
        matching_edge_labels,
        added_node_labels=[labeled_node for labeled_node in get_labeled_nodes(graph2) if labeled_node not in
                           [match[1] for match in matching_node_labels]],
        added_edge_labels=[labeled_node for labeled_node in get_labeled_edges(graph2) if labeled_node not in
                           [match[1] for match in matching_edge_labels]],
        deleted_node_labels=[labeled_node for labeled_node in get_labeled_nodes(graph1) if labeled_node not in
                             [match[0] for match in matching_node_labels]],
        deleted_edge_labels=[labeled_node for labeled_node in get_labeled_edges(graph1) if labeled_node not in
                             [match[0] for match in matching_edge_labels]]
    )
    return ComparisonResult(diff)


def get_all_possible_mappings(graph1: networkx.DiGraph, graph2: networkx.DiGraph):
    mappings = []
    product = list(itertools.product(graph1.nodes, graph2.nodes))
    product_list = [list(x) for x in product]
    for i in range(0, len(product) + 1):
        combinations: List[List[list]] = [list(x) for x in list(itertools.combinations(product_list, i))]
        mappings.extend(combinations)
    all_possible_mappings_list = [mapping for mapping in mappings if not mapping_has_splits(mapping)]
    return [[(x[0], x[1]) for x in mapping] for mapping in all_possible_mappings_list]


def mapping_has_splits(mapping: List[list]):
    left_mapping_nodes_counted = Counter([x[0] for x in mapping])
    right_mapping_nodes_counted = Counter([x[1] for x in mapping])
    return \
        any(count > 1 for count in left_mapping_nodes_counted.values()) or \
        any(count > 1 for count in right_mapping_nodes_counted.values())


def create_comparison_graph(statechart: Statechart):
    graph = networkx.DiGraph()
    for node in [
        node for node in statechart.hierarchy.nodes if statechart.hierarchy.nodes[node]['ntype'] == NodeType.STATE
    ]:
        labels = ['state']
        if statechart.hierarchy.nodes[node]['obj'].initial:
            labels.append('initial')
        graph.add_node(node, labels=labels)
        for transitions in statechart.transitions.values():
            for transition in transitions:
                graph.add_edge(transition.source_id, transition.target_id, labels=['transition'])
                for trigger in transition.specification.triggers:
                    graph[transition.source_id][transition.target_id]['labels'].append('trigger_' + trigger)
    return graph


def score(graph1: networkx.DiGraph, graph2: networkx.DiGraph, mapping: List[Tuple[Any, Any]]) -> float:
    return (
                   2 * len(get_matching_node_labels(graph1, graph2, mapping)) +
                   2 * len(get_matching_edge_labels(graph1, graph2, mapping))
           ) / \
           (
                   len(get_labeled_nodes(graph1)) +
                   len(get_labeled_nodes(graph2)) +
                   len(get_labeled_edges(graph1)) +
                   len(get_labeled_edges(graph2))
           )


def get_matching_node_labels(graph1: networkx.DiGraph, graph2: networkx.DiGraph, mapping: List[Tuple[Any, Any]]):
    matches = []
    for labeled_node in get_labeled_nodes(graph1):
        match = get_matching_labeled_node(labeled_node, mapping, graph2)
        if match is not None:
            matches.append((labeled_node, match))
    return matches


def get_matching_edge_labels(graph1: networkx.DiGraph, graph2: networkx.DiGraph, mapping: List[Tuple[Any, Any]]):
    matches = []
    for labeled_edge in get_labeled_edges(graph1):
        match = get_matching_labeled_edge(labeled_edge, mapping, graph2)
        if match is not None:
            matches.append((labeled_edge, match))
    return matches


def get_matching_labeled_node(labeled_node: Tuple[Any, str], mapping: List[Tuple[Any, Any]], graph: networkx.DiGraph) \
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


def get_matching_labeled_edge(labeled_edge: Tuple[Any, Any, str], mapping: List[Tuple[Any, Any]],
                              graph: networkx.DiGraph) -> Optional[Tuple[Any, Any, str]]:
    mapped_origin_node = apply_mapping(labeled_edge[0], mapping)
    mapped_destination_node = apply_mapping(labeled_edge[1], mapping)
    matching_labeled_edges = [(origin_node, destination_node, label) for origin_node, destination_node, label in
                              get_labeled_edges(graph) if origin_node == mapped_origin_node and
                              destination_node == mapped_destination_node and label == labeled_edge[2]]
    if len(matching_labeled_edges) > 1:
        raise ValueError('A very specific bad thing happened')
    if len(matching_labeled_edges) == 1:
        matching_labeled_edge = matching_labeled_edges[0]
        if labeled_edge[2] == matching_labeled_edge[2]:
            return matching_labeled_edge


def apply_mapping(node: Any, mapping: List[Tuple[Any, Any]]):
    relevant_mapping_elements = [(x, y) for x, y in mapping if x == node]
    if len(relevant_mapping_elements) > 1:
        raise ValueError('A very specific bad thing happened')
    elif len(relevant_mapping_elements) == 1:
        return relevant_mapping_elements[0][1]


def get_labeled_nodes(graph: networkx.DiGraph):
    return [
        grandchild for sublist in
        [[(node, label) for label in labels] for (node, labels) in
         networkx.get_node_attributes(graph, 'labels').items()]
        for grandchild in sublist
    ]


def get_labeled_edges(graph: networkx.DiGraph):
    return [
        grandchild for sublist in
        [[(edge[0], edge[1], label) for label in labels] for (edge, labels) in
         networkx.get_edge_attributes(graph, 'labels').items()]
        for grandchild in sublist
    ]
