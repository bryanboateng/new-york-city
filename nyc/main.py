import argparse
import itertools
import os
import pickle
import sys

from colorama import Fore, Style
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
            '''
        )
        parser.add_argument('command', help='Subcommand to run', choices=['compare', 'list'])
        args = parser.parse_args(sys.argv[1:2])
        if not hasattr(self, args.command):
            print('Unrecognized command')
            parser.print_help()
            exit(1)
        getattr(self, args.command)()

    @staticmethod
    def compare():
        parser = argparse.ArgumentParser(description='Record changes to the repository')
        parser.add_argument('directory', nargs='?', default=os.getcwd(),
                            help="The directory containing the statecharts")
        named_statecharts = Main.load_statecharts(parser.parse_args(sys.argv[2:]).directory)
        for _, statechart in named_statecharts:
            preprocessor.process(statechart)
        pairs = list(itertools.combinations(named_statecharts, 2))
        progress_bar = IncrementalBar('Processing', max=len(pairs), check_tty=False, hide_cursor=False,
                                      suffix='%(percent).1f%% - %(index)d / %(max)d')
        comparison_result = []
        for named_statechart1, named_statechart2 in pairs:
            comparison_result.append((named_statechart1[0], named_statechart2[0],
                                      comparator.compare(named_statechart1[1], named_statechart2[1])))
            progress_bar.next()
        progress_bar.finish()
        Main.save_comparison_result(comparison_result)

    @staticmethod
    def list():
        parser = argparse.ArgumentParser(description='List found cases of plagiarism')
        parser.add_argument('result_file', help="Path of the comparison result file")
        result_file = open(parser.parse_args(sys.argv[2:]).result_file, 'rb')
        new_dict = pickle.load(result_file)
        result_file.close()
        table = [
            [
                (Fore.GREEN + f"#{i}"),
                (Style.RESET_ALL + os.path.basename(path1)),
                os.path.basename(path2),
                "{:.2%}".format(result.similarity),
                "{:.2%}".format(result.max_similarity)
            ]
            for i, (path1, path2, result) in enumerate(new_dict, start=1)
            if result.similarity > 0.8 or result.max_similarity > 0.8
        ]
        print(tabulate(table, headers=['ID', 'File 1', 'File 2', 'Average similarity', 'Maximum similarity']))

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
        print(f"Result saved as {result_filename}")


if __name__ == '__main__':
    Main()
