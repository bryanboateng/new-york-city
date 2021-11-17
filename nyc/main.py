import argparse
import copy
import itertools
import os
import pickle
import sys

from colorama import Fore, init
from progress.bar import IncrementalBar
from tabulate import tabulate
from yak_parser.StatechartParser import StatechartParser

import comparator
import preprocessor


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
        parser = argparse.ArgumentParser(description='Record changes to the repository')
        parser.add_argument('directory', nargs='?', default=os.getcwd(),
                            help='The directory containing the statecharts')
        named_statecharts = Main.load_statecharts(parser.parse_args(sys.argv[2:]).directory)

        preprocessing_progress_bar = IncrementalBar(
            'Preprocessing',
            max=len(named_statecharts),
            check_tty=False,
            hide_cursor=False,
            suffix='%(percent).1f%% - %(index)d / %(max)d'
        )
        unprocessed_statechart_and_preprocessing_result_pairs = {}
        for path, statechart in named_statecharts:
            unprocessed_statechart_and_preprocessing_result_pairs[path] = \
                (copy.deepcopy(statechart), preprocessor.process(statechart))
            preprocessing_progress_bar.next()
        preprocessing_progress_bar.finish()

        pairs = list(itertools.combinations(named_statecharts, 2))
        print(f'{len(named_statecharts)} statecharts')
        print(f'{len(pairs)} combinations')
        processing_progress_bar = IncrementalBar(
            'Processing',
            max=len(pairs),
            check_tty=False,
            hide_cursor=False,
            suffix='%(percent).1f%% - %(index)d / %(max)d'
        )
        comparison_result = []
        for named_statechart1, named_statechart2 in pairs:
            comparison_result.append((named_statechart1[0], named_statechart2[0],
                                      comparator.compare(named_statechart1[1], named_statechart2[1])))
            processing_progress_bar.next()
        processing_progress_bar.finish()
        Main.save_comparison_result((unprocessed_statechart_and_preprocessing_result_pairs, comparison_result))

    @staticmethod
    def list():
        parser = argparse.ArgumentParser(description='List found cases of plagiarism')
        parser.add_argument('result_file', help='Path of the comparison result file')
        parser.add_argument('-threshold', type=float, default=0.8, help='Threshold for average similarity')
        parser.add_argument('-max-threshold', type=float, default=0.8, help='Threshold for maximum similarity')
        arguments = parser.parse_args(sys.argv[2:])
        _, comparison_result = Main.load_comparison_result(arguments.result_file)
        table = [
            [
                (Fore.GREEN + f'#{i}' + Fore.RESET),
                os.path.basename(path1),
                os.path.basename(path2),
                '{:.2%}'.format(result.similarity),
                '{:.2%}'.format(result.max_similarity)
            ]
            for i, (path1, path2, result) in enumerate(comparison_result, start=1)
            if result.similarity >= arguments.threshold or result.max_similarity >= arguments.max_threshold
        ]
        print(
            tabulate(table, headers=[
                'ID',
                'File 1',
                'File 2',
                f'Average similarity (>={"{:.2%}".format(arguments.threshold)})',
                f'Maximum similarity (>={"{:.2%}".format(arguments.max_threshold)})'
            ])
        )

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
        print(f'Average similarity: {"{:.2%}".format(comparison_result_.similarity)}')
        print(f'Maximum similarity: {"{:.2%}".format(comparison_result_.max_similarity)}')
        print()

        print(('\033[1m' + 'Preprocessing:'))
        Main.print_preprocessing_results(path1, unprocessed_statechart_and_preprocessing_result_pairs[path1])
        Main.print_preprocessing_results(path2, unprocessed_statechart_and_preprocessing_result_pairs[path2])

        print(('\033[1m' + 'Matches:'))
        for (id1, id2), labels in comparison_result_.diff.matches.items():
            print(f'{id1} - {id2}: {labels}')

    @staticmethod
    def load_statecharts(directory):
        statechart_paths = set()
        for root, _, files in os.walk(directory):
            [statechart_paths.add(os.path.join(root, file)) for file in files if
             os.path.splitext(file)[1] in ['.ysc', '.sct']]
        return [(statechart_path, StatechartParser().parse(path=statechart_path))
                for statechart_path in statechart_paths]

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

            statechart = unprocessed_statechart_and_processing_result[0]
            if len(unreachable_states) != 0:
                print('Removed unreachable states')
                print([statechart.get_state_name(state) for state in unreachable_states])

            if len(removed_nesting_states) != 0:
                print('Removed unnecessary nesting states')
                print([statechart.get_state_name(state) for state in removed_nesting_states])

            if len(removed_duplicate_transitions) != 0:
                print('Removed unnecessary nesting states')
                for transition in removed_duplicate_transitions:
                    print(
                        f'{transition.transition_id}: {statechart.get_state_name(transition.source_id)} -> '
                        f'{statechart.get_state_name(transition.target_id)} : {transition.specification}'
                    )

            print()


if __name__ == '__main__':
    Main()
