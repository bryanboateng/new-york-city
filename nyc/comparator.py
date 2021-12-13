import itertools
from collections import defaultdict, Collection
from typing import List, Tuple, Any, Set, Dict, Iterator

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
    def __init__(self, diff: Diff, similarity_: float, single_similarity0: float, single_similarity1: float,
                 state_similarity: float, is_greedy: bool):
        self.diff = diff
        self.similarity = similarity_
        self.single_similarity0 = single_similarity0
        self.single_similarity1 = single_similarity1
        self.state_similarity = state_similarity
        self.is_greedy = is_greedy

    @property
    def max_similarity(self) -> float:
        return max(self.single_similarity0, self.single_similarity1)


class Comparator:
    def __init__(self, statechart1: Statechart, statechart2: Statechart):
        self.statechart1 = statechart1
        self.statechart2 = statechart2
        self.graph1 = create_comparison_graph(statechart1)
        self.graph2 = create_comparison_graph(statechart2)
        self.states1 = get_states(self.graph1)
        self.states2 = get_states(self.graph2)
        self.edges1 = get_edges(self.graph1)
        self.edges2 = get_edges(self.graph2)
        self.grouped_edges1 = group_edges(self.graph1, self.edges1)
        self.grouped_edges2 = group_edges(self.graph2, self.edges2)
        self.labeled_nodes1 = get_labeled_nodes(self.graph1)
        self.labeled_nodes2 = get_labeled_nodes(self.graph2)
        self.mapping_to_matches_cache = {}

    def compare(self) -> ComparisonResult:
        max_degree1 = 0 if self.grouped_edges1 == {} else \
            max((len(transitions) for state_pair, transitions in self.grouped_edges1.items()))
        max_degree2 = 0 if self.grouped_edges2 == {} else \
            max((len(transitions) for state_pair, transitions in self.grouped_edges2.items()))
        is_greedy = max(len(self.states1), len(self.states2), max_degree1, max_degree2) > 10
        if is_greedy:
            best_mapping, score = self.get_best_mapping_greedy()
        else:
            mappings = self.get_statechart_mappings()
            best_mappings, score = maxima(mappings, key=lambda mapping: len(self.get_matches(mapping)))

            if len(best_mappings) > 1:
                tie_break_graph1 = create_tie_break_comparison_graph(self.statechart1)
                tie_break_graph2 = create_tie_break_comparison_graph(self.statechart2)
                best_mapping = \
                    maxima(best_mappings,
                           key=lambda mapping: len(get_matches(tie_break_graph1, tie_break_graph2, mapping)))[0][0]
            else:
                best_mapping = best_mappings[0]

        matches = self.get_matches(best_mapping)
        grouped_matches = group_labeled_matches(matches)
        diff = Diff(
            grouped_matches,
            additions=group_labeled_elements({labeled_node for labeled_node in self.labeled_nodes2
                                              if labeled_node not in [match[1] for match in matches]}),
            deletions=group_labeled_elements({labeled_node for labeled_node in self.labeled_nodes1
                                              if labeled_node not in [match[0] for match in matches]})
        )
        return ComparisonResult(
            diff=diff,
            similarity_=2 * score / (len(self.labeled_nodes1) + len(self.labeled_nodes2)),
            state_similarity=
            2 * len([j for i in [x[1] for x in self.group(grouped_matches.items())['state']] for j in i]) /
            (len([x for x in self.labeled_nodes1 if x[0] in self.states1]) +
             len([x for x in self.labeled_nodes2 if x[0] in self.states2])),
            single_similarity0=score / len(self.labeled_nodes1),
            single_similarity1=score / len(self.labeled_nodes2),
            is_greedy=is_greedy
        )

    def get_match_type(self, labels):
        if labels == {'hierarchy'}:
            return 'hierarchy'
        elif self.is_transition(labels):
            return 'transition'
        else:
            return 'state'

    def is_transition(self, labels):
        if 'transition' in labels:
            return True
        elif any(x.startswith('trigger_') for x in labels):
            return True
        elif any(x.startswith('guard_') for x in labels):
            return True
        elif any(x.startswith('effect_') for x in labels):
            return True
        else:
            return False

    def group(self, matches: List[Tuple[Any, Set[str]]]) -> Dict[str, List[Tuple[Any, Set[str]]]]:
        dictionary = defaultdict(list)
        for x, labels in matches:
            dictionary[self.get_match_type(labels)].append((x, labels))
        return dictionary

    def get_best_mapping_greedy(self):
        mapping = {}
        while True:
            unmapped_graph1_states = [state for state in self.states1 if state not in mapping.keys()]
            unmapped_graph2_states = [state for state in self.states2 if state not in mapping.values()]
            if min(len(unmapped_graph1_states), len(unmapped_graph2_states)) == 0:
                break
            candidates = maxima(
                itertools.product(unmapped_graph1_states, unmapped_graph2_states),
                key=lambda mapping_element: self.get_mapping_element_score(mapping_element, mapping)
            )[0]
            if len(candidates) > 1:
                candidates = \
                    maxima(candidates, key=lambda mapping_element: self.look_ahead(mapping_element))[0]
            best_mapping_element = candidates[0]
            mapping[best_mapping_element[0]] = best_mapping_element[1]

            grouped_mapable_adjacent_edges1 = \
                get_grouped_mapable_adjacent_edges(best_mapping_element[0], self.graph1, mapping.keys())
            grouped_mapable_adjacent_edges2 = \
                get_grouped_mapable_adjacent_edges(best_mapping_element[1], self.graph2, mapping.values())

            for source, target in grouped_mapable_adjacent_edges1.copy():
                grouped_mapable_adjacent_edges1[(mapping[source], mapping[target])] = \
                    grouped_mapable_adjacent_edges1.pop((source, target))

            for group_key in [value for value in grouped_mapable_adjacent_edges1 if
                              value in grouped_mapable_adjacent_edges2]:
                unmapped_edges1: Set = grouped_mapable_adjacent_edges1[group_key].copy()
                unmapped_edges2: Set = grouped_mapable_adjacent_edges2[group_key].copy()
                while True:
                    if min(len(unmapped_edges1), len(unmapped_edges2)) == 0:
                        break
                    candidate = maxima(
                        itertools.product(unmapped_edges1, unmapped_edges2),
                        key=lambda mapping_element: len(self.get_matches(expand_mapping(mapping, mapping_element)))
                    )[0][0]
                    mapping[candidate[0]] = candidate[1]
                    unmapped_edges1.remove(candidate[0])
                    unmapped_edges2.remove(candidate[1])

        return mapping, len(self.get_matches(mapping))

    def get_mapping_element_score(self, mapping_element: Tuple[Any, Any], mapping: Dict[Any, Any]):
        match_count = self.get_match_count(mapping_element)

        predecessors1 = {x for x in self.graph1.predecessors(mapping_element[0])
                         if self.graph1.nodes[x]['source_id'] in mapping.keys()}
        predecessors2 = {x for x in self.graph2.predecessors(mapping_element[1])
                         if self.graph2.nodes[x]['source_id'] in mapping.values()}
        predecessors_score = self.get_edges_score(predecessors1, predecessors2)

        successors1 = {x for x in self.graph1.successors(mapping_element[0]) if
                       self.graph1.nodes[x]['target_id'] in mapping.keys()}
        successors2 = {x for x in self.graph2.successors(mapping_element[1]) if
                       self.graph2.nodes[x]['target_id'] in mapping.values()}
        successors_score = self.get_edges_score(successors1, successors2)

        return match_count + successors_score + predecessors_score

    def get_edges_score(self, edges1, edges2):
        combinations = list(itertools.product(edges1, edges2))
        if len(combinations) == 0:
            return 0
        else:
            similarity_values = []
            total_labels1 = []
            total_labels2 = []
            for edge1, edge2 in combinations:
                edge_labels1 = self.graph1.nodes[edge1]['labels']
                edge_labels2 = self.graph2.nodes[edge2]['labels']
                total_labels1.extend(edge_labels1)
                total_labels2.extend(edge_labels2)
                matches = edge_labels1 & edge_labels2
                similarity_values.append(2 * len(matches) / (len(edge_labels1) + len(edge_labels2)))
            return (sum(similarity_values) / len(combinations)) * (len(total_labels1) + len(total_labels2))

    def get_match_count(self, mapping_element):
        labeled_nodes1 = {(node, label) for node, label in self.labeled_nodes1 if node == mapping_element[0]}
        labeled_nodes2 = {(node, label) for node, label in self.labeled_nodes2 if node == mapping_element[1]}
        matches = set()
        for labeled_node in labeled_nodes1:
            match = (mapping_element[1], labeled_node[1])
            if match in labeled_nodes2:
                matches.add((labeled_node, match))
        return 2 * len(matches)

    def look_ahead(self, mapping_element: Tuple[Any, Any]):
        outgoing_labeled_transitions1 = \
            get_labeled_edges(self.graph1, self.edges1, self.labeled_nodes1, mapping_element[0], True)
        outgoing_labeled_transitions2 = \
            get_labeled_edges(self.graph2, self.edges2, self.labeled_nodes2, mapping_element[1], True)
        a = get_potential_new_labeled_nodes(outgoing_labeled_transitions1, outgoing_labeled_transitions2)
        b = get_potential_new_labeled_nodes(outgoing_labeled_transitions2, outgoing_labeled_transitions1)

        incoming_labeled_transitions1 = \
            get_labeled_edges(self.graph1, self.edges1, self.labeled_nodes1, mapping_element[0], False)
        incoming_labeled_transitions2 = \
            get_labeled_edges(self.graph2, self.edges2, self.labeled_nodes2, mapping_element[1], False)
        c = get_potential_new_labeled_nodes(incoming_labeled_transitions1, incoming_labeled_transitions2)
        d = get_potential_new_labeled_nodes(incoming_labeled_transitions2, incoming_labeled_transitions1)

        return len(a + b + c + d)

    def get_matches(self, mapping: Dict[Any, Any]) \
            -> Set[Tuple[Tuple[Any, str], Tuple[Any, str]]]:
        mapping_str = str(mapping)
        cached_matches = self.mapping_to_matches_cache.get(mapping_str)
        if cached_matches:
            return cached_matches
        else:
            matches = set()
            for labeled_node in self.labeled_nodes1:
                match = (mapping.get(labeled_node[0]), labeled_node[1])
                if match in self.labeled_nodes2:
                    matches.add((labeled_node, match))
            self.mapping_to_matches_cache[mapping_str] = matches
            return matches

    def get_statechart_mappings(self) -> List[Dict[Any, Any]]:
        state_mappings = get_mappings(self.states1, self.states2)
        mappings = []
        for state_mapping in state_mappings:
            grouped_transition_mapping_groups = []
            for (source, target), transitions1 in self.grouped_edges1.items():
                if state_mapping.get(source) and state_mapping.get(target):
                    transitions2 = self.grouped_edges2[state_mapping[source], state_mapping[target]]
                    transition_mappings = get_mappings(transitions1, transitions2)
                    if transition_mappings != [{}]:
                        grouped_transition_mapping_groups.append(transition_mappings)
            for transition_mapping_groups in list(itertools.product(*grouped_transition_mapping_groups)):
                mapping = state_mapping.copy()
                for transition_mapping_group in transition_mapping_groups:
                    mapping.update(transition_mapping_group)
                mappings.append(mapping)
        return mappings


