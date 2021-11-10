import argparse
import itertools
import os
import pickle
from typing import Set

from progress.bar import IncrementalBar
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
pairs = list(itertools.combinations(named_statecharts, 2))
bar = IncrementalBar('Processing', max=len(pairs), check_tty=False, hide_cursor=False,
                     suffix='%(percent).1f%% - %(index)d / %(max)d')
comparison_result = []
for named_statechart1, named_statechart2 in pairs:
    comparison_result.append(comparator.compare(named_statechart1[1], named_statechart2[1]))
    bar.next()
bar.finish()

outfile = open('comparison.result', 'wb')
pickle.dump(comparison_result, outfile)
outfile.close()
