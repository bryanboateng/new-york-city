import argparse
import copy
import itertools
import os
import pickle
import sys
from collections import defaultdict
from multiprocessing import cpu_count
from typing import Set, Tuple, List, Any, Dict

from colorama import Fore, init
from tabulate import tabulate
from tqdm import tqdm
from tqdm.contrib.concurrent import process_map
from yak_parser import Statechart
from yak_parser.StatechartParser import StatechartParser

from nyc import preprocessor
from nyc.compare_pair import compare_pair


class Main:
    def __init__(self):
        parser = argparse.ArgumentParser(
            description='Detects plagiarism in statecharts',
            usage='''
            main.py <command> [<args>]

            Commands:
               compare     Compare statecharts
               list        List found cases of plagiarism
               matches     Show matches
            '''
        )
        parser.add_argument('command', help='Subcommand to run', choices=['compare', 'list', 'matches'])
        args = parser.parse_args(sys.argv[1:2])
        if not hasattr(self, args.command):
            print('Unrecognized command')
            parser.print_help()
            exit(1)
        init(autoreset=True)
        getattr(self, args.command)()

    @staticmethod
    def compare():
        parser = argparse.ArgumentParser(description='Compare statecharts')
        parser.add_argument('directory', nargs='?', default=os.getcwd(),
                            help='The directory containing the statecharts')
        named_statecharts = Main.load_statecharts(parser.parse_args(sys.argv[2:]).directory)

        unprocessed_statechart_and_preprocessing_result_pairs = {}
        for path, statechart in tqdm(named_statecharts, desc='Preprocessing', unit='statecharts'):
            unprocessed_statechart_and_preprocessing_result_pairs[path] = \
                (copy.deepcopy(statechart), preprocessor.process(statechart))

        pairs = list(itertools.combinations(named_statecharts, 2))
        comparison_result = process_map(compare_pair, pairs, desc='Processing', unit='pairs',
                                        max_workers=cpu_count() - 1)
        comparison_result.sort(
            key=lambda result: result[2].similarity * result[2].max_similarity * result[2].state_similarity,
            reverse=True)
        Main.save_comparison_result((unprocessed_statechart_and_preprocessing_result_pairs, comparison_result))

    @staticmethod
    def list():
        parser = argparse.ArgumentParser(description='List found cases of plagiarism')
        parser.add_argument('result_file', help='Path of the comparison result file')
        parser.add_argument('-threshold', type=float, default=0.8, help='Threshold for average similarity')
        parser.add_argument('-max-threshold', type=float, default=0.8, help='Threshold for maximum similarity')
        parser.add_argument('-state-threshold', type=float, default=0.9, help='Threshold for state similarity')
        arguments = parser.parse_args(sys.argv[2:])
        _, comparison_result = Main.load_comparison_result(arguments.result_file)
        table = [
            [
                (Fore.GREEN + str(i) + Fore.RESET),
                os.path.basename(path1),
                os.path.basename(path2),
                f'{result.similarity:.2%}{"*" if result.is_greedy else ""}',
                f'{result.max_similarity:.2%}{"*" if result.is_greedy else ""}',
                f'{result.state_similarity:.2%}{"*" if result.is_greedy else ""}'
            ]
            for i, (path1, path2, result) in enumerate(comparison_result, start=1)
            if result.similarity >= arguments.threshold or result.max_similarity >= arguments.max_threshold or result.state_similarity >= arguments.state_threshold
        ]
        print(
            tabulate(table, headers=[
                'ID',
                'File 1',
                'File 2',
                f'Similarity (>={"{:.2%}".format(arguments.threshold)})',
                f'Maximum single similarity (>={"{:.2%}".format(arguments.max_threshold)})',
                f'State similarity (>={"{:.2%}".format(arguments.state_threshold)})'
            ])
        )
        print('*: Greedy algorithm used')

    @staticmethod
    def matches():
        parser = argparse.ArgumentParser(description='Show matches')
        parser.add_argument('result_file', help='Path of the comparison result file')
        parser.add_argument('id', type=int, help='ID')
        arguments = parser.parse_args(sys.argv[2:])
        unprocessed_statechart_and_preprocessing_result_pairs, comparison_result = \
            Main.load_comparison_result(arguments.result_file)
        path1, path2, comparison_result_ = comparison_result[arguments.id - 1]
        print((Fore.GREEN + f'#{arguments.id}'))
        print(f'Statechart 1: {os.path.basename(path1)}')
        print(f'Statechart 2: {os.path.basename(path2)}')
        print(f'Average similarity: {"{:.2%}".format(comparison_result_.similarity)}')
        print(f'Maximum similarity: {"{:.2%}".format(comparison_result_.max_similarity)}')
        print()

        print(('\033[1m' + 'Preprocessing:'))
        Main.print_preprocessing_results(path1, unprocessed_statechart_and_preprocessing_result_pairs[path1])
        Main.print_preprocessing_results(path2, unprocessed_statechart_and_preprocessing_result_pairs[path2])

        statechart1: Statechart = unprocessed_statechart_and_preprocessing_result_pairs[path1][0]
        statechart2: Statechart = unprocessed_statechart_and_preprocessing_result_pairs[path2][0]
        print(('\033[1m' + 'Matches:'))
        grouped_matches = Main.group(comparison_result_.diff.matches.items())
        print('\033[3m' + 'States')
        for (id1, id2), labels in grouped_matches['state']:
            print(f'{statechart1.get_name(id1)} = {statechart2.get_name(id2)}: {labels}')
        print()
        print('\033[3m' + 'Transitions')
        for (id1, id2), labels in grouped_matches['transition']:
            transitions1 = [y for x in statechart1.transitions.values() for y in x if y.transition_id == id1][0]
            named_transitions1 = \
                f'{statechart1.get_name(transitions1.source_id)} -> {statechart1.get_name(transitions1.source_id)}'
            transitions2 = [y for x in statechart2.transitions.values() for y in x if y.transition_id == id2][0]
            named_transitions2 = \
                f'{statechart2.get_name(transitions2.source_id)} -> {statechart2.get_name(transitions2.source_id)}'
            print(f'{named_transitions1} = {named_transitions2}: {labels}')
        print()
        print('\033[3m' + 'Hierarchy')
        for (id1, id2), labels in grouped_matches['hierarchy']:
            named_edge1 = \
                f'{statechart1.get_name(id1[:len(id1) // 2])} -> {statechart1.get_name(id1[len(id1) // 2:])}'
            named_edge2 = \
                f'{statechart2.get_name(id2[:len(id2) // 2])} -> {statechart2.get_name(id2[len(id2) // 2:])}'
            print(f'{named_edge1} = {named_edge2}: {labels}')
        print()

        print(('\033[1m' + 'Deletions:'))
        Main.method_name(comparison_result_.diff.deletions.items(), statechart1)
        print()

        print(('\033[1m' + 'Additions:'))
        Main.method_name(comparison_result_.diff.additions.items(), statechart2)
        print()

    @staticmethod
    def group(matches: List[Tuple[Any, Set[str]]]) -> Dict[str, List[Tuple[Any, Set[str]]]]:
        dictionary = defaultdict(list)
        for x, labels in matches:
            dictionary[Main.get_match_type(labels)].append((x, labels))
        return dictionary

    @staticmethod
    def get_match_type(labels):
        if labels == {'hierarchy'}:
            return 'hierarchy'
        elif Main.is_transition(labels):
            return 'transition'
        else:
            return 'state'

    @staticmethod
    def method_name(something, statechart):
        grouped_something = Main.group(something)
        print('\033[3m' + 'States')
        for id_, labels in grouped_something['state']:
            print(f'{statechart.get_name(id_)}: {labels}')
        print()
        print('\033[3m' + 'Transitions')
        for id_, labels in grouped_something['transition']:
            transitions = [y for x in statechart.transitions.values() for y in x if y.transition_id == id_][0]
            named_transitions = \
                f'{statechart.get_name(transitions.source_id)} -> {statechart.get_name(transitions.target_id)}'
            print(f'{named_transitions}: {labels}')
        print()
        print('\033[3m' + 'Hierarchy')
        for id_, labels in grouped_something['hierarchy']:
            named_edge = \
                f'{statechart.get_name(id_[:len(id_) // 2])} -> {statechart.get_name(id_[len(id_) // 2:])}'
            print(f'{named_edge}: {labels}')

    @staticmethod
    def is_transition(labels):
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

    @staticmethod
    def load_statecharts(directory):
        statechart_paths = set()
        for root, _, files in os.walk(directory):
            [statechart_paths.add(os.path.join(root, file)) for file in files if
             os.path.splitext(file)[1] in ['.ysc', '.sct']]
        statecharts_with_path = []
        for statechart_path in statechart_paths:
            try:
                statecharts_with_path.append((statechart_path, StatechartParser().parse(path=statechart_path)))
            except ValueError as err:
                print(f'Skipped {statechart_path}: {err}')
        return statecharts_with_path

    @staticmethod
    def save_comparison_result(comparison_result):
        result_filename = 'comparison.result'
        result_file = open(result_filename, 'wb')
        pickle.dump(comparison_result, result_file)
        result_file.close()
        print(f'Result saved as {result_filename}')

    @staticmethod
    def load_comparison_result(path):
        result_file = open(path, 'rb')
        comparison_result = pickle.load(result_file)
        result_file.close()
        return comparison_result

    @staticmethod
    def print_preprocessing_results(path, unprocessed_statechart_and_processing_result):
        processing_result = unprocessed_statechart_and_processing_result[1]
        unreachable_states = processing_result.unreachable_states
        removed_nesting_states = processing_result.removed_nesting_states
        removed_duplicate_transitions = processing_result.removed_duplicate_transitions
        if len(unreachable_states) + len(removed_nesting_states) + len(removed_duplicate_transitions) != 0:
            print('\033[3m' + f'{os.path.basename(path)}:')

            statechart: Statechart = unprocessed_statechart_and_processing_result[0]
            if len(unreachable_states) != 0:
                print('Removed unreachable states')
                print([statechart.get_name(state) for state in unreachable_states])

            if len(removed_nesting_states) != 0:
                print('Removed unnecessary nesting states')
                print([statechart.get_name(state) for state in removed_nesting_states])

            if len(removed_duplicate_transitions) != 0:
                print('Removed unnecessary nesting states')
                for transition in removed_duplicate_transitions:
                    print(
                        f'{transition.transition_id}: {statechart.get_name(transition.source_id)} -> '
                        f'{statechart.get_name(transition.target_id)} : {transition.specification}'
                    )

            print()


if __name__ == '__main__':
    Main()
