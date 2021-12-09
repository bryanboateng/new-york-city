"""
Module containing the compare_pair function.
The function previously was inside of the comparator.py module
but has been relocated into its one module for the multiprocessing code to work.
"""

from nyc.comparator import Comparator


def compare_pair(named_statechart_pair):
    comparator = Comparator(named_statechart_pair[0][1], named_statechart_pair[1][1])
    return named_statechart_pair[0][0], named_statechart_pair[1][0], comparator.compare()
