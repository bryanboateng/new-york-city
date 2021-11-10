import argparse
import itertools
import os
import pickle
from typing import Set

from yak_parser.StatechartParser import StatechartParser

import comparator
import preprocessor


def get_statechart_filenames() -> Set[str]:
    parser = argparse.ArgumentParser()
    parser.add_argument("w", choices=['inspect'], help="increase output verbosity")
    parser.add_argument('dir', nargs='?', default=os.getcwd(), help="The directory containing the statecharts")
    files = set()
    for root, _, files_ in os.walk(parser.parse_args().dir):
        [files.add(os.path.join(root, file_)) for file_ in files_ if os.path.splitext(file_)[1] in ['.ysc', '.sct']]
    return files


filenames = get_statechart_filenames()
named_statecharts = [(filename, StatechartParser().parse(path=filename)) for filename in filenames]
for _, statechart in named_statecharts:
    preprocessor.process(statechart)
comparison_result = [comparator.compare(x[1], y[1]) for x, y in itertools.combinations(named_statecharts, 2)]
outfile = open('comparison.result', 'wb')
pickle.dump(comparison_result, outfile)
outfile.close()
