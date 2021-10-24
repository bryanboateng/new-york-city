import itertools
from collections import Counter
from typing import List, Tuple, Any

import networkx


def score(graph1: networkx.DiGraph, graph2: networkx.DiGraph, mapping: List[Tuple[Any, Any]]) -> float:
    return (len(matched_node_labels(graph1, graph2, mapping)) + len(matched_node_labels(graph2, graph1, mapping))) / \
           (len(get_labeled_nodes(graph1)) + len(get_labeled_nodes(graph2)))


def matched_node_labels(graph1: networkx.DiGraph, graph2: networkx.DiGraph, mapping: List[Tuple[Any, Any]]):
    return [labeled_node for labeled_node in get_labeled_nodes(graph1)
            if labeled_node_is_matched(labeled_node, mapping, graph2)]


def get_labeled_nodes(graph: networkx.DiGraph):
    return [
        grandchild for sublist in
        [[(node, label) for label in labels] for (node, labels) in
         networkx.get_node_attributes(graph, 'labels').items()]
        for grandchild in sublist
    ]


def labeled_node_is_matched(labeled_node: Tuple[Any, Any], mapping: List[Tuple[Any, Any]],
                            graph: networkx.DiGraph) -> bool:
    mapped_node = apply_mapping(mapping, labeled_node[0])
    labels = [label for node, label in get_labeled_nodes(graph) if node == mapped_node]
    return labeled_node[1] in labels


def apply_mapping(mapping: List[Tuple[Any, Any]], node: Any):
    relevant_mapping_elements = [(x, y) for x, y in mapping if x == node or y == node]
    if len(relevant_mapping_elements) > 1:
        raise ValueError('A very specific bad thing happened')
    elif len(relevant_mapping_elements) == 1:
        x, y = relevant_mapping_elements[0]
        return y if x == node else x


graph1 = networkx.DiGraph()
graph1.add_nodes_from([(0, {'labels': ['a']}), (1, {'labels': []})])
graph1.add_edges_from([(0, 1)])

graph2 = networkx.DiGraph()
graph2.add_nodes_from([(2, {'labels': ['a']}), (3, {'labels': ['b', 'm']})])
graph2.add_edges_from([(2, 3)])


def mapping_has_splits(mapping: List[list]):
    mapping_nodes_counted = Counter([node for sublist in mapping for node in sublist])
    return any(count > 1 for count in mapping_nodes_counted.values())


def get_all_possible_mappings(graph1: networkx.DiGraph, graph2: networkx.DiGraph):
    mappings = []
    product = list(itertools.product(graph1.nodes, graph2.nodes))
    product_list = [list(x) for x in product]
    for i in range(0, len(product) + 1):
        combinations: List[List[list]] = [list(x) for x in list(itertools.combinations(product_list, i))]
        mappings.extend(combinations)
    all_possible_mappings_list = [mapping for mapping in mappings if not mapping_has_splits(mapping)]
    return [[(x[0], x[1]) for x in mapping] for mapping in all_possible_mappings_list]


possible_mappings = get_all_possible_mappings(graph1, graph2)
print(max(possible_mappings, key=lambda mapping: score(graph1, graph2, mapping)))


def noji() -> List[str]:
    return ['s']
