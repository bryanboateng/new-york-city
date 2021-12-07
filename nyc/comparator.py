import itertools
from collections import defaultdict
from typing import List, Tuple, Any, Optional, Set, Dict, Iterator

import networkx
from yak_parser.Statechart import Statechart, NodeType, ScHistoryType


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


def get_best_mapping_greedy(graph1: networkx.DiGraph, graph2: networkx.DiGraph):
    mapping = {}
    graph1_states = get_states(graph1)
    graph2_states = get_states(graph2)
    while True:
        unmapped_graph1_states = [state for state in graph1_states if state not in mapping.keys()]
        unmapped_graph2_states = [state for state in graph2_states if state not in mapping.values()]
        if min(len(unmapped_graph1_states), len(unmapped_graph2_states)) == 0:
            break
        candidates = maxima(
            itertools.product(unmapped_graph1_states, unmapped_graph2_states),
            key=lambda mapping_element: len(get_matches(graph1, graph2, expand_mapping(mapping, mapping_element)))
        )[0]
        if len(candidates) > 1:
            candidates = maxima(candidates, key=lambda mapping_element: look_ahead(graph1, graph2, mapping_element))[0]
        best_mapping_element = candidates[0]
        mapping[best_mapping_element[0]] = best_mapping_element[1]

        grouped_mapable_adjacent_edges1 = \
            get_grouped_mapable_adjacent_edges(best_mapping_element[0], graph1, mapping.keys())
        grouped_mapable_adjacent_edges2 = \
            get_grouped_mapable_adjacent_edges(best_mapping_element[1], graph2, mapping.values())

        for source, target in grouped_mapable_adjacent_edges1.copy():
            grouped_mapable_adjacent_edges1[(mapping[source], mapping[target])] = \
                grouped_mapable_adjacent_edges1.pop((source, target))

        for edges1, edges2 in [(grouped_mapable_adjacent_edges1[group_key], grouped_mapable_adjacent_edges2[group_key])
                               for group_key in grouped_mapable_adjacent_edges1]:
            edge_mappings = get_mappings(edges1, edges2)
            if len(edge_mappings) == 1:
                mapping.update(edge_mappings[0])
            else:
                best_edge_mappings, _ = \
                    maxima(edge_mappings, key=lambda edge_mapping: len(get_matches(graph1, graph2, edge_mapping)))
                mapping.update(best_edge_mappings[0])
    return mapping, len(get_matches(graph1, graph2, mapping))


def get_grouped_mapable_adjacent_edges(best_mapping_element, graph, mapping):
    predecessors = [x for x in graph.predecessors(best_mapping_element) if graph.nodes[x]['source_id'] in mapping]
    predecessors_grouped = group_edges(graph, predecessors)
    successors = [x for x in graph.successors(best_mapping_element) if graph.nodes[x]['target_id'] in mapping]
    successors_grouped = group_edges(graph, successors)
    return {**predecessors_grouped, **successors_grouped}


def look_ahead(graph1: networkx.DiGraph, graph2: networkx.DiGraph, mapping_element: Tuple[Any, Any]):
    edges1 = get_edges(graph1)
    labeled_nodes1 = get_labeled_nodes(graph1)
    edges2 = get_edges(graph2)
    labeled_nodes2 = get_labeled_nodes(graph2)

    outgoing_labeled_transitions1 = \
        get_labeled_edges(graph1, edges1, labeled_nodes1, mapping_element[0], True)
    outgoing_labeled_transitions2 = \
        get_labeled_edges(graph2, edges2, labeled_nodes2, mapping_element[1], True)
    a = get_potential_new_labeled_nodes(outgoing_labeled_transitions1, outgoing_labeled_transitions2)
    b = get_potential_new_labeled_nodes(outgoing_labeled_transitions2, outgoing_labeled_transitions1)

    incoming_labeled_transitions1 = \
        get_labeled_edges(graph1, edges1, labeled_nodes1, mapping_element[0], False)
    incoming_labeled_transitions2 = \
        get_labeled_edges(graph2, edges2, labeled_nodes2, mapping_element[1], False)
    c = get_potential_new_labeled_nodes(incoming_labeled_transitions1, incoming_labeled_transitions2)
    d = get_potential_new_labeled_nodes(incoming_labeled_transitions2, incoming_labeled_transitions1)

    return len(a + b + c + d)


def get_labeled_edges(graph: networkx.DiGraph, edges: List[Any], labeled_nodes: Set[Tuple[Any, str]],
                      state: Any, use_source: bool):
    relevant_edges = [edge for edge in edges if graph.nodes[edge]['source_id' if use_source else 'target_id'] == state]
    return [(node, label) for node, label in labeled_nodes if node in relevant_edges]


def get_potential_new_labeled_nodes(labeled_nodes1: List[Tuple[Any, str]], labeled_nodes2: List[Tuple[Any, str]]):
    return [(node, label) for node, label in labeled_nodes1 if label in [label for node, label in labeled_nodes2]]


def expand_mapping(mapping: Dict[Any, Any], mapping_element: Tuple[Any, Any]):
    copy = mapping.copy()
    copy[mapping_element[0]] = mapping_element[1]
    return copy


