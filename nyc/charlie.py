import itertools
from collections import Counter
from enum import Enum
from typing import List, Tuple, Any

import networkx
from yak_parser.Statechart import Statechart, NodeType


class MappingDirection(Enum):
    LEFT_TO_RIGHT = 1
    RIGHT_TO_LEFT = 2


def score(graph1: networkx.DiGraph, graph2: networkx.DiGraph, mapping: List[Tuple[Any, Any]]) -> float:
    return (
                   len(matched_node_labels(graph1, graph2, mapping, MappingDirection.LEFT_TO_RIGHT)) +
                   len(matched_node_labels(graph2, graph1, mapping, MappingDirection.RIGHT_TO_LEFT))
           ) / \
           (
                   len(get_labeled_nodes(graph1)) +
                   len(get_labeled_nodes(graph2))
           )


def matched_node_labels(graph1: networkx.DiGraph, graph2: networkx.DiGraph, mapping: List[Tuple[Any, Any]],
                        mapping_direction: MappingDirection):
    return [labeled_node for labeled_node in get_labeled_nodes(graph1)
            if labeled_node_is_matched(labeled_node, mapping, graph2, mapping_direction)]


def get_labeled_nodes(graph: networkx.DiGraph):
    return [
        grandchild for sublist in
        [[(node, label) for label in labels] for (node, labels) in
         networkx.get_node_attributes(graph, 'labels').items()]
        for grandchild in sublist
    ]


def labeled_node_is_matched(labeled_node: Tuple[Any, Any], mapping: List[Tuple[Any, Any]],
                            graph: networkx.DiGraph, mapping_direction: MappingDirection) -> bool:
    mapped_node = apply_mapping(labeled_node[0], mapping, mapping_direction)
    labels = [label for node, label in get_labeled_nodes(graph) if node == mapped_node]
    return labeled_node[1] in labels


def apply_mapping(node: Any, mapping: List[Tuple[Any, Any]], mapping_direction: MappingDirection):
    relevant_mapping_elements = [(x, y) for x, y in mapping if
                                 (x if mapping_direction == MappingDirection.RIGHT_TO_LEFT else y) == node]
    if len(relevant_mapping_elements) > 1:
        raise ValueError('A very specific bad thing happened')
    elif len(relevant_mapping_elements) == 1:
        return relevant_mapping_elements[0][1 if mapping_direction == MappingDirection.RIGHT_TO_LEFT else 0]


def mapping_has_splits(mapping: List[list]):
    left_mapping_nodes_counted = Counter([x[0] for x in mapping])
    right_mapping_nodes_counted = Counter([x[1] for x in mapping])
    return \
        any(count > 1 for count in left_mapping_nodes_counted.values()) or \
        any(count > 1 for count in right_mapping_nodes_counted.values())


def get_all_possible_mappings(graph1: networkx.DiGraph, graph2: networkx.DiGraph):
    mappings = []
    product = list(itertools.product(graph1.nodes, graph2.nodes))
    product_list = [list(x) for x in product]
    for i in range(0, len(product) + 1):
        combinations: List[List[list]] = [list(x) for x in list(itertools.combinations(product_list, i))]
        mappings.extend(combinations)
    all_possible_mappings_list = [mapping for mapping in mappings if not mapping_has_splits(mapping)]
    return [[(x[0], x[1]) for x in mapping] for mapping in all_possible_mappings_list]


def create_comparison_graph(statechart: Statechart):
    graph = networkx.DiGraph()
    for node in [
        node for node in statechart.hierarchy.nodes if statechart.hierarchy.nodes[node]['ntype'] == NodeType.STATE
    ]:
        graph.add_node(node, labels=['state'])
    return graph


def get_additions(statechart1: Statechart, statechart2: Statechart) -> List[str]:
    graph1 = create_comparison_graph(statechart1)
    graph2 = create_comparison_graph(statechart2)

    possible_mappings = get_all_possible_mappings(graph1, graph2)
    best_mapping = max(possible_mappings, key=lambda mapping: score(graph1, graph2, mapping))

    added_nodes = [node for node in graph2.nodes if node not in [y for x, y in best_mapping]]
    return [statechart2.hierarchy.nodes[node]['obj'].name for node in added_nodes]