def get_grouped_mapable_adjacent_edges(best_mapping_element, graph, mapping):
    predecessors = {x for x in graph.predecessors(best_mapping_element) if graph.nodes[x]['source_id'] in mapping}
    predecessors_grouped = group_edges(graph, predecessors)
    successors = {x for x in graph.successors(best_mapping_element) if graph.nodes[x]['target_id'] in mapping}
    successors_grouped = group_edges(graph, successors)
    return {**predecessors_grouped, **successors_grouped}


def get_labeled_edges(graph: networkx.DiGraph, edges: Set[Any], labeled_nodes: Set[Tuple[Any, str]],
                      state: Any, use_source: bool):
    relevant_edges = [edge for edge in edges if graph.nodes[edge]['source_id' if use_source else 'target_id'] == state]
    return [(node, label) for node, label in labeled_nodes if node in relevant_edges]


def get_potential_new_labeled_nodes(labeled_nodes1: List[Tuple[Any, str]], labeled_nodes2: List[Tuple[Any, str]]):
    return [(node, label) for node, label in labeled_nodes1 if label in [label for node, label in labeled_nodes2]]


def expand_mapping(mapping: Dict[Any, Any], mapping_element: Tuple[Any, Any]):
    copy = mapping.copy()
    copy[mapping_element[0]] = mapping_element[1]
    return copy


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
    if state_attributes['ntype'] == NodeType.STATE and hierarchy.nodes[state]['obj'].initial:
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
                labeled_graph.add_node(edge_id, labels={'hierarchy'}, source_id=state, target_id=substate)
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