def compare(statechart1: Statechart, statechart2: Statechart) -> ComparisonResult:
    graph1 = create_comparison_graph(statechart1)
    graph2 = create_comparison_graph(statechart2)

    if min(graph1.number_of_nodes(), graph2.number_of_nodes()) > 10:
        best_mapping, score = get_best_mapping_greedy(graph1, graph2)
    else:
        mappings = get_statechart_mappings(graph1, graph2)
        best_mappings, score = maxima(mappings, key=lambda mapping: len(get_matches(graph1, graph2, mapping)))

        if len(best_mappings) > 1:
            tie_break_graph1 = create_tie_break_comparison_graph(statechart1)
            tie_break_graph2 = create_tie_break_comparison_graph(statechart2)
            best_mapping = \
                maxima(best_mappings,
                       key=lambda mapping: len(get_matches(tie_break_graph1, tie_break_graph2, mapping)))[0][0]
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
        similarity_=2 * score / (len(get_labeled_nodes(graph1)) + len(get_labeled_nodes(graph2))),
        single_similarity0=score / len(get_labeled_nodes(graph1)),
        single_similarity1=score / len(get_labeled_nodes(graph2))
    )


def create_comparison_graph(statechart: Statechart) -> networkx.DiGraph:
    graph = networkx.DiGraph()
    # noinspection PyArgumentList
    for _, region in statechart.hierarchy.out_edges('root'):
        # noinspection PyArgumentList
        for _, state in statechart.hierarchy.out_edges(region):
            build_hierarchy(statechart.hierarchy, state, statechart.hierarchy.nodes[region]['obj'].history, graph)

    for transitions in statechart.transitions.values():
        for transition in transitions:
            labels = {'transition'}
            for trigger in transition.specification.triggers:
                labels.add('trigger_' + trigger)
            for effect in transition.specification.effects:
                labels.add('effect_' + effect)
            guard = transition.specification.guard
            if guard:
                guard_stripped = "".join(guard.split())
                if guard_stripped:
                    labels.add('guard_' + guard_stripped)
            graph.add_node(transition.transition_id, labels=labels, source_id=transition.source_id,
                           target_id=transition.target_id)

            graph.add_edge(transition.source_id, transition.transition_id)
            graph.add_edge(transition.transition_id, transition.target_id)
    return graph


def build_hierarchy(hierarchy: networkx.DiGraph, state: Any, history_type: ScHistoryType,
                    labeled_graph: networkx.DiGraph):
    labels = {'state'}
    state_attributes = hierarchy.nodes[state]
    if state_attributes['obj'].initial:
        labels.add('initial')
    if state_attributes['ntype'] == NodeType.FINAL:
        labels.add('final')
    if state_attributes['ntype'] == NodeType.CHOICE:
        labels.add('choice')

    if history_type == ScHistoryType.SHALLOW:
        labels.update({'history', 'shallow_history'})
    elif history_type == ScHistoryType.DEEP:
        labels.update({'history', 'deep_history'})
    # noinspection PyArgumentList
    edges_to_regions = list(hierarchy.out_edges(state))
    subregion_count = len(edges_to_regions)
    if subregion_count != 0:
        labels.add('composite' if subregion_count == 1 else 'orthogonal')
        for _, region in edges_to_regions:
            # noinspection PyArgumentList
            for _, substate in hierarchy.out_edges(region):
                edge_id = state + substate
                labeled_graph.add_node(edge_id, labels=['hierarchy'], source_id=state, target_id=substate)
                labeled_graph.add_edge(state, edge_id)
                labeled_graph.add_edge(edge_id, substate)
                build_hierarchy(hierarchy, substate, hierarchy.nodes[region]['obj'].history, labeled_graph)

    labeled_graph.add_node(state, labels=labels)


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
        grouped_edges1 = group_edges(graph1, get_edges(graph1))
        grouped_edges2 = group_edges(graph2, get_edges(graph2))

        grouped_transition_mapping_groups = []
        for (source, target), transitions1 in grouped_edges1.items():
            if state_mapping.get(source) and state_mapping.get(target):
                transitions2 = grouped_edges2[state_mapping[source], state_mapping[target]]
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


def get_edges(graph: networkx.DiGraph) -> List[Any]:
    graph_labels = networkx.get_node_attributes(graph, 'labels').items()
    return [node for node, labels in graph_labels if 'transition' in labels or 'hierarchy' in labels]


def get_mappings(list1: List[Any], list2: List[Any]) -> List[Dict[Any, Any]]:
    element_count = min(len(list1), len(list2))
    list1_permutations = itertools.permutations(list1, element_count)
    list2_combinations = list(itertools.combinations(list2, element_count))
    return [
        dict(zip(permutation, combination))
        for permutation in list1_permutations
        for combination in list2_combinations
    ]


def group_edges(graph: networkx.DiGraph, transitions: List[Any]) -> Dict[Tuple[Any, Any], List[Any]]:
    dictionary = defaultdict(list)
    for transition in transitions:
        dictionary[get_source_and_target_states(graph, transition)].append(transition)
    return dictionary


def get_source_and_target_states(graph, transition):
    transition_attributes = graph.nodes[transition]
    source = transition_attributes['source_id']
    target = transition_attributes['target_id']
    return source, target


def maxima(iterable: Iterator[Any], key) -> Tuple[List[Any], float]:
    elements_scored = defaultdict(list)
    for element in iterable:
        elements_scored[key(element)].append(element)
    max_score = max(elements_scored)
    return elements_scored[max_score], max_score


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
