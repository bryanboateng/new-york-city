import os

import bryan
from yak_parser.StatechartParser import StatechartParser


path = '02_light_switch.ysc'
name_base = os.path.splitext(path)[0]
statechart = StatechartParser().parse(path=path)

statechart.save_hierarchy_image(name_base + '.svg')
statechart.print_transitions()


bryan.process(statechart)


statechart.save_hierarchy_image(name_base + '_processed.svg')
statechart.print_transitions()
