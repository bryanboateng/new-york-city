import copy
import re

from networkx import dfs_preorder_nodes, DiGraph, bfs_tree

from yak_parser.Statechart import NodeType, Statechart


def process(statechart: Statechart):
    __remove_unreachable_states(statechart)
    __remove_duplicate_transitions(statechart)
    __remove_unnecessary_nesting(statechart)
    __normalize_time_units(statechart)


def __remove_unreachable_states(statechart: Statechart):
    graph = DiGraph()
    for node in statechart.hierarchy:
        if statechart.hierarchy.nodes[node]['ntype'] != NodeType.STATE:
            continue
        graph.add_node(node)
        successors = statechart.hierarchy.successors(node)
        grandchildren_nested = [statechart.hierarchy.successors(successor) for successor in successors]
        grandchildren = [grandchild for sublist in grandchildren_nested for grandchild in sublist]
        for state in grandchildren:
            if statechart.hierarchy.nodes[state]['obj'].initial:
                graph.add_edge(node, state)

    for transitions in statechart.transitions.values():
        for transition in transitions:
            graph.add_edge(transition.source_id, transition.target_id)

    root_initial_states = __get_root_initial_states(statechart)
    reachable_states_nested = []
    for initial_state in root_initial_states:
        reachable_states_nested.append(bfs_tree(graph, initial_state))

    reachable_states = [state for sublist in reachable_states_nested for state in sublist]
    unreachable_states = [state for state in graph if state not in reachable_states]

    for state in unreachable_states:
        statechart.transitions.pop(state, None)
    statechart.hierarchy.remove_nodes_from(unreachable_states)


def __get_root_initial_states(statechart: Statechart):
    root_successors = statechart.hierarchy.successors('root')
    root_grandchildren_nested = [statechart.hierarchy.successors(state) for state in root_successors]
    root_grandchildren = [grandchild for sublist in root_grandchildren_nested for grandchild in sublist]
    root_initial_states = []
    for state in root_grandchildren:
        if statechart.hierarchy.nodes[state]['obj'].initial:
            root_initial_states.append(state)
    return root_initial_states


def __remove_duplicate_transitions(statechart: Statechart):
    for state, transitions in copy.deepcopy(statechart.transitions).items():
        transition_set = set(transitions)
        statechart.transitions[state] = list(transition_set)


def __remove_unnecessary_nesting(statechart: Statechart):
    for node in dfs_preorder_nodes(copy.deepcopy(statechart.hierarchy)):
        if statechart.hierarchy.nodes[node]['ntype'] != NodeType.STATE:
            continue
        parent = __get_parent(statechart, node)
        if statechart.hierarchy.nodes[parent]['ntype'] != NodeType.REGION:
            raise ValueError('A very specific bad thing happened')
        # noinspection PyCallingNonCallable
        if statechart.hierarchy.out_degree(parent) != 1:
            continue
        grandparent = __get_parent(statechart, parent)
        grandparent_type = statechart.hierarchy.nodes[grandparent]['ntype']
        if grandparent_type == NodeType.ROOT:
            continue
        elif grandparent_type != NodeType.STATE:
            raise ValueError('A very specific bad thing happened')
        if __state_is_orthogonal(statechart, grandparent):
            continue
        great_grandparent = __get_parent(statechart, grandparent)
        if statechart.hierarchy.nodes[great_grandparent]['ntype'] != NodeType.REGION:
            raise ValueError('A very specific bad thing happened')

        __transfer_transitions(statechart, grandparent, node)
        __transfer_initial_status(statechart, grandparent, node)
        statechart.hierarchy.add_edge(great_grandparent, node)
        statechart.hierarchy.remove_nodes_from([parent, grandparent])


def __get_parent(statechart: Statechart, node):
    predecessors = list(statechart.hierarchy.predecessors(node))
    if len(predecessors) != 1:
        raise ValueError('A very specific bad thing happened')
    return predecessors[0]


def __state_is_orthogonal(statechart: Statechart, state):
    # noinspection PyCallingNonCallable
    return statechart.hierarchy.out_degree(state) != 1


def __transfer_initial_status(statechart: Statechart, origin, destination):
    statechart.hierarchy.nodes[destination]['obj'].initial = statechart.hierarchy.nodes[origin]['obj'].initial


def __transfer_transitions(statechart: Statechart, origin, destination):
    for transition in statechart.transitions[origin]:
        new_transition = copy.deepcopy(transition)
        new_transition.source_id = destination
        statechart.transitions[destination].append(new_transition)
    statechart.transitions.pop(origin)

    for state, transitions in copy.deepcopy(statechart.transitions).items():
        for transition in transitions:
            if transition.target_id == origin:
                new_transition = copy.deepcopy(transition)
                new_transition.target_id = destination
                statechart.transitions[state].append(new_transition)
                statechart.transitions[state].remove(transition)


def __normalize_time_units(statechart: Statechart):
    for transitions in statechart.transitions.values():
        for transition in transitions:
            for trigger in copy.deepcopy(transition.specification.triggers):
                result = re.compile(r'after\s+(\d+)\s*([mn]?s)').search(trigger)
                if result is not None:
                    transition.specification.triggers.remove(trigger)
                    nanoseconds = __convert_to_nanoseconds(int(result.group(1)), result.group(2))
                    transition.specification.triggers.add("after " + str(nanoseconds) + "ns")


def __convert_to_nanoseconds(amount: int, unit: str):
    if unit == 'ns':
        return amount
    elif unit == 'ms':
        return amount * 1000000
    elif unit == 's':
        return amount * 1000000000
    else:
        raise ValueError('A very specific bad thing happened')