def get_states(graph: networkx.DiGraph) -> Set[Any]:
    graph_labels = networkx.get_node_attributes(graph, 'labels').items()
    return {node for node, labels in graph_labels if 'state' in labels}


def get_edges(graph: networkx.DiGraph) -> Set[Any]:
    graph_labels = networkx.get_node_attributes(graph, 'labels').items()
    return {node for node, labels in graph_labels if 'transition' in labels or 'hierarchy' in labels}


def get_mappings(list1: Collection[Any], list2: Collection[Any]) -> List[Dict[Any, Any]]:
    element_count = min(len(list1), len(list2))
    list1_permutations = itertools.permutations(list1, element_count)
    list2_combinations = list(itertools.combinations(list2, element_count))
    return [
        dict(zip(permutation, combination))
        for permutation in list1_permutations
        for combination in list2_combinations
    ]


def group_edges(graph: networkx.DiGraph, transitions: Set[Any]) -> Dict[Tuple[Any, Any], Set[Any]]:
    dictionary = defaultdict(set)
    for transition in transitions:
        dictionary[get_source_and_target_states(graph, transition)].add(transition)
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
    labeled_nodes2 = get_labeled_nodes(graph2)
    for labeled_node in get_labeled_nodes(graph1):
        match = (mapping.get(labeled_node[0]), labeled_node[1])
        if match in labeled_nodes2:
            matches.add((labeled_node, match))
    return matches


def get_labeled_nodes(graph: networkx.DiGraph) -> Set[Tuple[Any, str]]:
    return {
        grandchild for sublist in
        [[(node, label) for label in labels] for (node, labels) in
         networkx.get_node_attributes(graph, 'labels').items()]
        for grandchild in sublist
    }


def group_labeled_matches(matches: Set[Tuple[Tuple[Any, str], Tuple[Any, str]]]) -> Dict[Tuple[Any, Any], Set[str]]:
    return group_labeled_elements({((x[0], y[0]), x[1]) for x, y in matches})


def group_labeled_elements(labeled_elements: Set[Tuple[Any, str]]) -> Dict[Any, Set[str]]:
    dictionary = {}
    for element, label in labeled_elements:
        if element not in dictionary:
            dictionary[element] = set()
        dictionary[element].add(label)
    return dictionary
